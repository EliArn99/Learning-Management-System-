from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError


class CustomUser(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    age = models.PositiveIntegerField()
    achievements = models.TextField(blank=True, null=True)
    faculty_number = models.CharField(max_length=20, unique=True, editable=False)
    is_approved = models.BooleanField(default=False)

    def clean(self):
        if self.age < 18:
            raise ValidationError("Student age must be at least 18.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensure clean() is called on save
        if not self.faculty_number:
            self.faculty_number = f'F-{self.user.id:05}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username


class TeacherProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    age = models.PositiveIntegerField()
    education = models.CharField(max_length=225)
    is_approved = models.BooleanField(default=False)

    def clean(self):
        if self.age < 25:
            raise ValidationError("Teacher age must be at least 25.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username
