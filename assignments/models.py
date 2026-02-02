from django.core.exceptions import ValidationError
from django.db import models
from courses.models import Course
from users.models import StudentProfile
from django.utils import timezone


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=225)
    description = models.TextField()
    topic = models.CharField(max_length=225)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()

    def clean(self):
        if self.due_date < timezone.now():
            raise ValidationError("Due date cannot be in the past.")

    def __str__(self):
        return self.title

    @property
    def status(self):
        return "Open" if timezone.now() < self.due_date else "Closed"


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)

    file = models.FileField(upload_to="submissions/", null=True, blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.FloatField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_file = models.FileField(upload_to="graded_files/", null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["assignment", "student"], name="unique_submission")
        ]
        indexes = [
            models.Index(fields=["assignment", "submitted_at"]),
            models.Index(fields=["student", "submitted_at"]),
            models.Index(fields=["assignment", "grade"]),
        ]

    def __str__(self):
        return f"{self.assignment.title} - {self.student.user.username}"

    def save(self, *args, **kwargs):
        if self.grade is not None and self.graded_at is None:
            self.graded_at = timezone.now()
        super().save(*args, **kwargs)
