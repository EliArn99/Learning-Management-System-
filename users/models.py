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
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)


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
    experience_years = models.PositiveIntegerField(null=True, blank=True)  # ⬅️ добавено
    is_approved = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)


    def clean(self):
        if self.experience_years is not None and self.experience_years < 0:
            raise ValidationError("Опитът не може да е отрицателен.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username




class RegistrationCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    is_used = models.BooleanField(default=False)
    user = models.OneToOneField(CustomUser, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

