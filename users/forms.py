from django import forms
from django.contrib.auth.forms import UserCreationForm

from assignments.models import Submission
from .models import CustomUser, StudentProfile, TeacherProfile


class StudentRegisterForm(UserCreationForm):
    full_name = forms.CharField(label="Име и фамилия", max_length=100)
    age = forms.IntegerField(min_value=18)
    achievements = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_student = True
        user.username = self.cleaned_data['full_name']
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                age=self.cleaned_data['age'],
                achievements=self.cleaned_data.get('achievements', '')
            )
        return user


class TeacherRegisterForm(UserCreationForm):
    full_name = forms.CharField(label="Име и фамилия", max_length=100)
    age = forms.IntegerField(min_value=25)
    education = forms.CharField()

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_teacher = True
        user.username = self.cleaned_data['full_name']
        if commit:
            user.save()
            TeacherProfile.objects.create(
                user=user,
                age=self.cleaned_data['age'],
                education=self.cleaned_data['education']
            )
        return user



# class StudentProfileForm(forms.ModelForm):
#     class Meta:
#         model = StudentProfile
#         fields = ['age', 'achievements', 'profile_picture']
#         widgets = {
#             'achievements': forms.Textarea(attrs={'rows': 4}),
#         }
#
#
# class TeacherProfileForm(forms.ModelForm):
#     class Meta:
#         model = TeacherProfile
#         fields = ['age', 'education', 'experience_years', 'profile_picture']
#         widgets = {
#             'education': forms.TextInput(attrs={'placeholder': 'Висше образование и специалност'}),
#             'experience_years': forms.NumberInput(attrs={'min': 0}),
#         }


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['age', 'achievements', 'profile_picture']  # faculty_number се генерира автоматично

class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        fields = ['age', 'education', 'experience_years', 'profile_picture']


class SubmissionGradeForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['grade', 'feedback', 'graded_file']

        widgets = {
            'grade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 2, 'max': 6}),
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'graded_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


