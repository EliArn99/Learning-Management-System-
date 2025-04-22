from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404

from .decorators import student_required, teacher_required
from .forms import StudentRegisterForm, TeacherRegisterForm
from .models import StudentProfile, TeacherProfile, CustomUser
from django.contrib.auth.decorators import login_required


@login_required
def profile_redirect_view(request):
    if request.user.is_student:
        return redirect('users:student_profile')
    elif request.user.is_teacher:
        return redirect('users:teacher_profile')
    return redirect('login')


@login_required
def student_profile_view(request):
    profile, created = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('users:student_dashboard')
    else:
        form = StudentProfileForm(instance=profile)

    return render(request, 'users/student_profile.html', {'form': form})


@login_required
def teacher_profile_view(request):
    profile, created = TeacherProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('users:teacher_dashboard')
    else:
        form = TeacherProfileForm(instance=profile)

    return render(request, 'users/teacher_profile.html', {'form': form})


@login_required
def approval_pending_view(request):
    return render(request, 'users/approval_pending.html')



def register_student(request):
    if request.method == 'POST':
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('approval_pending')
    else:
        form = StudentRegisterForm()
    return render(request, 'users/register_student.html', {'form': form})


def register_teacher(request):
    if request.method == 'POST':
        form = TeacherRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('approval_pending')
    else:
        form = TeacherRegisterForm()
    return render(request, 'users/register_teacher.html', {'form': form})

@student_required
def student_dashboard(request):
    profile = request.user.studentprofile
    if not profile.is_approved:
        return redirect('approval_pending')
    return render(request, 'dashboards/student.html')

@teacher_required
def teacher_dashboard(request):
    profile = request.user.teacherprofile
    if not profile.is_approved:
        return redirect('approval_pending')
    return render(request, 'dashboards/teacher.html')


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
                        return redirect('approval_pending')
                    return redirect('student_dashboard')
                except StudentProfile.DoesNotExist:
                    return redirect('approval_pending')
            elif user.is_teacher:
                try:
                    profile = TeacherProfile.objects.get(user=user)
                    if not profile.is_approved:
                        return redirect('approval_pending')
                    return redirect('teacher_dashboard')
                except TeacherProfile.DoesNotExist:
                    return redirect('approval_pending')
            else:
                return redirect('home')  # or some fallback
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if user.is_teacher:
                profile = user.teacherprofile
                if not profile.is_approved:
                    return redirect('approval_pending')
                return redirect('teacher_dashboard')

            elif user.is_student:
                profile = user.studentprofile
                if not profile.is_approved:
                    return redirect('approval_pending')
                return redirect('student_dashboard')

            else:
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})
