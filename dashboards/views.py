from datetime import timedelta

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from users.models import StudentProfile
from assignments.models import Submission as AssignmentSubmission, Assignment
from quizz.models import Quiz, Submission as QuizSubmission
from courses.models import Course, Enrollment
from messaging.models import Message


def require_student(user):
    if not hasattr(user, "studentprofile"):
        raise PermissionDenied("Само студенти имат достъп до тази страница.")
    return user.studentprofile


def require_teacher(user):
    if not hasattr(user, "teacherprofile"):
        raise PermissionDenied("Само преподаватели имат достъп до тази страница.")
    return user.teacherprofile


def home(request):
    return render(request, "dashboards/home.html")


def about(request):
    return render(request, "dashboards/about.html")


def contacts(request):
    return render(request, "dashboards/contacts.html")


def dashboard_home_view(request):
    return render(request, "dashboards/dashboard_home.html")


@login_required
def teacher_dashboard_view(request):
    teacher_profile = require_teacher(request.user)
    courses = Course.objects.filter(teacher=teacher_profile)

    total_students = StudentProfile.objects.filter(
        pk__in=Enrollment.objects.filter(course__in=courses, is_paid=True).values("student_id")
    ).distinct().count()

    assignments = Assignment.objects.filter(course__in=courses)

    submissions_qs = (
        AssignmentSubmission.objects.filter(assignment__in=assignments)
        .select_related("student__user", "assignment", "assignment__course")
        .order_by("-submitted_at")
    )

    selected_course_id = request.GET.get("course")
    if selected_course_id and courses.filter(id=selected_course_id).exists():
        submissions_qs = submissions_qs.filter(assignment__course__id=selected_course_id)
    else:
        selected_course_id = None

    total_submissions = submissions_qs.count()
    graded_submissions = submissions_qs.filter(grade__isnull=False).count()
    pending_submissions = submissions_qs.filter(grade__isnull=True).count()

    recent_submissions = submissions_qs[:5]

    unread_messages = (
        Message.objects.filter(receiver=request.user, is_read=False)
        .select_related("sender")
        .prefetch_related("sender__studentprofile", "sender__teacherprofile")
        .order_by("-timestamp")[:5]
    )

    return render(
        request,
        "dashboards/teacher_dashboard.html",
        {
            "courses": courses,
            "assignments": assignments,
            "submissions": submissions_qs,
            "recent_submissions": recent_submissions,
            "total_submissions": total_submissions,
            "graded_submissions": graded_submissions,
            "pending_submissions": pending_submissions,
            "selected_course_id": selected_course_id,
            "total_students": total_students,
            "unread_messages": unread_messages,
        },
    )


@login_required
def student_dashboard_view(request):
    student_profile = require_student(request.user)
    current_user = request.user
    now = timezone.now()

    courses = Course.objects.filter(enrollments__student=student_profile, enrollments__is_paid=True).distinct()

    all_assignments = Assignment.objects.filter(course__in=courses).select_related("course")
    all_quizzes = Quiz.objects.filter(course__in=courses).select_related("course")

    upcoming_assignments = all_assignments.filter(due_date__gt=now)

    upcoming_quizzes = (
        all_quizzes
        .filter(Q(available_from__isnull=True) | Q(available_from__lte=now))
        .filter(Q(available_until__isnull=True) | Q(available_until__gt=now))
        .exclude(submissions__student=current_user)
    )

    combined = [
        {
            "type": "assignment",
            "pk": a.pk,
            "title": a.title,
            "due_date": a.due_date,
            "is_urgent": (a.due_date - now).days < 3,
        }
        for a in upcoming_assignments
    ] + [
        {
            "type": "quiz",
            "pk": q.pk,
            "title": q.title,
            # Avoid None sorting issues if available_until is null
            "due_date": q.available_until or (now + timedelta(days=3650)),
            "is_urgent": bool(q.available_until and (q.available_until - now).days < 3),
        }
        for q in upcoming_quizzes
    ]

    combined_sorted = sorted(combined, key=lambda x: x["due_date"])

    total_quizzes = all_quizzes.count()
    submitted_quizzes = QuizSubmission.objects.filter(student=current_user, quiz__in=all_quizzes).count()
    quiz_progress = int((submitted_quizzes / total_quizzes) * 100) if total_quizzes else 0

    unread_messages = (
        Message.objects.filter(receiver=current_user, is_read=False)
        .select_related("sender")
        .prefetch_related("sender__teacherprofile", "sender__studentprofile")
        .order_by("-timestamp")[:5]
    )

    return render(
        request,
        "dashboards/student_dashboard.html",
        {
            "courses": courses,
            "upcoming_assignments": combined_sorted[:5],
            "progress": quiz_progress,
            "unread_messages": unread_messages,
        },
    )
