from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from users.models import StudentProfile, TeacherProfile


class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    university_name = models.CharField(max_length=255, default="Your University Name")

    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="taught_courses",
    )

    slug = models.SlugField(unique=True, blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["teacher"]),
            models.Index(fields=["created_at"]),
        ]

    def clean(self):
        if self.price < 0:
            raise ValidationError({"price": "Price cannot be negative."})

    def save(self, *args, **kwargs):
        # Slug is generated only once to keep stable URLs.
        if not self.slug:
            base_slug = slugify(self.name) or "course"
            slug_candidate = base_slug
            counter = 1

            while Course.objects.filter(slug=slug_candidate).exists():
                counter += 1
                slug_candidate = f"{base_slug}-{counter}"

            self.slug = slug_candidate

        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("courses:course_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return f"{self.name} - {self.university_name}"


class Enrollment(models.Model):
    course = models.ForeignKey(
        Course,
        related_name="enrollments",
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    is_paid = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ("student", "course")
        ordering = ("-enrolled_at",)
        indexes = [
            models.Index(fields=["student", "course"]),
            models.Index(fields=["course", "is_paid"]),
            models.Index(fields=["student", "is_paid"]),
        ]

    def __str__(self):
        return f"{self.student.user.username} - {self.course.name}"


class ModuleCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "Module categories"

    def __str__(self):
        return self.name


class Module(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="modules",
    )
    category = models.ForeignKey(
        ModuleCategory,
        on_delete=models.CASCADE,
        related_name="modules",
    )
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("category__name", "title")
        indexes = [
            models.Index(fields=["course", "category"]),
            models.Index(fields=["code"]),
        ]

    def clean(self):
        if len(self.code.strip()) < 2:
            raise ValidationError({"code": "Module code is too short."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.code})"
