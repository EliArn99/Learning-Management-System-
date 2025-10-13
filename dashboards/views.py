# TODO: Да оправя имейлите между студент и преподавател и да подобря изледа така че да показва че има съобщение при студента и да могат до отговарят
from users.models import StudentProfile, TeacherProfile # Make sure TeacherProfile is imported
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from assignments.models import Submission as AssignmentSubmission, Assignment
from quizz.models import Quiz, Submission as QuizSubmission

from courses.models import Course
from messaging.models import Message

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
    teacher_profile = request.user.teacherprofile # Renamed for clarity to avoid conflict with `teacher` in context
    courses = Course.objects.filter(teacher=teacher_profile)

    total_students = StudentProfile.objects.filter(
        enrollment__course__in=courses
    ).distinct().count()

    assignments = Assignment.objects.filter(course__in=courses)
    assignment_submissions = AssignmentSubmission.objects.filter(assignment__in=assignments)

    total_submissions = assignment_submissions.count()
    graded_submissions = assignment_submissions.filter(grade__isnull=False).count()

    # recent_submissions = assignment_submissions.order_by('-submitted_at')[:5]
    recent_submissions = assignment_submissions.order_by('-submitted_at')[:5].select_related(
        'student__user',
        'assignment',
    )

    selected_course_id = request.GET.get("course")
    if selected_course_id:
        assignment_submissions = assignment_submissions.filter(assignment__course__id=selected_course_id)

    # --- Messaging Integration ---
    # Fetch unread messages for the current teacher
    # Order by timestamp descending and get the latest 5
    unread_messages = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).select_related(
        'sender'
    ).prefetch_related(
        'sender__studentprofile', # Prefetch student profile for sender
        'sender__teacherprofile'  # Prefetch teacher profile for sender
    ).order_by('-timestamp')[:5]
    # --- End Messaging Integration ---

    return render(request, 'dashboards/teacher_dashboard.html', {
        'courses': courses,
        'assignments': assignments,
        'submissions': assignment_submissions,
        'recent_submissions': recent_submissions,
        'total_submissions': total_submissions,
        'graded_submissions': graded_submissions,
        'selected_course_id': selected_course_id,
        'total_students': total_students,
        'unread_messages': unread_messages, # Add unread messages to the context
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
    submitted_quizzes = QuizSubmission.objects.filter(student=current_user, quiz__in=all_quizzes).count()

    quiz_progress = int((submitted_quizzes / total_quizzes) * 100) if total_quizzes else 0

    context = {
        'courses': courses,
        'upcoming_assignments': upcoming_items_sorted[:5],
        'progress': quiz_progress,
    }
    return render(request, 'dashboards/student_dashboard.html', context)
