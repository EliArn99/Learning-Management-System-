import logging
import random

from django.db import transaction
from django.utils import timezone

from .models import Answer, Question, StudentAnswer, StudentQuizAttempt, Submission
from .selectors import selected_questions_with_answers

logger = logging.getLogger(__name__)


def get_or_reset_attempt(quiz, student_user):
    attempt, _ = StudentQuizAttempt.objects.get_or_create(
        quiz=quiz,
        student=student_user,
        defaults={
            "start_time": timezone.now(),
            "is_complete": False,
            "selected_question_ids": [],
        },
    )

    if attempt.is_complete:
        attempt.is_complete = False
        attempt.start_time = timezone.now()
        attempt.selected_question_ids = []
        attempt.save(
            update_fields=[
                "is_complete",
                "start_time",
                "selected_question_ids",
            ]
        )

    return attempt


def select_questions_for_attempt(quiz, attempt):
    if attempt.selected_question_ids:
        return selected_questions_with_answers(quiz, attempt.selected_question_ids)

    all_question_ids = list(
        quiz.questions.values_list("id", flat=True).order_by("id")
    )

    number_to_select = quiz.num_questions_to_select or 0

    if number_to_select > 0 and number_to_select < len(all_question_ids):
        selected_ids = random.sample(all_question_ids, number_to_select)
    else:
        selected_ids = all_question_ids

    attempt.selected_question_ids = selected_ids
    attempt.save(update_fields=["selected_question_ids"])

    return selected_questions_with_answers(quiz, selected_ids)


def quiz_time_expired(quiz, attempt) -> bool:
    if not quiz.time_limit:
        return False

    elapsed = timezone.now() - attempt.start_time
    return elapsed.total_seconds() > quiz.time_limit * 60


def complete_attempt(attempt):
    attempt.is_complete = True
    attempt.save(update_fields=["is_complete"])
    return attempt


def evaluate_closed_question(question, selected_answer_ids):
    correct_answer_ids = {
        answer.id
        for answer in question.all_answers
        if answer.is_correct
    }

    selected_ids = {
        answer_id
        for answer_id in selected_answer_ids
        if answer_id is not None
    }

    if selected_ids == correct_answer_ids and correct_answer_ids:
        return question.points

    return 0


@transaction.atomic
def process_quiz_submission(quiz, student_user, attempt, user_answers_raw):
    allowed_question_ids = set(attempt.selected_question_ids or [])

    questions = selected_questions_with_answers(
        quiz,
        attempt.selected_question_ids or [],
    )

    question_map = {
        question.id: question
        for question in questions
    }

    submission = Submission.objects.create(
        quiz=quiz,
        student=student_user,
    )

    total_points_earned = 0
    total_possible_points = sum(question.points for question in questions)

    for answer_data in user_answers_raw:
        question_id = answer_data.get("questionId")

        if question_id not in allowed_question_ids:
            logger.warning(
                "User attempted to submit answer for unseen question. user_id=%s quiz_id=%s question_id=%s",
                student_user.id,
                quiz.id,
                question_id,
            )
            continue

        question = question_map.get(question_id)

        if not question:
            continue

        selected_answer_ids = answer_data.get("selectedAnswerIds", [])
        text_answer = answer_data.get("textAnswer", "")

        if question.type in ["MC", "MM", "TF"]:
            points_awarded = evaluate_closed_question(
                question,
                selected_answer_ids,
            )

            selected_ids = {
                answer_id
                for answer_id in selected_answer_ids
                if answer_id is not None
            }

            if selected_ids:
                is_first_answer = True

                for selected_id in selected_ids:
                    selected_answer = next(
                        (
                            answer
                            for answer in question.all_answers
                            if answer.id == selected_id
                        ),
                        None,
                    )

                    if selected_answer:
                        StudentAnswer.objects.create(
                            submission=submission,
                            question=question,
                            selected_answer=selected_answer,
                            points_awarded=points_awarded if is_first_answer else 0,
                        )
                        is_first_answer = False
            else:
                StudentAnswer.objects.create(
                    submission=submission,
                    question=question,
                    selected_answer=None,
                    points_awarded=0,
                )

            total_points_earned += points_awarded

        elif question.type == "OT":
            StudentAnswer.objects.create(
                submission=submission,
                question=question,
                text_response=text_answer,
                selected_answer=None,
                points_awarded=0,
            )

    submission.score = (
        round((total_points_earned / total_possible_points) * 100, 2)
        if total_possible_points
        else 0
    )
    submission.save(update_fields=["score"])

    complete_attempt(attempt)

    return submission