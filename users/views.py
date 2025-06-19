from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import StudentRegisterForm, LoginForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout


def home(request):
    return render(request, 'users/home.html')


def register(request):
    if request.method == 'POST':
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"Успешна регистрация на {username}!")
            return redirect('users:home')
    else:
        form = StudentRegisterForm()

    return render(request, "users/register.html", {'form': form})


def user_login(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('users:home')
        else:
            messages.error(request, "Грешно потребителско име или парола.")
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})


def logout(request):
    auth_logout(request)
    return redirect('users:home')




@login_required
def profile(request):
    return render(request, 'users/profile.html')


@login_required
def dashboard(request):
    return render(request, 'users/dashboard.html')




# from django.contrib.auth import login, logout
# from django.contrib.auth.forms import AuthenticationForm
# from django.shortcuts import render, redirect

# from quizz.models import Quiz
# from .forms import StudentRegisterForm, TeacherRegisterForm, StudentProfileForm, TeacherProfileForm, SubmissionGradeForm
# from .models import StudentProfile, TeacherProfile
# from django.contrib.auth.decorators import login_required


# @login_required
# def student_profile_view(request):
#     profile, created = StudentProfile.objects.get_or_create(user=request.user)

#     if request.method == 'POST':
#         form = StudentRegisterForm(request.POST, instance=profile)
#         if form.is_valid():
#             form.save()
#             return redirect('users:student_dashboard')
#     else:
#         form = StudentRegisterForm(instance=profile)

#     return render(request, 'users/student_profile.html', {'form': form})


# @login_required
# def teacher_profile_view(request):
#     profile, created = TeacherProfile.objects.get_or_create(user=request.user)

#     if request.method == 'POST':
#         form = TeacherRegisterForm(request.POST, instance=profile)
#         if form.is_valid():
#             form.save()
#             return redirect('users:teacher_dashboard')
#     else:
#         form = TeacherRegisterForm(instance=profile)

#     return render(request, 'users/teacher_profile.html', {'form': form})


# def approval_pending_view():
#     return redirect('users:approval_pending')


# def register_student(request):
#     if request.method == 'POST':
#         form = StudentRegisterForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.is_student = True
#             user.save()
#             StudentProfile.objects.create(
#                 user=user,
#                 age=form.cleaned_data['age']  # only if age is in the form
#             )
#             login(request, user)
#             return redirect('users:student_profile')  # 👈 директно към профила
#     else:
#         form = StudentRegisterForm()
#     return render(request, 'users/register_student.html', {'form': form})


# def register_teacher(request):
#     if request.method == 'POST':
#         form = TeacherRegisterForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.is_teacher = True
#             user.save()
#             TeacherProfile.objects.create(user=user)
#             login(request, user)
#             return redirect('users:teacher_profile')  # 👈 директно към профила
#     else:
#         form = TeacherRegisterForm()
#     return render(request, 'users/register_teacher.html', {'form': form})



# def custom_login_view(request):
#     if request.method == 'POST':
#         form = AuthenticationForm(request, data=request.POST)
#         if form.is_valid():
#             user = form.get_user()
#             login(request, user)

#             if user.is_student:
#                 try:
#                     profile = StudentProfile.objects.get(user=user)
#                     if not profile.is_approved:
#                         return redirect('users:approval_pending')
#                     return redirect('dashboards:student_dashboard')
#                 except StudentProfile.DoesNotExist:
#                     return redirect('users:approval_pending')

#             elif user.is_teacher:
#                 try:
#                     profile = TeacherProfile.objects.get(user=user)
#                     if not profile.is_approved:
#                         return redirect('users:approval_pending')
#                     return redirect('dashboards:teacher_dashboard')
#                 except TeacherProfile.DoesNotExist:
#                     return redirect('users:approval_pending')
#             else:
#                 return redirect('home')
#     else:
#         form = AuthenticationForm()
#     return render(request, 'users/login.html', {'form': form})


# def custom_logout_view(request):
#     logout(request)
#     return render(request, 'users/logout.html')




# @login_required
# def profile_view(request):
#     user = request.user

#     if user.is_student:
#         try:
#             student = StudentProfile.objects.get(user=user)
#         except StudentProfile.DoesNotExist:
#             return redirect('users:student_profile')
#         try:
#             upcoming_quizzes = Quiz.objects.filter(course__students=user, is_active=True)
#         except Exception as e:
#             print("❗️Грешка при извличане на тестове:", e)
#             upcoming_quizzes = []

#         return render(request, 'users/student_profile.html', {
#             'student': student,
#             'upcoming_quizzes': upcoming_quizzes
#         })

#     elif user.is_teacher:
#         try:
#             teacher = TeacherProfile.objects.get(user=user)
#         except TeacherProfile.DoesNotExist:
#             return redirect('users:teacher_profile')

#         return render(request, 'users/teacher_profile.html', {
#             'teacher': teacher
#         })

#     return redirect('home')




# @login_required
# def edit_profile_view(request):
#     user = request.user

#     if hasattr(user, 'studentprofile'):
#         profile = user.studentprofile
#         form_class = StudentProfileForm
#     elif hasattr(user, 'teacherprofile'):
#         profile = user.teacherprofile
#         form_class = TeacherProfileForm
#     else:
#         return redirect('users:profile')  # fallback

#     if request.method == 'POST':
#         form = form_class(request.POST, request.FILES, instance=profile)
#         if form.is_valid():
#             form.save()
#             return redirect('users:profile')
#     else:
#         form = form_class(instance=profile)

#     return render(request, 'users/edit_profile.html', {'form': form})

