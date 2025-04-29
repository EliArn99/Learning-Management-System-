from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from courses.models import Course
from assignments.models import Assignment, Submission


def home(request):
    return render(request, 'dashboards/home.html')


def dashboard_home_view(request):
    return render(request, 'dashboards/dashboard_home.html')


@login_required
def teacher_dashboard_view(request):
    teacher = request.user.teacherprofile
    courses = Course.objects.filter(teacher=teacher)
    submissions = Submission.objects.filter(assignment__course__in=courses)

    return render(request, 'dashboards/teacher_dashboard.html', {
        'courses': courses,
        'submissions': submissions,
    })


@login_required
def student_dashboard_view(request):
    student = request.user.studentprofile
    courses = Course.objects.filter(students=student)
    assignments = Assignment.objects.filter(course__in=courses)

    return render(request, 'dashboards/student_dashboard.html', {
        'courses': courses,
        'assignments': assignments,
    })
