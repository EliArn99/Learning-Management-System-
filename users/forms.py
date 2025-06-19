from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.forms import AuthenticationForm

class StudentRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'



class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Потребителско име",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Въведи потребителско име'
        })
    )
    password = forms.CharField(
        label="Парола",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Въведи парола'
        })
    )








# from django import forms
# from django.contrib.auth.forms import UserCreationForm
# from .models import CustomUser, StudentProfile, TeacherProfile, RegistrationCode


# class StudentRegisterForm(UserCreationForm):
#     full_name = forms.CharField(label="Име и фамилия", max_length=100)
#     age = forms.IntegerField(min_value=18)
#     achievements = forms.CharField(widget=forms.Textarea, required=False)
#     registration_code = forms.CharField(max_length=20, label="Регистрационен код")

#     class Meta:
#         model = CustomUser
#         fields = ['full_name', 'email', 'password1', 'password2']

#     def clean_registration_code(self):
#         code = self.cleaned_data['registration_code']
#         try:
#             reg_code = RegistrationCode.objects.get(code=code, is_used=False)
#         except RegistrationCode.DoesNotExist:
#             raise forms.ValidationError("Невалиден или вече използван регистрационен код.")
#         return reg_code

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.is_student = True
#         user.username = self.cleaned_data['full_name']  # използваме реалното име като username
#         if commit:
#             user.save()
#             StudentProfile.objects.create(
#                 user=user,
#                 age=self.cleaned_data['age'],
#                 achievements=self.cleaned_data.get('achievements', '')
#             )

#             # маркирай кода като използван
#             reg_code = self.cleaned_data['registration_code']
#             reg_code.user = user
#             reg_code.is_used = True
#             reg_code.save()
#         return user


# class TeacherRegisterForm(UserCreationForm):
#     full_name = forms.CharField(label="Име и фамилия", max_length=100)
#     age = forms.IntegerField(min_value=25)
#     education = forms.CharField()
#     registration_code = forms.CharField(max_length=20, label="Регистрационен код")

#     class Meta:
#         model = CustomUser
#         fields = ['full_name', 'email', 'password1', 'password2']

#     def clean_registration_code(self):
#         code = self.cleaned_data['registration_code']
#         try:
#             reg_code = RegistrationCode.objects.get(code=code, is_used=False)
#         except RegistrationCode.DoesNotExist:
#             raise forms.ValidationError("Невалиден или вече използван регистрационен код.")
#         return reg_code

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.is_teacher = True
#         user.username = self.cleaned_data['full_name']  # използваме реалното име като username
#         if commit:
#             user.save()
#             TeacherProfile.objects.create(
#                 user=user,
#                 age=self.cleaned_data['age'],
#                 education=self.cleaned_data['education']
#             )

#             # маркирай кода като използван
#             reg_code = self.cleaned_data['registration_code']
#             reg_code.user = user
#             reg_code.is_used = True
#             reg_code.save()
#         return user
