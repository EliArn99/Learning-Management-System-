from courses.models import Course
from assignments.models import Submission
from users.models import StudentProfile
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from courses.models import Course
from assignments.models import Assignment
from quizz.models import Quiz, Submission 


def home(request):
    return render(request, 'dashboards/home.html')

def about(request):
    return render(request, 'dashboards/about.html')

def contacts(request):
    return render(request, 'dashboards/contacts.html')


def dashboard_home_view(request):
    return render(request, 'dashboards/dashboard_home.html')


@login_required
def teacher_dashboard_view(request):
    teacher = request.user.teacherprofile
    courses = Course.objects.filter(teacher=teacher)

    total_students = StudentProfile.objects.filter(
        enrollment__course__in=courses
    ).distinct().count()

    assignments = Assignment.objects.filter(course__in=courses)
    submissions = Submission.objects.filter(assignment__in=assignments)

    total_submissions = submissions.count()
    graded_submissions = submissions.filter(grade__isnull=False).count()

    recent_submissions = submissions.order_by('-submitted_at')[:5]

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
        'total_students': total_students,
    })



@login_required
def student_dashboard_view(request):
    current_user = request.user 
    student_profile = current_user.studentprofile 

    courses = Course.objects.filter(enrollments__student=student_profile).distinct()

    all_assignments = Assignment.objects.filter(course__in=courses)
    all_quizzes = Quiz.objects.filter(course__in=courses)

    now = timezone.now()

    upcoming_assignments_queryset = all_assignments.filter(
        due_date__gt=now
    )

    upcoming_quizzes_queryset = all_quizzes.filter(
        available_until__gt=now
    ).exclude(submissions__student=current_user) 

    combined_upcoming_items = []

    for assignment in upcoming_assignments_queryset:
        combined_upcoming_items.append({
            'type': 'assignment',
            'pk': assignment.pk,
            'title': assignment.title,
            'due_date': assignment.due_date,
            'is_urgent': (assignment.due_date - now).days < 3
        })

    for quiz in upcoming_quizzes_queryset:
        combined_upcoming_items.append({
            'type': 'quiz',
            'pk': quiz.pk,
            'title': quiz.title,
            'due_date': quiz.available_until,
            'is_urgent': (quiz.available_until - now).days < 3
        })

    upcoming_items_sorted = sorted(combined_upcoming_items, key=lambda x: x['due_date'])

    total_quizzes = all_quizzes.count()
    submitted_quizzes = Submission.objects.filter(student=current_user, quiz__in=all_quizzes).count() 

    quiz_progress = int((submitted_quizzes / total_quizzes) * 100) if total_quizzes else 0

    context = {
        'courses': courses,
        'upcoming_assignments': upcoming_items_sorted[:5],
        'progress': quiz_progress,
    }
    return render(request, 'dashboards/student_dashboard.html', context)
