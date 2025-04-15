from django import forms
from .models import Course, Enrollment
from django.utils.text import slugify

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description', 'university_name', 'teacher']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Course Description'}),
            'university_name': forms.TextInput(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        course = super().save(commit=False)
        if not course.slug:
            base_slug = slugify(course.name)
            counter = 1
            slug_candidate = base_slug
            while Course.objects.filter(slug=slug_candidate).exists():
                slug_candidate = f"{base_slug}-{counter}"
                counter += 1
            course.slug = slug_candidate
        if commit:
            course.save()
        return course




class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'course']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        enrollment = super().save(commit=False)
        if not enrollment.slug:
            enrollment.slug = slugify(f"{enrollment.student.user.username}-{enrollment.course.name}")
        if commit:
            enrollment.save()
        return enrollment
