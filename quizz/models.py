from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from courses.models import Course
from users.models import TeacherProfile


User = get_user_model()


QUESTION_TYPE_CHOICES = (
    ("MC", "Множествен избор (Един верен)"),
    ("MM", "Множествен избор (Множество верни)"),
    ("OT", "Свободен текст (Ръчна оценка)"),
    ("TF", "Вярно/Грешно"),
)


class Quiz(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="quizzes",
    )
    created_by = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="quizzes",
    )
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)
    time_limit = models.IntegerField(
        default=60,
        help_text="Времеви лимит за теста в минути.",
    )
    num_questions_to_select = models.IntegerField(
        default=0,
        help_text="Брой въпроси за случаен избор. 0 означава всички.",
    )

    class Meta:
        ordering = ("-id",)
        indexes = [
            models.Index(fields=["course", "available_from", "available_until"]),
            models.Index(fields=["created_by"]),
        ]

    def clean(self):
        if self.time_limit is not None and self.time_limit <= 0:
            raise ValidationError({"time_limit": "Времевият лимит трябва да е положително число."})

        if self.num_questions_to_select is not None and self.num_questions_to_select < 0:
            raise ValidationError({"num_questions_to_select": "Броят въпроси не може да е отрицателен."})

        if self.available_from and self.available_until and self.available_until <= self.available_from:
            raise ValidationError("Крайната дата трябва да е след началната дата.")

    def is_active(self):
        now = timezone.now()
        return (
            self.available_from is None or self.available_from <= now
        ) and (
            self.available_until is None or self.available_until >= now
        )

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    text = models.CharField(max_length=500)
    points = models.IntegerField(
        default=1,
        help_text="Points awarded for a correct answer.",
    )
    type = models.CharField(
        max_length=2,
        choices=QUESTION_TYPE_CHOICES,
        default="MC",
    )

    class Meta:
        ordering = ("id",)
        indexes = [
            models.Index(fields=["quiz", "type"]),
        ]

    def clean(self):
        if self.points is not None and self.points <= 0:
            raise ValidationError({"points": "Точките трябва да са положително число."})

        if not self.pk:
            return

        correct_count = self.answers.filter(is_correct=True).count()

        if self.type in ("MC", "TF") and correct_count != 1:
            raise ValidationError("За този тип въпрос трябва да има точно 1 верен отговор.")

        if self.type == "MM" and correct_count < 1:
            raise ValidationError("За този тип въпрос трябва да има поне 1 верен отговор.")

        if self.type == "OT" and correct_count != 0:
            raise ValidationError("При свободен текст не трябва да има верни отговори.")

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return self.text


class StudentQuizAttempt(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    start_time = models.DateTimeField(default=timezone.now)
    is_complete = models.BooleanField(default=False)
    selected_question_ids = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = ("quiz", "student")
        indexes = [
            models.Index(fields=["quiz", "student"]),
            models.Index(fields=["student", "is_complete"]),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} - Attempt"


class Submission(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(default=0)

    class Meta:
        ordering = ("-submitted_at",)
        indexes = [
            models.Index(fields=["quiz", "student"]),
            models.Index(fields=["student", "submitted_at"]),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title}"


class StudentAnswer(models.Model):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="student_answers",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
    )
    selected_answer = models.ForeignKey(
        Answer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    text_response = models.TextField(blank=True, null=True)
    points_awarded = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["submission", "question"]),
        ]
