import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses.models import Course, Enrollment
from users.models import StudentProfile, TeacherProfile

from .models import (
    Answer,
    Question,
    Quiz,
    StudentQuizAttempt,
    Submission,
)
from .services import (
    get_or_reset_attempt,
    process_quiz_submission,
    select_questions_for_attempt,
)


User = get_user_model()


class QuizTestMixin:
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username="teacher",
            email="teacher@example.com",
            password="testpass123",
            is_teacher=True,
        )

        # SIGNAL CREATED PROFILE
        self.teacher_profile = self.teacher_user.teacherprofile
        self.teacher_profile.age = 30
        self.teacher_profile.education = "Computer Science"
        self.teacher_profile.experience_years = 5
        self.teacher_profile.is_approved = True
        self.teacher_profile.save()

        self.student_user = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="testpass123",
            is_student=True,
        )

        # SIGNAL CREATED PROFILE
        self.student_profile = self.student_user.studentprofile
        self.student_profile.age = 20
        self.student_profile.is_approved = True
        self.student_profile.save()

        self.course = Course.objects.create(
            name="Django Course",
            description="Test course",
            teacher=self.teacher_profile,
            price=Decimal("10.00"),
        )

        self.quiz = Quiz.objects.create(
            title="Django Quiz",
            description="Test quiz",
            course=self.course,
            created_by=self.teacher_profile,
            available_from=timezone.now() - timedelta(days=1),
            available_until=timezone.now() + timedelta(days=1),
            time_limit=30,
            num_questions_to_select=0,
        )

        self.question = Question.objects.create(
            quiz=self.quiz,
            text="What is Django?",
            points=2,
            type="MC",
        )

        self.correct_answer = Answer.objects.create(
            question=self.question,
            text="Web framework",
            is_correct=True,
        )

        self.wrong_answer = Answer.objects.create(
            question=self.question,
            text="Operating system",
            is_correct=False,
        )


class QuizModelTests(QuizTestMixin, TestCase):

    def test_quiz_is_active(self):
        self.assertTrue(self.quiz.is_active())

    def test_quiz_invalid_time_limit(self):
        quiz = Quiz(
            title="Invalid Quiz",
            course=self.course,
            created_by=self.teacher_profile,
            time_limit=0,
        )

        with self.assertRaises(ValidationError):
            quiz.full_clean()

    def test_question_points_must_be_positive(self):
        question = Question(
            quiz=self.quiz,
            text="Invalid question",
            points=0,
            type="MC",
        )

        with self.assertRaises(ValidationError):
            question.full_clean()


class QuizServiceTests(QuizTestMixin, TestCase):

    def test_get_or_reset_attempt_creates_attempt(self):
        attempt = get_or_reset_attempt(
            quiz=self.quiz,
            student_user=self.student_user,
        )

        self.assertEqual(attempt.quiz, self.quiz)
        self.assertEqual(attempt.student, self.student_user)
        self.assertFalse(attempt.is_complete)

    def test_completed_attempt_is_reset(self):
        attempt = StudentQuizAttempt.objects.create(
            quiz=self.quiz,
            student=self.student_user,
            is_complete=True,
            selected_question_ids=[self.question.id],
        )

        reset_attempt = get_or_reset_attempt(
            quiz=self.quiz,
            student_user=self.student_user,
        )

        self.assertFalse(reset_attempt.is_complete)
        self.assertEqual(reset_attempt.selected_question_ids, [])

    def test_select_questions_for_attempt_stores_question_ids(self):
        attempt = get_or_reset_attempt(
            quiz=self.quiz,
            student_user=self.student_user,
        )

        questions = select_questions_for_attempt(
            self.quiz,
            attempt,
        )

        attempt.refresh_from_db()

        self.assertEqual(len(questions), 1)
        self.assertEqual(
            attempt.selected_question_ids,
            [self.question.id],
        )

    def test_process_quiz_submission_scores_correct_answer(self):
        attempt = get_or_reset_attempt(
            self.quiz,
            self.student_user,
        )

        attempt.selected_question_ids = [self.question.id]
        attempt.save(update_fields=["selected_question_ids"])

        submission = process_quiz_submission(
            quiz=self.quiz,
            student_user=self.student_user,
            attempt=attempt,
            user_answers_raw=[
                {
                    "questionId": self.question.id,
                    "selectedAnswerIds": [self.correct_answer.id],
                }
            ],
        )

        self.assertEqual(submission.score, 100)
        self.assertEqual(
            submission.student_answers.count(),
            1,
        )

    def test_process_quiz_submission_scores_wrong_answer(self):
        attempt = get_or_reset_attempt(
            self.quiz,
            self.student_user,
        )

        attempt.selected_question_ids = [self.question.id]
        attempt.save(update_fields=["selected_question_ids"])

        submission = process_quiz_submission(
            quiz=self.quiz,
            student_user=self.student_user,
            attempt=attempt,
            user_answers_raw=[
                {
                    "questionId": self.question.id,
                    "selectedAnswerIds": [self.wrong_answer.id],
                }
            ],
        )

        self.assertEqual(submission.score, 0)


class QuizViewTests(QuizTestMixin, TestCase):

    def test_quiz_list_returns_200(self):
        response = self.client.get(
            reverse("quizz:quiz_list")
        )

        self.assertEqual(response.status_code, 200)

    def test_teacher_can_access_manage_list(self):
        self.client.login(
            username="teacher",
            password="testpass123",
        )

        response = self.client.get(
            reverse("quizz:quiz_manage_list")
        )

        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_manage_list(self):
        self.client.login(
            username="student",
            password="testpass123",
        )

        response = self.client.get(
            reverse("quizz:quiz_manage_list")
        )

        self.assertEqual(response.status_code, 403)

    def test_student_without_paid_enrollment_cannot_take_quiz(self):
        self.client.login(
            username="student",
            password="testpass123",
        )

        response = self.client.get(
            reverse(
                "quizz:quiz_take",
                kwargs={"pk": self.quiz.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_student_with_paid_enrollment_can_take_quiz(self):
        Enrollment.objects.create(
            student=self.student_profile,
            course=self.course,
            is_paid=True,
        )

        self.client.login(
            username="student",
            password="testpass123",
        )

        response = self.client.get(
            reverse(
                "quizz:quiz_take",
                kwargs={"pk": self.quiz.pk},
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_student_can_submit_quiz(self):
        Enrollment.objects.create(
            student=self.student_profile,
            course=self.course,
            is_paid=True,
        )

        attempt = get_or_reset_attempt(
            self.quiz,
            self.student_user,
        )

        attempt.selected_question_ids = [self.question.id]
        attempt.save(update_fields=["selected_question_ids"])

        self.client.login(
            username="student",
            password="testpass123",
        )

        response = self.client.post(
            reverse(
                "quizz:quiz_take",
                kwargs={"pk": self.quiz.pk},
            ),
            data=json.dumps(
                {
                    "userAnswers": [
                        {
                            "questionId": self.question.id,
                            "selectedAnswerIds": [self.correct_answer.id],
                        }
                    ]
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            Submission.objects.filter(
                quiz=self.quiz,
                student=self.student_user,
                score=100,
            ).exists()
        )

    def test_quiz_results_requires_submission(self):
        Enrollment.objects.create(
            student=self.student_profile,
            course=self.course,
            is_paid=True,
        )

        self.client.login(
            username="student",
            password="testpass123",
        )

        response = self.client.get(
            reverse(
                "quizz:quiz_results",
                kwargs={"pk": self.quiz.pk},
            )
        )

        self.assertEqual(response.status_code, 403)
