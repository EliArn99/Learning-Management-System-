from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from users.forms import StudentRegisterForm, TeacherRegisterForm
from users.models import StudentProfile, TeacherProfile


User = get_user_model()


class UserModelTests(TestCase):
    def test_student_profile_requires_adult_age(self):
        user = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="testpass123",
            is_student=True,
        )

        profile = StudentProfile(
            user=user,
            age=17,
        )

        with self.assertRaises(Exception):
            profile.full_clean()

    def test_teacher_experience_cannot_be_negative(self):
        user = User.objects.create_user(
            username="teacher",
            email="teacher@example.com",
            password="testpass123",
            is_teacher=True,
        )

        profile = TeacherProfile(
            user=user,
            age=30,
            experience_years=-1,
        )

        with self.assertRaises(Exception):
            profile.full_clean()


class UserRegistrationFormTests(TestCase):
    def test_student_register_form_creates_student_user_and_profile(self):
        form = StudentRegisterForm(
            data={
                "full_name": "Ivan Ivanov",
                "email": "ivan@example.com",
                "age": 20,
                "achievements": "Good student",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        user = form.save()

        self.assertTrue(user.is_student)
        self.assertFalse(user.is_teacher)
        self.assertTrue(StudentProfile.objects.filter(user=user).exists())

    def test_teacher_register_form_creates_teacher_user_and_profile(self):
        form = TeacherRegisterForm(
            data={
                "full_name": "Petar Petrov",
                "email": "petar@example.com",
                "age": 30,
                "education": "Computer Science",
                "experience_years": 5,
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        user = form.save()

        self.assertTrue(user.is_teacher)
        self.assertFalse(user.is_student)
        self.assertTrue(TeacherProfile.objects.filter(user=user).exists())


class UserViewTests(TestCase):
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
            is_approved=False,
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

    def test_login_page_returns_200(self):
        response = self.client.get(reverse("users:login"))

        self.assertEqual(response.status_code, 200)

    def test_unapproved_student_redirects_to_approval_pending(self):
        self.client.login(username="student", password="testpass123")

        response = self.client.get(reverse("users:profile"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("users:approval_pending"))

    def test_approved_teacher_can_access_profile(self):
        self.client.login(username="teacher", password="testpass123")

        response = self.client.get(reverse("users:profile"))

        self.assertEqual(response.status_code, 200)

    def test_edit_profile_requires_login(self):
        response = self.client.get(reverse("users:edit_profile"))

        self.assertEqual(response.status_code, 302)
