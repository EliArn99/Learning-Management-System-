from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    StudentProfileForm,
    StudentRegisterForm,
    TeacherProfileForm,
    TeacherRegisterForm,
)
from .models import StudentProfile, TeacherProfile
from .selectors import get_upcoming_quizzes_for_student
from .services import get_user_profile, redirect_user_after_login


@login_required
def student_profile_view(request):
    profile = get_object_or_404(StudentProfile, user=request.user)

    if not profile.is_approved:
        return redirect("users:approval_pending")

    upcoming_quizzes = get_upcoming_quizzes_for_student(request.user)

    return render(
        request,
        "users/student_profile.html",
        {
            "student": profile,
            "upcoming_quizzes": upcoming_quizzes,
        },
    )


@login_required
def teacher_profile_view(request):
    profile = get_object_or_404(TeacherProfile, user=request.user)

    if not profile.is_approved:
        return redirect("users:approval_pending")

    return render(
        request,
        "users/teacher_profile.html",
        {
            "teacher": profile,
        },
    )


@login_required
def approval_pending_view(request):
    profile = get_user_profile(request.user)

    if profile and profile.is_approved:
        return redirect_user_after_login(request.user)

    return render(request, "users/account_approval_pending.html")


def register_student(request):
    if request.method == "POST":
        form = StudentRegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                "Успешна регистрация! Вашият акаунт очаква одобрение.",
            )
            return redirect("users:approval_pending")

        messages.error(
            request,
            "Възникна грешка при регистрацията. Моля, проверете данните си.",
        )
    else:
        form = StudentRegisterForm()

    return render(
        request,
        "users/register_student.html",
        {
            "form": form,
        },
    )


def register_teacher(request):
    if request.method == "POST":
        form = TeacherRegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                "Успешна регистрация! Вашият акаунт очаква одобрение от администратор.",
            )
            return redirect("users:approval_pending")

        messages.error(
            request,
            "Възникна грешка при регистрацията. Моля, проверете данните си.",
        )
    else:
        form = TeacherRegisterForm()

    return render(
        request,
        "users/register_teacher.html",
        {
            "form": form,
        },
    )


def custom_login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if user.is_student or user.is_teacher:
                profile = get_user_profile(user)

                if not profile:
                    messages.error(
                        request,
                        "Възникна грешка с профила ви. Моля, свържете се с администратор.",
                    )
                    return redirect("users:approval_pending")

                if not profile.is_approved:
                    messages.warning(
                        request,
                        "Вашият акаунт очаква одобрение от администратор.",
                    )
                    return redirect("users:approval_pending")

            messages.success(request, "Добре дошли!")
            return redirect_user_after_login(user)

    else:
        form = AuthenticationForm()

    return render(
        request,
        "users/login.html",
        {
            "form": form,
        },
    )


def custom_logout_view(request):
    logout(request)
    messages.info(request, "Успешно излязохте от профила си.")
    return render(request, "users/logout.html")


@login_required
def profile_view(request):
    if request.user.is_student:
        return student_profile_view(request)

    if request.user.is_teacher:
        return teacher_profile_view(request)

    messages.error(request, "Невалиден тип потребител или профил не е намерен.")
    return redirect("home")


@login_required
def edit_profile_view(request):
    profile = get_user_profile(request.user)

    if not profile:
        messages.error(request, "Профилът не е намерен.")
        return redirect("home")

    if not profile.is_approved:
        return redirect("users:approval_pending")

    if request.user.is_student:
        form_class = StudentProfileForm
    elif request.user.is_teacher:
        form_class = TeacherProfileForm
    else:
        messages.error(request, "Нямате право да редактирате профил.")
        return redirect("home")

    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            form.save()
            messages.success(request, "Профилът е успешно обновен!")
            return redirect("users:profile")

        messages.error(
            request,
            "Възникна грешка при обновяване на профила. Моля, проверете данните.",
        )
    else:
        form = form_class(instance=profile)

    return render(
        request,
        "users/edit_profile.html",
        {
            "form": form,
            "profile": profile,
        },
    )
