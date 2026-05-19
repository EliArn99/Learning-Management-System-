from courses.models import Course, Enrollment

from .models import Assignment, Submission


def student_paid_courses(student_profile):
    return Course.objects.filter(
        enrollments__student=student_profile,
        enrollments__is_paid=True,
    ).distinct()


def student_assignments(student_profile):
    return Assignment.objects.filter(
        course__in=student_paid_courses(student_profile),
    ).select_related("course").order_by("due_date")


def teacher_assignments(teacher_profile):
    return Assignment.objects.filter(
        course__teacher=teacher_profile,
    ).select_related("course").order_by("due_date")


def student_submission_for_assignment(student_profile, assignment):
    return Submission.objects.filter(
        student=student_profile,
        assignment=assignment,
    ).first()


def student_submissions_for_assignments(student_profile, assignments):
    return Submission.objects.filter(
        student=student_profile,
        assignment__in=assignments,
    ).select_related("assignment")


def teacher_submissions(teacher_profile):
    return (
        Submission.objects.filter(assignment__course__teacher=teacher_profile)
        .select_related("assignment", "assignment__course", "student__user")
        .order_by("-submitted_at")
    )


def assignment_submissions(assignment):
    return (
        Submission.objects.filter(assignment=assignment)
        .select_related("student__user")
        .order_by("-submitted_at")
    )


def student_has_paid_enrollment(student_profile, course) -> bool:
    return Enrollment.objects.filter(
        student=student_profile,
        course=course,
        is_paid=True,
    ).exists()