from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from courses.models import Course, Enrollment, Module, ModuleCategory
from users.models import StudentProfile, TeacherProfile

User = get_user_model()


class CourseModelTests(TestCase):
    def test_slug_is_generated(self):
        course = Course.objects.create(
            name="Python Basics",
            description="Test description",
            price=Decimal("10.00"),
        )

        self.assertEqual(course.slug, "python-basics")

    def test_duplicate_slug_gets_suffix(self):
        Course.objects.create(
            name="Python Basics",
            description="First course",
        )

        second_course = Course.objects.create(
            name="Python Basics",
            description="Second course",
        )

        self.assertEqual(second_course.slug, "python-basics-2")

    def test_course_absolute_url(self):
        course = Course.objects.create(
            name="Django Advanced",
            description="Test description",
        )

        self.assertEqual(
            course.get_absolute_url(),
            reverse("courses:course_detail", kwargs={"slug": course.slug}),
        )

    def test_negative_price_is_invalid(self):
        course = Course(
            name="Invalid Course",
            description="Test description",
            price=Decimal("-1.00"),
        )

        with self.assertRaises(Exception):
            course.full_clean()


class ModuleModelTests(TestCase):
    def test_module_string_representation(self):
        course = Course.objects.create(
            name="Django Course",
            description="Test description",
        )
        category = ModuleCategory.objects.create(name="Backend")

        module = Module.objects.create(
            course=course,
            category=category,
            title="Models",
            code="DJ01",
            description="Django models module",
        )

        self.assertEqual(str(module), "Models (DJ01)")


class CourseViewTests(TestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="testpass123",
            is_student=True,
        )

        self.teacher_user = User.objects.create_user(
            username="teacher",
            email="teacher@example.com",
            password="testpass123",
            is_teacher=True,
        )

        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            age=20,
        )

        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
        )

        self.course = Course.objects.create(
            name="Python Basics",
            description="Test description",
            teacher=self.teacher_profile,
            price=Decimal("20.00"),
        )

    def test_course_list_returns_200(self):
        response = self.client.get(reverse("courses:course_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python Basics")

    def test_course_detail_requires_login(self):
        response = self.client.get(
            reverse("courses:course_detail", kwargs={"slug": self.course.slug})
        )

        self.assertEqual(response.status_code, 302)

    def test_logged_in_user_can_view_course_detail(self):
        self.client.login(username="student", password="testpass123")

        response = self.client.get(
            reverse("courses:course_detail", kwargs={"slug": self.course.slug})
        )

        self.assertEqual(response.status_code, 200)

    def test_teacher_can_create_course(self):
        self.client.login(username="teacher", password="testpass123")

        response = self.client.post(
            reverse("courses:create_course"),
            {
                "name": "New Course",
                "description": "New course description",
                "university_name": "Test University",
                "price": "15.00",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Course.objects.filter(name="New Course").exists())

    def test_student_cannot_create_course(self):
        self.client.login(username="student", password="testpass123")

        response = self.client.post(
            reverse("courses:create_course"),
            {
                "name": "Student Course",
                "description": "Invalid",
                "university_name": "Test University",
                "price": "15.00",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Course.objects.filter(name="Student Course").exists())

    def test_student_can_create_unpaid_enrollment(self):
        self.client.login(username="student", password="testpass123")

        response = self.client.post(
            reverse("courses:course_detail", kwargs={"slug": self.course.slug})
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Enrollment.objects.filter(
                student=self.student_profile,
                course=self.course,
                is_paid=False,
            ).exists()
        )
