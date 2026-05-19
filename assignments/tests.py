from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses.models import Course, Enrollment
from users.models import StudentProfile, TeacherProfile

from .models import Assignment, Submission


User = get_user_model()


class AssignmentModelTests(TestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username="teacher",
            email="teacher@example.com",
            password="testpass123",
            is_teacher=True,
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            age=30,
            education="Computer Science",
            experience_years=5,
            is_approved=True,
        )
        self.course = Course.objects.create(
            name="Django Course",
            description="Test course",
            teacher=self.teacher_profile,
            price=Decimal("10.00"),
        )

    def test_assignment_status_open(self):
        assignment = Assignment.objects.create(
            course=self.course,
            title="Homework 1",
            description="Test",
            topic="Django",
            due_date=timezone.now() + timedelta(days=3),
        )

        self.assertEqual(assignment.status, "Open")

    def test_assignment_due_date_cannot_be_in_past(self):
        assignment = Assignment(
            course=self.course,
            title="Old Homework",
            description="Test",
            topic="Django",
            due_date=timezone.now() - timedelta(days=1),
        )

        with self.assertRaises(ValidationError):
            assignment.full_clean()


class SubmissionModelTests(TestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="testpass123",
            is_student=True,
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            age=20,
            is_approved=True,
        )

        self.teacher_user = User.objects.create_user(
            username="teacher",
            email="teacher@example.com",
            password="testpass123",
            is_teacher=True,
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            age=30,
            education="Computer Science",
            experience_years=5,
            is_approved=True,
        )

        self.course = Course.objects.create(
            name="Python Course",
            description="Test course",
            teacher=self.teacher_profile,
            price=Decimal("10.00"),
        )

        self.assignment = Assignment.objects.create(
            course=self.course,
            title="Homework",
            description="Test",
            topic="Python",
            due_date=timezone.now() + timedelta(days=5),
        )

    def test_submission_string_representation(self):
        submission = Submission.objects.create(
            assignment=self.assignment,
            student=self.student_profile,
        )

        self.assertEqual(
            str(submission),
            f"{self.assignment.title} - {self.student_user.username}",
        )

    def test_submission_sets_graded_at_when_grade_exists(self):
        submission = Submission.objects.create(
            assignment=self.assignment,
            student=self.student_profile,
            grade=5.5,
        )

        self.assertIsNotNone(submission.graded_at)


class AssignmentViewTests(TestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="testpass123",
            is_student=True,
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            age=20,
            is_approved=True,
        )

        self.teacher_user = User.objects.create_user(
            username="teacher",
            email="teacher@example.com",
            password="testpass123",
            is_teacher=True,
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            age=30,
            education="Computer Science",
            experience_years=5,
            is_approved=True,
        )

        self.course = Course.objects.create(
            name="Django Course",
            description="Test course",
            teacher=self.teacher_profile,
            price=Decimal("10.00"),
        )

        self.assignment = Assignment.objects.create(
            course=self.course,
            title="Homework 1",
            description="Test assignment",
            topic="Django",
            due_date=timezone.now() + timedelta(days=7),
        )

    def test_assignment_list_requires_login(self):
        response = self.client.get(reverse("assignments:assignment_list"))

        self.assertEqual(response.status_code, 302)

    def test_teacher_can_view_assignment_list(self):
        self.client.login(username="teacher", password="testpass123")

        response = self.client.get(reverse("assignments:assignment_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Homework 1")

    def test_student_without_paid_enrollment_cannot_view_assignment_detail(self):
        self.client.login(username="student", password="testpass123")

        response = self.client.get(
            reverse("assignments:assignment_detail", kwargs={"pk": self.assignment.pk})
        )

        self.assertEqual(response.status_code, 403)

    def test_student_with_paid_enrollment_can_view_assignment_detail(self):
        Enrollment.objects.create(
            student=self.student_profile,
            course=self.course,
            is_paid=True,
        )

        self.client.login(username="student", password="testpass123")

        response = self.client.get(
            reverse("assignments:assignment_detail", kwargs={"pk": self.assignment.pk})
        )

        self.assertEqual(response.status_code, 200)

    def test_student_can_submit_assignment_with_paid_enrollment(self):
        Enrollment.objects.create(
            student=self.student_profile,
            course=self.course,
            is_paid=True,
        )

        self.client.login(username="student", password="testpass123")

        response = self.client.post(
            reverse("assignments:submit", kwargs={"assignment_id": self.assignment.pk}),
            {},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Submission.objects.filter(
                assignment=self.assignment,
                student=self.student_profile,
            ).exists()
        )

    def test_teacher_can_access_teacher_submissions(self):
        self.client.login(username="teacher", password="testpass123")

        response = self.client.get(reverse("assignments:teacher_submissions"))

        self.assertEqual(response.status_code, 200)
