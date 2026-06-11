from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from assignments.models import Assignment, Submission as AssignmentSubmission
from courses.models import Course, Enrollment
from messaging.models import Message
from quizz.models import Quiz, Submission as QuizSubmission

from .models import DashboardNotification


User = get_user_model()


class DashboardTestMixin:
    def setUp(self):
        self.student_user = User.objects.create_user(
            username="dashboard_student",
            email="dashboard_student@example.com",
            password="testpass123",
            is_student=True,
        )
        self.student_profile = self.student_user.studentprofile
        self.student_profile.age = 20
        self.student_profile.is_approved = True
        self.student_profile.save()

        self.teacher_user = User.objects.create_user(
            username="dashboard_teacher",
            email="dashboard_teacher@example.com",
            password="testpass123",
            is_teacher=True,
        )
        self.teacher_profile = self.teacher_user.teacherprofile
        self.teacher_profile.age = 30
        self.teacher_profile.education = "Computer Science"
        self.teacher_profile.experience_years = 5
        self.teacher_profile.is_approved = True
        self.teacher_profile.save()

        self.other_user = User.objects.create_user(
            username="other_user",
            email="other@example.com",
            password="testpass123",
        )

        self.course = Course.objects.create(
            name="Dashboard Course",
            description="Test course",
            teacher=self.teacher_profile,
            price=Decimal("10.00"),
        )

        self.enrollment = Enrollment.objects.create(
            student=self.student_profile,
            course=self.course,
            is_paid=True,
        )

        self.assignment = Assignment.objects.create(
            course=self.course,
            title="Dashboard Assignment",
            description="Test assignment",
            topic="Django",
            due_date=timezone.now() + timedelta(days=3),
        )

        self.quiz = Quiz.objects.create(
            title="Dashboard Quiz",
            description="Test quiz",
            course=self.course,
            created_by=self.teacher_profile,
            available_from=timezone.now() - timedelta(days=1),
            available_until=timezone.now() + timedelta(days=2),
            time_limit=30,
            num_questions_to_select=0,
        )


class DashboardPublicViewTests(TestCase):
    def test_home_returns_200(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)

    def test_about_returns_200(self):
        response = self.client.get(reverse("dashboards:about"))

        self.assertEqual(response.status_code, 200)

    def test_contacts_returns_200(self):
        response = self.client.get(reverse("dashboards:contacts"))

        self.assertEqual(response.status_code, 200)


class TeacherDashboardTests(DashboardTestMixin, TestCase):
    def test_teacher_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboards:teacher_dashboard"))

        self.assertEqual(response.status_code, 302)

    def test_teacher_can_access_teacher_dashboard(self):
        self.client.login(
            username="dashboard_teacher",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboards:teacher_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard Course")

    def test_student_cannot_access_teacher_dashboard(self):
        self.client.login(
            username="dashboard_student",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboards:teacher_dashboard"))

        self.assertEqual(response.status_code, 403)

    def test_teacher_dashboard_context_counts_submissions(self):
        AssignmentSubmission.objects.create(
            assignment=self.assignment,
            student=self.student_profile,
            grade=5.5,
        )

        self.client.login(
            username="dashboard_teacher",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboards:teacher_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_submissions"], 1)
        self.assertEqual(response.context["graded_submissions"], 1)
        self.assertEqual(response.context["pending_submissions"], 0)

    def test_teacher_dashboard_shows_unread_messages(self):
        Message.objects.create(
            sender=self.student_user,
            receiver=self.teacher_user,
            subject="Question",
            content="Hello teacher",
            is_read=False,
        )

        self.client.login(
            username="dashboard_teacher",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboards:teacher_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["unread_messages"]), 1)


class StudentDashboardTests(DashboardTestMixin, TestCase):
    def test_student_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboards:student_dashboard"))

        self.assertEqual(response.status_code, 302)

    def test_student_can_access_student_dashboard(self):
        self.client.login(
            username="dashboard_student",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboards:student_dashboard"))

        self.assertEqual(response.status_code, 200)

    def test_teacher_cannot_access_student_dashboard(self):
        self.client.login(
            username="dashboard_teacher",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboards:student_dashboard"))

        self.assertEqual(response.status_code, 403)

    def test_student_dashboard_progress_is_zero_without_submissions(self):
        self.client.login(
            username="dashboard_student",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboards:student_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["progress"], 0)

    def test_student_dashboard_progress_after_quiz_submission(self):
        QuizSubmission.objects.create(
            quiz=self.quiz,
            student=self.student_user,
            score=100,
        )

        self.client.login(
            username="dashboard_student",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboards:student_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["progress"], 100)


class DashboardNotificationTests(DashboardTestMixin, TestCase):
    def test_notifications_require_login(self):
        response = self.client.get(reverse("dashboards:notifications"))

        self.assertEqual(response.status_code, 302)

    def test_user_can_view_own_notifications(self):
        DashboardNotification.objects.create(
            user=self.student_user,
            title="Test Notification",
            message="Hello student",
        )

        self.client.login(
            username="dashboard_student",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboards:notifications"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Notification")
        self.assertEqual(response.context["unread_count"], 1)

    def test_user_can_mark_own_notification_as_read(self):
        notification = DashboardNotification.objects.create(
            user=self.student_user,
            title="Read me",
            message="Mark this as read",
            url="dashboards:notifications",
        )

        self.client.login(
            username="dashboard_student",
            password="testpass123",
        )

        response = self.client.get(
            reverse(
                "dashboards:mark_notification_read",
                kwargs={"pk": notification.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_user_can_view_own_notifications(self):
        notification = DashboardNotification.objects.create(
            user=self.student_user,
            title="Test Notification",
            message="Hello student",
        )

        self.client.login(
            username="dashboard_student",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboards:notifications"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["unread_count"], 1)
        self.assertIn(notification, response.context["notifications"])
