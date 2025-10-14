from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from courses.models import Course
from users.models import TeacherProfile

User = get_user_model()

QUESTION_TYPE_CHOICES = (
    ('MC', 'Множествен избор (Един верен)'),
    ('MM', 'Множествен избор (Множество верни)'),
    ('OT', 'Свободен текст (Ръчна оценка)'),
    ('TF', 'Вярно/Грешно'),
)


class Quiz(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    created_by = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='quizzes')
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)

    time_limit = models.IntegerField(
        default=60,
        help_text="Времеви лимит за теста в минути (напр. 60)."  # КОРИГИРАН help_text
    )

    num_questions_to_select = models.IntegerField(
        default=0,
        help_text="Брой въпроси, които да се изберат на случаен принцип (0 за всички)."
    )

    def is_active(self):
        now = timezone.now()
        return (self.available_from is None or self.available_from <= now) and \
            (self.available_until is None or self.available_until >= now)

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500)
    points = models.IntegerField(
        default=1,  # You can choose your default, 1 is common
        help_text="Points awarded for a correct answer to this question."
    )
    type = models.CharField(
        max_length=2,
        choices=QUESTION_TYPE_CHOICES,
        default='MC',
        help_text="Тип на въпроса."
    )

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class StudentQuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)

    class Meta:
        unique_together = ('quiz', 'student')

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} - Attempt"


class Submission(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(default=0)

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title}"


class StudentAnswer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='student_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.SET_NULL, null=True, blank=True)
    text_response = models.TextField(blank=True, null=True)
    points_awarded = models.IntegerField(default=0)
