import logging

from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


def grade_submission(submission, grade, feedback="", graded_file=None):
    submission.grade = grade
    submission.feedback = feedback
    submission.graded_at = timezone.now()

    if graded_file:
        submission.graded_file = graded_file

    submission.save()

    return submission


def notify_student_submission_graded(submission):
    student_email = submission.student.user.email

    if not student_email:
        return False

    try:
        send_mail(
            "Your Assignment Has Been Graded",
            (
                f"Hello {submission.student.user.username},\n\n"
                f'Your submission for "{submission.assignment.title}" has been graded. '
                f"You received a {submission.grade}.\n\n"
                f"Feedback: {submission.feedback or 'No feedback provided.'}"
            ),
            "no-reply@yourplatform.com",
            [student_email],
            fail_silently=False,
        )
        return True

    except Exception:
        logger.exception("Failed to send graded assignment email.")
        return False