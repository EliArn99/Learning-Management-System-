from django.db import models
from users.models import TeacherProfile, StudentProfile

from django.utils.text import slugify


class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    university_name = models.CharField(max_length=255, default="Your University Name")
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='taught_courses')
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            counter = 1
            slug_candidate = base_slug
            while Course.objects.filter(slug=slug_candidate).exists():
                slug_candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug_candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} - {self.university_name}'


class Enrollment(models.Model):
    course = models.ForeignKey(Course, related_name='enrollments', on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.student.user.username}-{self.course.name}")
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f'{self.student.user.username} - {self.course.name}'


class ModuleCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    category = models.ForeignKey(ModuleCategory, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    description = models.TextField()

    def __str__(self):
        return f"{self.title} ({self.code})"
