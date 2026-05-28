from django.db.models import Prefetch

from courses.models import Enrollment

from .models import Answer, Question, Quiz, StudentQuizAttempt, Submission


def quizzes_for_teacher(teacher_profile):
    return Quiz.objects.filter(
        created_by=teacher_profile,
    ).select_related("course", "created_by__user").order_by("-id")


def get_quiz_for_teacher_or_404_queryset(teacher_profile):
    return Quiz.objects.filter(
        created_by=teacher_profile,
    ).select_related("course", "created_by__user")


def all_quizzes():
    return Quiz.objects.select_related("course", "created_by__user").order_by("-id")


def quiz_with_questions_and_answers():
    return Quiz.objects.prefetch_related(
        Prefetch(
            "questions",
            queryset=Question.objects.prefetch_related("answers").order_by("id"),
        )
    ).select_related("course", "created_by__user")


def student_has_paid_enrollment(student_profile, course) -> bool:
    return Enrollment.objects.filter(
        student=student_profile,
        course=course,
        is_paid=True,
    ).exists()


def latest_submission_for_student(quiz, student_user):
    return Submission.objects.filter(
        quiz=quiz,
        student=student_user,
    ).order_by("-submitted_at").first()


def selected_questions_with_answers(quiz, selected_question_ids):
    questions = Question.objects.filter(
        quiz=quiz,
        id__in=selected_question_ids,
    ).prefetch_related(
        Prefetch(
            "answers",
            queryset=Answer.objects.all(),
            to_attr="all_answers",
        )
    )

    question_by_id = {question.id: question for question in questions}

    return [
        question_by_id[question_id]
        for question_id in selected_question_ids
        if question_id in question_by_id
    ]


def attempt_for_student(quiz, student_user):
    return StudentQuizAttempt.objects.filter(
        quiz=quiz,
        student=student_user,
    ).first()
