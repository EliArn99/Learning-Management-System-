from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from users.models import StudentProfile, TeacherProfile

from .forms import MessageForm
from .models import Message
from .services import (
    create_message,
    mark_all_inbox_messages_as_read,
    mark_message_as_read,
    soft_delete_message,
)


User = get_user_model()


class MessageTestMixin:
    def setUp(self):
        self.student_user = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="testpass123",
            is_student=True,
        )
        self.student_profile = self.student_user.studentprofile
        self.student_profile.age = 20
        self.student_profile.is_approved = True
        self.student_profile.save()

        self.teacher_user = User.objects.create_user(
            username="teacher",
            email="teacher@example.com",
            password="testpass123",
            is_teacher=True,
        )
        self.teacher_profile = self.teacher_user.teacherprofile
        self.teacher_profile.age = 30
        self.teacher_profile.education = "Computer Science"
        self.teacher_profile.experience_years = 5
        self.teacher_profile.is_approved = True
        self.teacher_profile.save()

        self.message = Message.objects.create(
            sender=self.teacher_user,
            receiver=self.student_user,
            subject="Test subject",
            content="Hello student",
            is_read=False,
        )


class MessageModelTests(MessageTestMixin, TestCase):
    def test_message_string_representation(self):
        self.assertIn("From teacher to student", str(self.message))

    def test_soft_deleted_messages_are_hidden_from_default_manager(self):
        self.message.deleted = True
        self.message.save(update_fields=["deleted"])

        self.assertFalse(Message.objects.filter(pk=self.message.pk).exists())
        self.assertTrue(Message.all_objects.filter(pk=self.message.pk).exists())


class MessageFormTests(MessageTestMixin, TestCase):
    def test_student_can_send_to_approved_teacher(self):
        form = MessageForm(
            user=self.student_user,
            data={
                "receiver": self.teacher_user.id,
                "subject": "Question",
                "content": "Hello teacher",
            },
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_user_cannot_send_to_self(self):
        form = MessageForm(
            user=self.teacher_user,
            data={
                "receiver": self.teacher_user.id,
                "subject": "Self",
                "content": "Message to self",
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("receiver", form.errors)

    def test_empty_content_is_invalid(self):
        form = MessageForm(
            user=self.student_user,
            data={
                "receiver": self.teacher_user.id,
                "subject": "Question",
                "content": "",
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)


class MessageServiceTests(MessageTestMixin, TestCase):
    def test_create_message(self):
        message = create_message(
            sender=self.student_user,
            receiver=self.teacher_user,
            subject="New message",
            content="Hello",
        )

        self.assertEqual(message.sender, self.student_user)
        self.assertEqual(message.receiver, self.teacher_user)
        self.assertEqual(message.subject, "New message")

    def test_mark_message_as_read(self):
        mark_message_as_read(self.message)
        self.message.refresh_from_db()

        self.assertTrue(self.message.is_read)

    def test_mark_all_inbox_messages_as_read(self):
        Message.objects.create(
            sender=self.teacher_user,
            receiver=self.student_user,
            subject="Second",
            content="Second unread message",
            is_read=False,
        )

        updated_count = mark_all_inbox_messages_as_read(self.student_user)

        self.assertEqual(updated_count, 2)
        self.assertFalse(
            Message.objects.filter(receiver=self.student_user, is_read=False).exists()
        )

    def test_soft_delete_message(self):
        soft_delete_message(self.message)

        self.assertFalse(Message.objects.filter(pk=self.message.pk).exists())
        self.assertTrue(
            Message.all_objects.filter(pk=self.message.pk, deleted=True).exists()
        )


class MessageViewTests(MessageTestMixin, TestCase):
    def test_messages_home_requires_login(self):
        response = self.client.get(reverse("messaging:home"))

        self.assertEqual(response.status_code, 302)

    def test_messages_home_returns_200_for_logged_user(self):
        self.client.login(username="student", password="testpass123")

        response = self.client.get(reverse("messaging:home"))

        self.assertEqual(response.status_code, 200)

    def test_inbox_returns_200_and_marks_messages_as_read(self):
        self.client.login(username="student", password="testpass123")

        response = self.client.get(reverse("messaging:inbox"))

        self.assertEqual(response.status_code, 200)

        self.message.refresh_from_db()
        self.assertTrue(self.message.is_read)

    def test_sent_returns_200_for_sender(self):
        self.client.login(username="teacher", password="testpass123")

        response = self.client.get(reverse("messaging:sent"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello student")

    def test_receiver_can_open_message_detail(self):
        self.client.login(username="student", password="testpass123")

        response = self.client.get(
            reverse("messaging:message_detail", kwargs={"pk": self.message.pk})
        )

        self.assertEqual(response.status_code, 200)

    def test_sender_cannot_open_receiver_detail_page(self):
        self.client.login(username="teacher", password="testpass123")

        response = self.client.get(
            reverse("messaging:message_detail", kwargs={"pk": self.message.pk})
        )

        self.assertEqual(response.status_code, 403)

    def test_send_message_view_creates_message(self):
        self.client.login(username="student", password="testpass123")

        response = self.client.post(
            reverse("messaging:send_message"),
            {
                "receiver": self.teacher_user.id,
                "subject": "Question",
                "content": "Hello teacher",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Message.objects.filter(
                sender=self.student_user,
                receiver=self.teacher_user,
                subject="Question",
            ).exists()
        )
