from django import forms
from django.utils import timezone

from courses.models import Course
from .models import Assignment, Submission


class AssignmentForm(forms.ModelForm):
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
        label="Due Date",
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = Assignment
        fields = ["title", "description", "topic", "due_date", "course"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Assignment Title"}),
            "description": forms.Textarea(attrs={"class": "form-control", "placeholder": "Assignment Description", "rows": 4}),
            "topic": forms.TextInput(attrs={"class": "form-control", "placeholder": "Topic"}),
            "course": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):

        teacher_profile = kwargs.pop("teacher_profile", None)
        super().__init__(*args, **kwargs)

        if teacher_profile is not None:
            self.fields["course"].queryset = Course.objects.filter(teacher=teacher_profile)
        else:
            self.fields["course"].queryset = Course.objects.none()

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        if due_date and due_date <= timezone.now():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due_date


class AssignmentSubmissionForm(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ["file"]
        widgets = {
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def clean_file(self):
        f = self.cleaned_data.get("file")
        if not f:
            raise forms.ValidationError("Please upload a file.")
        max_size = 10 * 1024 * 1024
        if hasattr(f, "size") and f.size > max_size:
            raise forms.ValidationError("File size must be under 10MB.")
        return f


class GradeSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["grade", "feedback"]
        widgets = {
            "grade": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Grade", "step": "0.01", "min": "0"}),
            "feedback": forms.Textarea(attrs={"class": "form-control", "placeholder": "Feedback", "rows": 4}),
        }

    def clean_grade(self):
        grade = self.cleaned_data.get("grade")

        if grade is None:
            return grade

        try:
            grade_value = float(grade)
        except (TypeError, ValueError):
            raise forms.ValidationError("Invalid grade value.")

        if grade_value < 0 or grade_value > 100:
            raise forms.ValidationError("Grade must be between 0 and 100.")

        return grade
