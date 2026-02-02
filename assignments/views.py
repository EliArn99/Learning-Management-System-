from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from courses.models import Course, Enrollment

from .models import Assignment, Submission
from .forms import AssignmentForm, AssignmentSubmissionForm, GradeSubmissionForm


def require_student(user):
    if not hasattr(user, "studentprofile"):
        raise PermissionDenied("Само студенти имат достъп до тази страница.")
    return user.studentprofile


def require_teacher(user):
    if not hasattr(user, "teacherprofile"):
        raise PermissionDenied("Само преподаватели имат достъп до тази страница.")
    return user.teacherprofile


def student_has_paid_enrollment(student_profile, course):
    return Enrollment.objects.filter(student=student_profile, course=course, is_paid=True).exists()


@login_required
def assignment_list_view(request):
    if hasattr(request.user, "studentprofile"):
        sp = request.user.studentprofile
        courses = Course.objects.filter(enrollments__student=sp, enrollments__is_paid=True).distinct()
        assignments = Assignment.objects.filter(course__in=courses).select_related("course").order_by("due_date")
    elif hasattr(request.user, "teacherprofile"):
        tp = request.user.teacherprofile
        assignments = Assignment.objects.filter(course__teacher=tp).select_related("course").order_by("due_date")
    else:
        assignments = Assignment.objects.none()

    return render(request, "assignments/assignment_list.html", {"assignments": assignments})


@login_required
def my_assignments_view(request):
    student_profile = require_student(request.user)

    my_courses = Course.objects.filter(enrollments__student=student_profile, enrollments__is_paid=True).distinct()
    assignments = Assignment.objects.filter(course__in=my_courses).select_related("course").order_by("due_date")

    # reduce queries: preload submissions
    submissions = Submission.objects.filter(student=student_profile, assignment__in=assignments).select_related("assignment")
    submission_map = {s.assignment_id: s for s in submissions}

    assignments_with_status = [{"assignment": a, "submission": submission_map.get(a.id)} for a in assignments]

    return render(request, "assignments/my_assignments.html", {"assignments_with_status": assignments_with_status})


@login_required
def assignment_detail_view(request, pk):
    assignment = get_object_or_404(Assignment.objects.select_related("course"), pk=pk)

    context = {"assignment": assignment, "submission": None, "submissions": None}

    # Student view: show only their submission
    if hasattr(request.user, "studentprofile"):
        student_profile = request.user.studentprofile

        if not student_has_paid_enrollment(student_profile, assignment.course):
            raise PermissionDenied("Нямате достъп до това задание (не сте записан/нямате платен достъп).")

        submission = Submission.objects.filter(student=student_profile, assignment=assignment).first()
        context["submission"] = submission

    # Teacher view: show submissions for own course only
    elif hasattr(request.user, "teacherprofile"):
        teacher = request.user.teacherprofile
        if assignment.course.teacher != teacher:
            raise PermissionDenied("Нямате достъп до задания за чужд курс.")

        submissions = (
            Submission.objects.filter(assignment=assignment)
            .select_related("student__user")
            .order_by("-submitted_at")
        )
        context["submissions"] = submissions

    return render(request, "assignments/assignment_detail.html", context)


@login_required
def submit_assignment_view(request, assignment_id):
    assignment = get_object_or_404(Assignment.objects.select_related("course"), id=assignment_id)
    student_profile = require_student(request.user)

    if not student_has_paid_enrollment(student_profile, assignment.course):
        raise PermissionDenied("Нямате достъп до това задание (не сте записан/нямате платен достъп).")

    submission = Submission.objects.filter(assignment=assignment, student=student_profile).first()

    if request.method == "POST":
        form = AssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.assignment = assignment
            sub.student = student_profile
            sub.save()
            messages.success(request, "Успешно изпратихте решението.")
            return redirect("assignments:assignment_detail", pk=assignment.id)
    else:
        form = AssignmentSubmissionForm(instance=submission)

    return render(request, "assignments/submit_assignment.html", {
        "assignment": assignment,
        "form": form,
        "submission": submission,
    })


@login_required
def edit_submission_view(request, submission_id):
    student_profile = require_student(request.user)
    submission = get_object_or_404(Submission.objects.select_related("assignment__course", "student__user"), id=submission_id,)

    if submission.student != student_profile:
        raise PermissionDenied("Нямате право да редактирате това решение.")

    if not student_has_paid_enrollment(student_profile, submission.assignment.course):
        raise PermissionDenied("Нямате достъп до този курс/задание.")

    if request.method == "POST":
        form = AssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            form.save()
            messages.success(request, "Успешно редактирахте решението.")
            return redirect("assignments:assignment_detail", pk=submission.assignment.id)
    else:
        form = AssignmentSubmissionForm(instance=submission)

    return render(request, "assignments/edit_submission.html", {"form": form, "submission": submission})


@login_required
def teacher_submissions_view(request):
    teacher = require_teacher(request.user)

    submissions = (
        Submission.objects.filter(assignment__course__teacher=teacher)
        .select_related("assignment", "assignment__course", "student__user")
        .order_by("-submitted_at")
    )

    status_filter = request.GET.get("status")
    if status_filter == "pending":
        submissions = submissions.filter(grade__isnull=True)
    elif status_filter == "graded":
        submissions = submissions.filter(grade__isnull=False)

    return render(request, "assignments/teacher_submissions.html", {
        "submissions": submissions,
        "current_status_filter": status_filter
    })


@login_required
def grade_submission_view(request, submission_id):
    teacher = require_teacher(request.user)

    submission = get_object_or_404(
        Submission.objects.select_related("assignment__course", "student__user"),
        id=submission_id,
    )

    if submission.assignment.course.teacher != teacher:
        raise PermissionDenied("Нямате право да оценявате решения за чужд курс.")

    if request.method == "POST":
        form = GradeSubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            graded_submission = form.save(commit=False)
            graded_submission.graded_at = timezone.now()
            graded_submission.save()

            student_email = submission.student.user.email
            if student_email:
                send_mail(
                    "Your Assignment Has Been Graded",
                    f'Hello {submission.student.user.username},\n\n'
                    f'Your submission for "{submission.assignment.title}" has been graded. '
                    f"You received a {graded_submission.grade}.\n\n"
                    f"Feedback: {graded_submission.feedback}",
                    "no-reply@yourplatform.com",
                    [student_email],
                    fail_silently=True,
                )

            messages.success(request, "Оценката е записана.")
            return redirect("assignments:teacher_submissions")
    else:
        form = GradeSubmissionForm(instance=submission)

    return render(request, "assignments/grade_submission.html", {"form": form, "submission": submission})


@login_required
def create_assignment_view(request):
    teacher = require_teacher(request.user)

    if request.method == "POST":
        form = AssignmentForm(request.POST, teacher_profile=teacher)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.save()
            messages.success(request, "Успешно създадохте ново задание.")
            return redirect("assignments:assignment_list")
        messages.error(request, "Възникна грешка при създаването на заданието. Проверете данните.")
    else:
        form = AssignmentForm(teacher_profile=teacher)

    return render(request, "assignments/create_assignment.html", {"form": form})
