from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

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
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes")
    created_by = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="quizzes")
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)

    time_limit = models.IntegerField(
        default=60,
        help_text="Времеви лимит за теста в минути (напр. 60).",
    )

    num_questions_to_select = models.IntegerField(
        default=0,
        help_text="Брой въпроси, които да се изберат на случаен принцип (0 за всички).",
    )

    def is_active(self):
        now = timezone.now()
        return (self.available_from is None or self.available_from <= now) and (
            self.available_until is None or self.available_until >= now
        )

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.CharField(max_length=500)
    points = models.IntegerField(
        default=1,
        help_text="Points awarded for a correct answer to this question.",
    )
    type = models.CharField(
        max_length=2,
        choices=QUESTION_TYPE_CHOICES,
        default="MC",
        help_text="Тип на въпроса.",
    )

    def clean(self):
        # Basic data rules
        if self.points is not None and self.points <= 0:
            raise ValidationError({"points": "Точките трябва да са положително число."})

        # Correctness rules (only if question exists and answers exist)
        if not self.pk:
            return

        correct_count = self.answers.filter(is_correct=True).count()

        if self.type in ("MC", "TF"):
            if correct_count != 1:
                raise ValidationError("За този тип въпрос трябва да има точно 1 верен отговор.")
        elif self.type == "MM":
            if correct_count < 1:
                raise ValidationError("За този тип въпрос трябва да има поне 1 верен отговор.")
        elif self.type == "OT":
            if correct_count != 0:
                raise ValidationError("При 'Свободен текст' не трябва да има верни отговори (is_correct=True).")

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class StudentQuizAttempt(models.Model):
    """
    Stores:
    - attempt start_time (reliable time limit enforcement)
    - selected_question_ids (prevents submitting answers for unseen questions)
    - is_complete flag
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
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
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(default=0)

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title}"


class StudentAnswer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="student_answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.SET_NULL, null=True, blank=True)
    text_response = models.TextField(blank=True, null=True)
    points_awarded = models.IntegerField(default=0)
