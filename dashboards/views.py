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

    # Всички задания и предадени задания по тези курсове
    assignments = Assignment.objects.filter(course__in=courses)
    submissions = Submission.objects.filter(assignment__in=assignments)

    # Статистика
    total_submissions = submissions.count()
    graded_submissions = submissions.filter(grade__isnull=False).count()

    # Последни 5 предавания
    recent_submissions = submissions.order_by('-submitted_at')[:5]

    # Филтриране по курс (опционално)
    selected_course_id = request.GET.get("course")
    if selected_course_id:
        submissions = submissions.filter(assignment__course__id=selected_course_id)

    return render(request, 'dashboards/teacher_dashboard.html', {
        'courses': courses,
        'assignments': assignments,
        'submissions': submissions,
        'recent_submissions': recent_submissions,
        'total_submissions': total_submissions,
        'graded_submissions': graded_submissions,
        'selected_course_id': selected_course_id,
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
