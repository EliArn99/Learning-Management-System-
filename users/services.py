from django.shortcuts import redirect

from .models import StudentProfile, TeacherProfile


def get_user_profile(user):
    if user.is_student:
        return StudentProfile.objects.filter(user=user).first()

    if user.is_teacher:
        return TeacherProfile.objects.filter(user=user).first()

    return None


def user_is_approved(user) -> bool:
    profile = get_user_profile(user)
    return bool(profile and profile.is_approved)


def redirect_user_after_login(user):
    profile = get_user_profile(user)

    if user.is_student:
        if profile and profile.is_approved:
            return redirect("dashboards:student_dashboard")
        return redirect("users:approval_pending")

    if user.is_teacher:
        if profile and profile.is_approved:
            return redirect("dashboards:teacher_dashboard")
        return redirect("users:approval_pending")

    return redirect("home")