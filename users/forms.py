# users/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, StudentProfile, TeacherProfile


class StudentRegisterForm(UserCreationForm):
    age = forms.IntegerField(min_value=18)
    achievements = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_student = True
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                age=self.cleaned_data['age'],
                achievements=self.cleaned_data.get('achievements', '')
            )
        return user


class TeacherRegisterForm(UserCreationForm):
    age = forms.IntegerField(min_value=25)
    education = forms.CharField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_teacher = True
        if commit:
            user.save()
            TeacherProfile.objects.create(
                user=user,
                age=self.cleaned_data['age'],
                education=self.cleaned_data['education']
            )
        return user
