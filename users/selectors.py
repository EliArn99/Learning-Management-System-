import logging

from quizz.models import Quiz

logger = logging.getLogger(__name__)


def get_upcoming_quizzes_for_student(user):
    try:
        return Quiz.objects.filter(
            course__students=user,
            is_active=True,
        )
    except Exception:
        logger.exception("Failed to fetch upcoming quizzes for student.")
        return []