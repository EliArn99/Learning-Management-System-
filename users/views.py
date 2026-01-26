from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404

from quizz.models import Quiz
from .forms import StudentRegisterForm, TeacherRegisterForm, StudentProfileForm, TeacherProfileForm
from .models import StudentProfile, TeacherProfile, CustomUser
from django.contrib.auth.decorators import login_required


@login_required
def student_profile_view(request):
    profile = get_object_or_404(StudentProfile, user=request.user)

    if not profile.is_approved:
        return redirect('users:approval_pending')

    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профилът е успешно обновен!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Възникна грешка при обновяване на профила. Моля, проверете данните.')
    else:
        form = StudentProfileForm(instance=profile)

    upcoming_quizzes = []
    try:
        if profile.is_approved:
            upcoming_quizzes = Quiz.objects.filter(course__students=request.user, is_active=True)
    except Exception as e:
        print("❗️Грешка при извличане на тестове:", e)


    return render(request, 'users/student_profile.html', {
        'form': form,
        'student': profile,
        'upcoming_quizzes': upcoming_quizzes
    })


@login_required
def teacher_profile_view(request):
    profile = get_object_or_404(TeacherProfile, user=request.user)

    if not profile.is_approved:
        return redirect('users:approval_pending')

    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профилът е успешно обновен!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Възникна грешка при обновяване на профила. Моля, проверете данните.')
    else:
        form = TeacherProfileForm(instance=profile)

    return render(request, 'users/teacher_profile.html', {'form': form, 'teacher': profile})


@login_required
def approval_pending_view(request):

    user = request.user
    profile = None

    if user.is_student:
        try:
            profile = StudentProfile.objects.get(user=user)
        except StudentProfile.DoesNotExist:

            pass
    elif user.is_teacher:
        try:
            profile = TeacherProfile.objects.get(user=user)
        except TeacherProfile.DoesNotExist:
            pass

    if profile and profile.is_approved:
        if user.is_student:
            return redirect('dashboards:student_dashboard')
        elif user.is_teacher:
            return redirect('dashboards:teacher_dashboard')

    return render(request, 'users/account_approval_pending.html')


def register_student(request):
    if request.method == 'POST':
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Успешна регистрация! Вашият акаунт очаква одобрение.')
            return redirect('users:approval_pending')
        messages.error(request, 'Възникна грешка при регистрацията. Моля, проверете данните си.')
    else:
        form = StudentRegisterForm()
    return render(request, 'users/register_student.html', {'form': form})


def register_teacher(request):
    if request.method == 'POST':
        form = TeacherRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Успешна регистрация! Вашият акаунт очаква одобрение от администратор.')
            return redirect('users:approval_pending')
        messages.error(request, 'Възникна грешка при регистрацията. Моля, проверете данните си.')
    else:
        form = TeacherRegisterForm()
    return render(request, 'users/register_teacher.html', {'form': form})



def custom_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if user.is_student:
                try:
                    profile = StudentProfile.objects.get(user=user)
                    if not profile.is_approved:
                        messages.warning(request, 'Вашият акаунт очаква одобрение от администратор.')
                        return redirect('users:approval_pending')
                    return redirect('dashboards:student_dashboard')
                except StudentProfile.DoesNotExist:
                    messages.error(request, 'Възникна грешка с профила ви. Моля, свържете се с администратор.')
                    return redirect('users:approval_pending')

            elif user.is_teacher:
                try:
                    profile = TeacherProfile.objects.get(user=user)
                    if not profile.is_approved:
                        messages.warning(request, 'Вашият акаунт очаква одобрение от администратор.')
                        return redirect('users:approval_pending')
                    return redirect('dashboards:teacher_dashboard')
                except TeacherProfile.DoesNotExist:
                    messages.error(request, 'Възникна грешка с профила ви. Моля, свържете се с администратор.')
                    return redirect('users:approval_pending')
            else:
                messages.info(request, 'Добре дошли!')
                return redirect('home')

    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})


def custom_logout_view(request):
    logout(request)
    messages.info(request, 'Успешно излязохте от профила си.')
    return render(request, 'users/logout.html')


@login_required
def profile_view(request):
    user = request.user

    profile = None
    if user.is_student:
        profile = get_object_or_404(StudentProfile, user=user)
        if not profile.is_approved:
            return redirect('users:approval_pending')
        # If approved, proceed to render student profile
        try:
            upcoming_quizzes = Quiz.objects.filter(course__students=user, is_active=True)
        except Exception as e:
            print("❗️Грешка при извличане на тестове:", e)
            upcoming_quizzes = []
        return render(request, 'users/student_profile.html', {
            'student': profile,
            'upcoming_quizzes': upcoming_quizzes
        })

    elif user.is_teacher:
        profile = get_object_or_404(TeacherProfile, user=user)
        if not profile.is_approved:
            return redirect('users:approval_pending')
        return render(request, 'users/teacher_profile.html', {
            'teacher': profile
        })

    messages.error(request, 'Невалиден тип потребител или профил не е намерен.')
    return redirect('home')


@login_required
def edit_profile_view(request):
    user = request.user
    profile = None
    ProfileForm = None

    if user.is_student:
        profile = get_object_or_404(StudentProfile, user=user)
        if not profile.is_approved: # Prevent editing unapproved profile
            return redirect('users:approval_pending')
        ProfileForm = StudentProfileForm
    elif user.is_teacher:
        profile = get_object_or_404(TeacherProfile, user=user)
        if not profile.is_approved: # Prevent editing unapproved profile
            return redirect('users:approval_pending')
        ProfileForm = TeacherProfileForm
    else:
        messages.error(request, 'Нямате право да редактирате профил.')
        return redirect('home')

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профилът е успешно обновен!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Възникна грешка при обновяване на профила. Моля, проверете данните.')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'users/edit_profile.html', {'form': form, 'profile': profile})
