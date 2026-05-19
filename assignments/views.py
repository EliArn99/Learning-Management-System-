from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import student_required, teacher_required
from .forms import AssignmentForm, AssignmentSubmissionForm, GradeSubmissionForm
from .models import Assignment, Submission
from .selectors import (
    assignment_submissions,
    student_assignments,
    student_has_paid_enrollment,
    student_submission_for_assignment,
    student_submissions_for_assignments,
    teacher_assignments,
    teacher_submissions,
)
from .services import grade_submission, notify_student_submission_graded


@login_required
def assignment_list_view(request):
    if hasattr(request.user, "studentprofile"):
        assignments = student_assignments(request.user.studentprofile)

    elif hasattr(request.user, "teacherprofile"):
        assignments = teacher_assignments(request.user.teacherprofile)

    else:
        assignments = Assignment.objects.none()

    return render(
        request,
        "assignments/assignment_list.html",
        {
            "assignments": assignments,
        },
    )


@login_required
@student_required
def my_assignments_view(request):
    student_profile = request.user.studentprofile

    assignments = student_assignments(student_profile)
    submissions = student_submissions_for_assignments(
        student_profile,
        assignments,
    )

    submission_map = {
        submission.assignment_id: submission
        for submission in submissions
    }

    assignments_with_status = [
        {
            "assignment": assignment,
            "submission": submission_map.get(assignment.id),
        }
        for assignment in assignments
    ]

    return render(
        request,
        "assignments/my_assignments.html",
        {
            "assignments_with_status": assignments_with_status,
        },
    )


@login_required
def assignment_detail_view(request, pk):
    assignment = get_object_or_404(
        Assignment.objects.select_related("course", "course__teacher"),
        pk=pk,
    )

    context = {
        "assignment": assignment,
        "submission": None,
        "submissions": None,
    }

    if hasattr(request.user, "studentprofile"):
        student_profile = request.user.studentprofile

        if not student_has_paid_enrollment(student_profile, assignment.course):
            raise PermissionDenied(
                "Нямате достъп до това задание (не сте записан/нямате платен достъп)."
            )

        context["submission"] = student_submission_for_assignment(
            student_profile,
            assignment,
        )

    elif hasattr(request.user, "teacherprofile"):
        teacher_profile = request.user.teacherprofile

        if assignment.course.teacher != teacher_profile:
            raise PermissionDenied("Нямате достъп до задания за чужд курс.")

        context["submissions"] = assignment_submissions(assignment)

    else:
        raise PermissionDenied("Нямате достъп до тази страница.")

    return render(
        request,
        "assignments/assignment_detail.html",
        context,
    )


@login_required
@student_required
def submit_assignment_view(request, assignment_id):
    student_profile = request.user.studentprofile

    assignment = get_object_or_404(
        Assignment.objects.select_related("course"),
        id=assignment_id,
    )

    if not student_has_paid_enrollment(student_profile, assignment.course):
        raise PermissionDenied(
            "Нямате достъп до това задание (не сте записан/нямате платен достъп)."
        )

    submission = student_submission_for_assignment(
        student_profile,
        assignment,
    )

    if request.method == "POST":
        form = AssignmentSubmissionForm(
            request.POST,
            request.FILES,
            instance=submission,
        )

        if form.is_valid():
            submitted_assignment = form.save(commit=False)
            submitted_assignment.assignment = assignment
            submitted_assignment.student = student_profile
            submitted_assignment.save()

            messages.success(request, "Успешно изпратихте решението.")
            return redirect(
                "assignments:assignment_detail",
                pk=assignment.id,
            )

    else:
        form = AssignmentSubmissionForm(instance=submission)

    return render(
        request,
        "assignments/submit_assignment.html",
        {
            "assignment": assignment,
            "form": form,
            "submission": submission,
        },
    )


@login_required
@student_required
def edit_submission_view(request, submission_id):
    student_profile = request.user.studentprofile

    submission = get_object_or_404(
        Submission.objects.select_related(
            "assignment__course",
            "student__user",
        ),
        id=submission_id,
    )

    if submission.student != student_profile:
        raise PermissionDenied("Нямате право да редактирате това решение.")

    if not student_has_paid_enrollment(
        student_profile,
        submission.assignment.course,
    ):
        raise PermissionDenied("Нямате достъп до този курс/задание.")

    if request.method == "POST":
        form = AssignmentSubmissionForm(
            request.POST,
            request.FILES,
            instance=submission,
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Успешно редактирахте решението.")
            return redirect(
                "assignments:assignment_detail",
                pk=submission.assignment.id,
            )

    else:
        form = AssignmentSubmissionForm(instance=submission)

    return render(
        request,
        "assignments/edit_submission.html",
        {
            "form": form,
            "submission": submission,
        },
    )


@login_required
@teacher_required
def teacher_submissions_view(request):
    teacher_profile = request.user.teacherprofile

    submissions = teacher_submissions(teacher_profile)

    status_filter = request.GET.get("status")

    if status_filter == "pending":
        submissions = submissions.filter(grade__isnull=True)

    elif status_filter == "graded":
        submissions = submissions.filter(grade__isnull=False)

    return render(
        request,
        "assignments/teacher_submissions.html",
        {
            "submissions": submissions,
            "current_status_filter": status_filter,
        },
    )


@login_required
@teacher_required
def grade_submission_view(request, submission_id):
    teacher_profile = request.user.teacherprofile

    submission = get_object_or_404(
        Submission.objects.select_related(
            "assignment__course",
            "student__user",
        ),
        id=submission_id,
    )

    if submission.assignment.course.teacher != teacher_profile:
        raise PermissionDenied("Нямате право да оценявате решения за чужд курс.")

    if request.method == "POST":
        form = GradeSubmissionForm(
            request.POST,
            request.FILES,
            instance=submission,
        )

        if form.is_valid():
            graded_submission = grade_submission(
                submission=submission,
                grade=form.cleaned_data["grade"],
                feedback=form.cleaned_data.get("feedback", ""),
                graded_file=form.cleaned_data.get("graded_file"),
            )

            notify_student_submission_graded(graded_submission)

            messages.success(request, "Оценката е записана.")
            return redirect("assignments:teacher_submissions")

    else:
        form = GradeSubmissionForm(instance=submission)

    return render(
        request,
        "assignments/grade_submission.html",
        {
            "form": form,
            "submission": submission,
        },
    )


@login_required
@teacher_required
def create_assignment_view(request):
    teacher_profile = request.user.teacherprofile

    if request.method == "POST":
        form = AssignmentForm(
            request.POST,
            teacher_profile=teacher_profile,
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Успешно създадохте ново задание.")
            return redirect("assignments:assignment_list")

        messages.error(
            request,
            "Възникна грешка при създаването на заданието. Проверете данните.",
        )

    else:
        form = AssignmentForm(teacher_profile=teacher_profile)

    return render(
        request,
        "assignments/create_assignment.html",
        {
            "form": form,
        },
    )
