import json

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import AnswerForm, BaseAnswerFormSet, QuestionForm, QuizForm
from .models import Answer, Question, Quiz
from .selectors import (
    all_quizzes,
    get_quiz_for_teacher_or_404_queryset,
    latest_submission_for_student,
    quiz_with_questions_and_answers,
    quizzes_for_teacher,
    student_has_paid_enrollment,
)
from .services import (
    complete_attempt,
    get_or_reset_attempt,
    process_quiz_submission,
    quiz_time_expired,
    select_questions_for_attempt,
)


class TeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return (
            self.request.user.is_authenticated
            and hasattr(self.request.user, "teacherprofile")
        )

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Нямате права на преподавател за тази операция.")
        return super().handle_no_permission()


QuestionFormSet = inlineformset_factory(
    Quiz,
    Question,
    form=QuestionForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)

AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    form=AnswerForm,
    formset=BaseAnswerFormSet,
    extra=4,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class QuizManageListView(TeacherRequiredMixin, ListView):
    model = Quiz
    template_name = "quiz/quiz_manage_list.html"
    context_object_name = "quizzes"
    paginate_by = 10

    def get_queryset(self):
        return quizzes_for_teacher(self.request.user.teacherprofile)


class QuizCreateView(TeacherRequiredMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = "quiz/quiz_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user.teacherprofile
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("quizz:manage_q_a", kwargs={"quiz_pk": self.object.pk})

    def get_form(self):
        form = super().get_form()
        form.fields["course"].queryset = self.request.user.teacherprofile.taught_courses.all()
        return form


class QuizUpdateView(TeacherRequiredMixin, UpdateView):
    model = Quiz
    form_class = QuizForm
    template_name = "quiz/quiz_form.html"

    def get_queryset(self):
        return get_quiz_for_teacher_or_404_queryset(
            self.request.user.teacherprofile,
        )

    def get_success_url(self):
        return reverse_lazy("quizz:quiz_manage_list")

    def get_form(self):
        form = super().get_form()
        form.fields["course"].queryset = self.request.user.teacherprofile.taught_courses.all()
        return form


class QuizDeleteView(TeacherRequiredMixin, DeleteView):
    model = Quiz
    template_name = "quiz/quiz_confirm_delete.html"
    success_url = reverse_lazy("quizz:quiz_manage_list")

    def get_queryset(self):
        return get_quiz_for_teacher_or_404_queryset(
            self.request.user.teacherprofile,
        )


@login_required
@transaction.atomic
def manage_questions_and_answers(request, quiz_pk):
    if not hasattr(request.user, "teacherprofile"):
        raise PermissionDenied("Нямате права на преподавател.")

    quiz = get_object_or_404(
        get_quiz_for_teacher_or_404_queryset(request.user.teacherprofile),
        pk=quiz_pk,
    )

    if request.method == "POST" and "questions-submit" in request.POST:
        question_formset = QuestionFormSet(
            request.POST,
            instance=quiz,
            prefix="question",
        )

        if question_formset.is_valid():
            question_formset.save()
            return redirect("quizz:manage_q_a", quiz_pk=quiz.pk)
    else:
        question_formset = QuestionFormSet(
            instance=quiz,
            prefix="question",
        )

    question_forms_data = []

    for question in quiz.questions.all():
        if request.method == "POST" and f"answers-submit-{question.pk}" in request.POST:
            answer_formset = AnswerFormSet(
                request.POST,
                instance=question,
                prefix=f"answer-{question.pk}",
            )

            if answer_formset.is_valid():
                answer_formset.save()
                return redirect("quizz:manage_q_a", quiz_pk=quiz.pk)
        else:
            answer_formset = AnswerFormSet(
                instance=question,
                prefix=f"answer-{question.pk}",
            )

        question_forms_data.append(
            {
                "question": question,
                "answer_formset": answer_formset,
            }
        )

    return render(
        request,
        "quiz/manage_questions_and_answers.html",
        {
            "quiz": quiz,
            "q_formset": question_formset,
            "question_forms_data": question_forms_data,
        },
    )


class QuizListView(ListView):
    model = Quiz
    template_name = "quiz/quiz_list.html"
    context_object_name = "quizzes"
    paginate_by = 10

    def get_queryset(self):
        return all_quizzes()


class QuizDetailView(DetailView):
    model = Quiz
    template_name = "quiz/quiz_detail.html"
    context_object_name = "quiz"

    def get_queryset(self):
        return all_quizzes()


class QuizTakeView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = "quiz/quiz_take.html"

    def get_queryset(self):
        return quiz_with_questions_and_answers()

    def _require_student_access(self, quiz):
        user = self.request.user

        if not hasattr(user, "studentprofile"):
            raise PermissionDenied("Само студенти могат да решават тестове.")

        if not student_has_paid_enrollment(user.studentprofile, quiz.course):
            raise PermissionDenied(
                "Нямате достъп до този тест."
            )

        if not quiz.is_active():
            raise PermissionDenied("Тестът не е активен в момента.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        quiz = self.get_object()
        self._require_student_access(quiz)

        attempt = get_or_reset_attempt(
            quiz,
            self.request.user,
        )
        questions = select_questions_for_attempt(
            quiz,
            attempt,
        )

        context["attempt"] = attempt
        context["questions"] = questions
        context["time_limit_seconds"] = int((quiz.time_limit or 0) * 60)

        return context

    def post(self, request, *args, **kwargs):
        quiz = self.get_object()
        self._require_student_access(quiz)

        attempt = get_or_reset_attempt(
            quiz,
            request.user,
        )

        if not attempt.selected_question_ids:
            select_questions_for_attempt(
                quiz,
                attempt,
            )

        if not attempt.selected_question_ids:
            return JsonResponse(
                {"error": "Няма избрани въпроси за този тест."},
                status=400,
            )

        if quiz_time_expired(quiz, attempt):
            complete_attempt(attempt)
            return JsonResponse(
                {"error": "Времето за теста изтече!"},
                status=403,
            )

        try:
            data = json.loads(request.body or "{}")
            user_answers_raw = data.get("userAnswers", [])
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Невалиден JSON формат."},
                status=400,
            )

        submission = process_quiz_submission(
            quiz=quiz,
            student_user=request.user,
            attempt=attempt,
            user_answers_raw=user_answers_raw,
        )

        return JsonResponse(
            {
                "message": "Тестът е успешно изпратен!",
                "score": submission.score,
                "redirect_url": reverse(
                    "quizz:quiz_results",
                    kwargs={"pk": quiz.pk},
                ),
            }
        )


@login_required
def quiz_results(request, pk):
    quiz = get_object_or_404(
        Quiz.objects.select_related("course"),
        pk=pk,
    )

    if not hasattr(request.user, "studentprofile"):
        raise PermissionDenied("Само студенти могат да виждат резултати.")

    if not student_has_paid_enrollment(request.user.studentprofile, quiz.course):
        raise PermissionDenied("Нямате достъп до резултатите за този тест.")

    submission = latest_submission_for_student(
        quiz,
        request.user,
    )

    if not submission:
        return HttpResponseForbidden("Нямате резултати за този тест.")

    return render(
        request,
        "quiz/quiz_results.html",
        {
            "quiz": quiz,
            "submission": submission,
        },
    )
