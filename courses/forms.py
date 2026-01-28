from django import forms
from .models import Course


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["name", "description", "university_name", "price"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Course Name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "placeholder": "Course Description"}),
            "university_name": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
        }
