from decimal import Decimal
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from users.models import TeacherProfile, StudentProfile


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
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "course"
            slug_candidate = base_slug
            counter = 1
            while Course.objects.filter(slug=slug_candidate).exists():
                counter += 1
                slug_candidate = f"{base_slug}-{counter}"
            self.slug = slug_candidate
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("courses:course_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return f"{self.name} - {self.university_name}"


class Enrollment(models.Model):
    course = models.ForeignKey(Course, related_name="enrollments", on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    # Access/payment
    is_paid = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    # Payment reference (PayPal order/capture id)
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

    def __str__(self):
        return self.name


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    category = models.ForeignKey(ModuleCategory, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    description = models.TextField()

    class Meta:
        ordering = ("category__name", "title")

    def __str__(self):
        return f"{self.title} ({self.code})"
