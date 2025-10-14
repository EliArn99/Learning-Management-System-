from django import template

register = template.Library()


@register.filter
def filter_selected(student_answers, answer_id):
    if not student_answers:
        return False

    for student_answer in student_answers:
        if student_answer.selected_answer and student_answer.selected_answer.id == answer_id:
            return True
    return False


@register.filter
def get_student_answer_for_question(student_answers, question_id):
    for sa in student_answers:
        if sa.question.id == question_id:
            return sa
    return None