from django.utils import timezone

from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404

from assignments.models import Submission
from quizz.models import Quiz
from .decorators import student_required, teacher_required
from .forms import StudentRegisterForm, TeacherRegisterForm, StudentProfileForm, TeacherProfileForm
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
def profile_view(request):
    user = request.user

    if hasattr(user, 'studentprofile'):
        return render(request, 'users/student_profile.html', {'student': user.studentprofile})

    elif hasattr(user, 'teacherprofile'):
        return render(request, 'users/teacher_profile.html', {'teacher': user.teacherprofile})

    else:
        # Ако няма профил — върни грешка или пренасочи
        return redirect('home')


@login_required
def student_profile_view(request):
    profile, created = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = StudentRegisterForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('users:student_dashboard')
    else:
        form = StudentRegisterForm(instance=profile)

    return render(request, 'users/student_profile.html', {'form': form})


@login_required
def teacher_profile_view(request):
    profile, created = TeacherProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = TeacherRegisterForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('users:teacher_dashboard')
    else:
        form = TeacherRegisterForm(instance=profile)

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
            return redirect('users:approval_pending')
    else:
        form = StudentRegisterForm()
    return render(request, 'users/register_student.html', {'form': form})


def register_teacher(request):
    if request.method == 'POST':
        form = TeacherRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('users:approval_pending')
    else:
        form = TeacherRegisterForm()
    return render(request, 'users/register_teacher.html', {'form': form})


@student_required
def student_dashboard(request):
    profile = request.user.studentprofile
    if not profile.is_approved:
        return redirect('users:approval_pending')

    now = timezone.now()
    courses = profile.courses.all()
    upcoming_quizzes = Quiz.objects.filter(
        course__in=courses,
        available_from__lte=now,
        available_until__gte=now
    )
    return render(request, 'dashboards/student.html', {
        'upcoming_quizzes': upcoming_quizzes
    })


@teacher_required
def teacher_dashboard(request):
    profile = request.user.teacherprofile

    if not profile.is_approved:
        return redirect('users:approval_pending')

    # Предавания за курсовете на учителя
    total_submissions = Submission.objects.filter(quiz__course__teacher=profile).count()
    graded_submissions = Submission.objects.filter(quiz__course__teacher=profile, is_graded=True).count()
    pending_submissions = total_submissions - graded_submissions

    # Всички студенти, записани в курсовете на този учител
    total_students = StudentProfile.objects.filter(courses__in=profile.courses.all()).distinct().count()

    return render(request, 'dashboards/teacher.html', {
        'total_submissions': total_submissions,
        'graded_submissions': graded_submissions,
        'pending_submissions': pending_submissions,
        'total_students': total_students,
    })


def custom_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Пренасочване според ролята и одобрението
            if user.is_student:
                try:
                    profile = StudentProfile.objects.get(user=user)
                    if not profile.is_approved:
                        return redirect('users:approval_pending')
                    return redirect('dashboards:student_dashboard')
                except StudentProfile.DoesNotExist:
                    return redirect('users:approval_pending')

            elif user.is_teacher:
                try:
                    profile = TeacherProfile.objects.get(user=user)
                    if not profile.is_approved:
                        return redirect('users:approval_pending')
                    return redirect('dashboards:teacher_dashboard')
                except TeacherProfile.DoesNotExist:
                    return redirect('users:approval_pending')
            else:
                return redirect('home')
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
                    return redirect('users:approval_pending')
                return redirect('teacher_dashboard')

            elif user.is_student:
                profile = user.studentprofile
                if not profile.is_approved:
                    return redirect('users:approval_pending')
                return redirect('student_dashboard')

            else:
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})


def custom_logout_view(request):
    logout(request)
    return render(request, 'users/logout.html')


@login_required
def edit_profile_view(request):
    user = request.user

    if hasattr(user, 'studentprofile'):
        profile = user.studentprofile
        form_class = StudentProfileForm
    elif hasattr(user, 'teacherprofile'):
        profile = user.teacherprofile
        form_class = TeacherProfileForm
    else:
        return redirect('users:profile')  # fallback

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('users:profile')
    else:
        form = form_class(instance=profile)

    return render(request, 'users/edit_profile.html', {'form': form})



# views.py
@teacher_required
def grade_submission_view(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    if request.method == 'POST':
        form = SubmissionGradeForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.is_graded = True
            submission.save()
            return redirect('teacher_dashboard')
    else:
        form = SubmissionGradeForm(instance=submission)

    return render(request, 'grading/grade_submission.html', {
        'submission': submission,
        'form': form
    })
