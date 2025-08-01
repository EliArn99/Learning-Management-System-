from django import forms

from courses.models import Course
from .models import Assignment, Submission
from django.utils import timezone


class AssignmentForm(forms.ModelForm):
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Due Date",
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher)
        else:
            self.fields['course'].queryset = Course.objects.none()

    class Meta:
        model = Assignment
        fields = ['title', 'description', 'topic', 'due_date', 'course']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Assignment Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Assignment Description'}),
            'topic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Topic'}),
            'course': forms.Select(attrs={'class': 'form-select'}), 
        }

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due_date


class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['assignment', 'file']




class GradeSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['grade', 'feedback']
        widgets = {
            'grade': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Grade'}),
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Feedback'}),
        }
