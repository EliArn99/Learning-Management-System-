from django import forms
from users.models import StudentProfile, TeacherProfile

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['age', 'achievements']
        widgets = {
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'achievements': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'List any achievements...'}),
        }

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age and age < 18:
            raise forms.ValidationError("Student must be at least 18 years old.")
        return age


class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        fields = ['age', 'education']
        widgets = {
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'education': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your highest degree'}),
        }

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age and age < 25:
            raise forms.ValidationError("Teacher must be at least 25 years old.")
        return age