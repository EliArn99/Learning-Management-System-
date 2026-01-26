from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.text import slugify

from .models import CustomUser, StudentProfile, TeacherProfile


def generate_unique_username(full_name: str) -> str:
    base = slugify(full_name)[:30] or "user"
    candidate = base
    i = 1
    while CustomUser.objects.filter(username=candidate).exists():
        i += 1
        candidate = f"{base}-{i}"
    return candidate


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
        user.is_active = True

        user.username = generate_unique_username(self.cleaned_data['full_name'])

        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                age=self.cleaned_data['age'],
                achievements=self.cleaned_data.get('achievements', ''),
                is_approved=False,
            )
        return user


class TeacherRegisterForm(UserCreationForm):
    full_name = forms.CharField(label="Име и фамилия", max_length=100)
    age = forms.IntegerField(min_value=25)
    education = forms.CharField()
    experience_years = forms.IntegerField(min_value=0, required=False)

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_teacher = True
        user.is_active = True
        user.username = generate_unique_username(self.cleaned_data['full_name'])

        if commit:
            user.save()
            TeacherProfile.objects.create(
                user=user,
                age=self.cleaned_data.get('age'),
                education=self.cleaned_data.get('education', ''),
                experience_years=self.cleaned_data.get('experience_years'),
                is_approved=False,
            )
        return user
