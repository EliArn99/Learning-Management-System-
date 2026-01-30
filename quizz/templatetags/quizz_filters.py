from django import template

register = template.Library()


def _selected_answer_id_set(student_answers):
    """
    Returns a cached set of selected_answer IDs for fast membership checks.
    Works with both QuerySets and plain lists.
    """
    if not student_answers:
        return set()

    # Cache on the object to avoid recomputing in templates
    cached = getattr(student_answers, "_selected_answer_ids_cache", None)
    if cached is not None:
        return cached

    ids = set()
    try:
        # If QuerySet: pull only needed field(s) from DB
        for sid in student_answers.values_list("selected_answer_id", flat=True):
            if sid:
                ids.add(sid)
    except Exception:
        # If it's a list/iterable of StudentAnswer objects
        for sa in student_answers:
            if getattr(sa, "selected_answer_id", None):
                ids.add(sa.selected_answer_id)

    setattr(student_answers, "_selected_answer_ids_cache", ids)
    return ids


@register.filter
def filter_selected(student_answers, answer_id):
    """
    Returns True if the answer_id exists in student's selected answers.
    Optimized to avoid O(n) scan per call.
    """
    if not answer_id:
        return False
    return int(answer_id) in _selected_answer_id_set(student_answers)


@register.filter
def get_student_answer_for_question(student_answers, question_id):
    """
    Returns the first StudentAnswer matching question_id, or None.
    Adds safe guards and small optimization for QuerySets.
    """
    if not student_answers or not question_id:
        return None

    try:
        # If QuerySet: filter in DB
        return student_answers.filter(question_id=question_id).first()
    except Exception:
        # If list/iterable: scan
        for sa in student_answers:
            if getattr(sa, "question_id", None) == question_id:
                return sa
        return None
