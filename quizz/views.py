import random
from courses.models import Enrollment
from .models import StudentQuizAttempt
from django.contrib.auth.decorators import login_required
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden, JsonResponse
from .models import Quiz, Answer, Submission, StudentAnswer, Question
from .forms import QuizForm, QuestionForm
from django.forms import inlineformset_factory
from django.db import transaction
from django.db.models import Prefetch
from django.core.exceptions import PermissionDenied

from .forms import AnswerForm, BaseAnswerFormSet


class TeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and hasattr(self.request.user, 'teacherprofile')

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
    template_name = 'quiz/quiz_manage_list.html'
    context_object_name = 'quizzes'

    def get_queryset(self):
        # Връща само тестовете, създадени от текущия учител
        return Quiz.objects.filter(created_by=self.request.user.teacherprofile).order_by('-id')


# quizz/views.py (само QuizCreateView)

class QuizCreateView(TeacherRequiredMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'quiz/quiz_form.html'

    # НЕ ДЕФИНИРАТЕ success_url ТУК.

    def form_valid(self, form):
        # 1. Задаваме създателя на теста
        form.instance.created_by = self.request.user.teacherprofile

        # 2. Връщаме резултата от super().form_valid(form)
        # Това запазва обекта и задава self.object.
        # След това автоматично се извиква get_success_url().
        return super().form_valid(form)

    # *** КЛЮЧОВА ПРОМЯНА: ДОБАВЯНЕ НА get_success_url ***
    def get_success_url(self):
        # Пренасочваме към управление на въпросите, използвайки ID-то на новосъздадения обект (self.object)
        # Използвайте reverse(), тъй като имате динамичен URL.
        return reverse('quizz:manage_q_a', kwargs={'quiz_pk': self.object.pk})

    def get_form(self):
        form = super().get_form()
        form.fields['course'].queryset = self.request.user.teacherprofile.taught_courses.all()
        return form


class QuizUpdateView(TeacherRequiredMixin, UpdateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'quiz/quiz_form.html'

    def get_queryset(self):
        # Проверява, че учителят може да редактира само собствените си тестове
        return Quiz.objects.filter(created_by=self.request.user.teacherprofile)

    def get_success_url(self):
        # След редактиране на основните полета, връщаме към списъка за управление
        return reverse_lazy('quizz:quiz_manage_list')


class QuizDeleteView(TeacherRequiredMixin, DeleteView):
    model = Quiz
    template_name = 'quiz/quiz_confirm_delete.html'  # Трябва да създадете този шаблон
    success_url = reverse_lazy('quizz:quiz_manage_list')

    def get_queryset(self):
        # Проверява, че учителят може да изтрива само собствените си тестове
        return Quiz.objects.filter(created_by=self.request.user.teacherprofile)


@login_required
@transaction.atomic
def manage_questions_and_answers(request, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    if not hasattr(request.user, "teacherprofile"):
        raise PermissionDenied("Нямате права на преподавател.")

    # Проверка за достъп (само създателят)
    if quiz.created_by != request.user.teacherprofile:
        raise PermissionDenied("Нямате право да редактирате този тест.")

    # 1. QUESTION FORMSET
    if request.method == 'POST' and 'questions-submit' in request.POST:
        q_formset = QuestionFormSet(request.POST, instance=quiz, prefix='question')
        if q_formset.is_valid():
            q_formset.save()
            return redirect('quizz:manage_q_a', quiz_pk=quiz.pk)
    else:
        q_formset = QuestionFormSet(instance=quiz, prefix='question')

    # 2. ANSWER FORMSETS (Динамично за всеки въпрос)
    question_forms_data = []
    for question in quiz.questions.all():
        # Проверка дали има POST заявка специално за отговорите на този въпрос
        if request.method == 'POST' and f'answers-submit-{question.pk}' in request.POST:
            a_formset = AnswerFormSet(request.POST, instance=question, prefix=f'answer-{question.pk}')
            if a_formset.is_valid():
                a_formset.save()
                return redirect('quizz:manage_q_a', quiz_pk=quiz.pk)
        else:
            a_formset = AnswerFormSet(instance=question, prefix=f'answer-{question.pk}')

        question_forms_data.append({
            'question': question,
            'answer_formset': a_formset
        })

    context = {
        'quiz': quiz,
        'q_formset': q_formset,
        'question_forms_data': question_forms_data,
    }
    return render(request, 'quiz/manage_questions_and_answers.html', context)


# --- СЪЩЕСТВУВАЩИ VIEWS (Студентски и Общи) ---

class QuizListView(ListView):
    model = Quiz
    template_name = 'quiz/quiz_list.html'
    context_object_name = 'quizzes'


class QuizDetailView(DetailView):
    model = Quiz
    template_name = 'quiz/quiz_detail.html'
    context_object_name = 'quiz'


class QuizTakeView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = "quiz/quiz_take.html"

    def _require_student_and_enrollment(self, quiz):
        user = self.request.user

        # Student role
        if not hasattr(user, "studentprofile"):
            raise PermissionDenied("Само студенти могат да решават тестове.")

        # Enrollment check (you can require is_paid=True if needed)
        is_enrolled = Enrollment.objects.filter(
            student=user.studentprofile,
            course=quiz.course,
            is_paid=True,  # ако искаш да е само за платени
        ).exists()

        if not is_enrolled:
            raise PermissionDenied("Нямате достъп до този тест (не сте записан/нямате платен достъп до курса).")

        # Active window
        if not quiz.is_active():
            raise PermissionDenied("Тестът не е активен в момента.")

    def _get_or_reset_attempt(self, quiz):
        attempt, _ = StudentQuizAttempt.objects.get_or_create(
            quiz=quiz,
            student=self.request.user,
            defaults={"start_time": timezone.now(), "is_complete": False, "selected_question_ids": []},
        )

        # If previously completed, reset for new attempt
        if attempt.is_complete:
            attempt.is_complete = False
            attempt.start_time = timezone.now()
            attempt.selected_question_ids = []
            attempt.save(update_fields=["is_complete", "start_time", "selected_question_ids"])

        return attempt

    def _select_questions_for_attempt(self, quiz, attempt):
        # Reuse stored selection if exists
        if attempt.selected_question_ids:
            ids = attempt.selected_question_ids
        else:
            all_ids = list(quiz.questions.values_list("id", flat=True).order_by("id"))
            n = quiz.num_questions_to_select or 0

            if n > 0 and n < len(all_ids):
                ids = random.sample(all_ids, n)
            else:
                ids = all_ids

            attempt.selected_question_ids = ids
            attempt.save(update_fields=["selected_question_ids"])

        # Fetch questions + answers and preserve selection order
        qs = Question.objects.filter(quiz=quiz, id__in=ids).prefetch_related(
            Prefetch("answers", queryset=Answer.objects.all(), to_attr="all_answers")
        )
        question_by_id = {q.id: q for q in qs}
        ordered_questions = [question_by_id[qid] for qid in ids if qid in question_by_id]
        return ordered_questions

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.get_object()

        self._require_student_and_enrollment(quiz)
        attempt = self._get_or_reset_attempt(quiz)
        questions = self._select_questions_for_attempt(quiz, attempt)

        context["attempt"] = attempt
        context["questions"] = questions
        context["time_limit_seconds"] = int((quiz.time_limit or 0) * 60)
        return context

    def post(self, request, *args, **kwargs):
        quiz = self.get_object()
        self._require_student_and_enrollment(quiz)

        attempt = self._get_or_reset_attempt(quiz)
        if not attempt.selected_question_ids:
            self._select_questions_for_attempt(quiz, attempt)

        allowed_ids = set(attempt.selected_question_ids or [])
        if not allowed_ids:
            return JsonResponse({"error": "Няма избрани въпроси за този тест."}, status=400)

        # Time limit enforcement
        if quiz.time_limit:
            elapsed = timezone.now() - attempt.start_time
            if elapsed.total_seconds() > (quiz.time_limit * 60):
                attempt.is_complete = True
                attempt.save(update_fields=["is_complete"])
                return JsonResponse({"error": "Времето за теста изтече!"}, status=403)

        # Parse JSON
        try:
            data = json.loads(request.body or "{}")
            user_answers_raw = data.get("userAnswers", [])
        except json.JSONDecodeError:
            return JsonResponse({"error": "Невалиден JSON формат."}, status=400)

        # Load selected questions with answers (only allowed)
        questions_with_answers = Question.objects.filter(
            quiz=quiz, id__in=allowed_ids
        ).prefetch_related(
            Prefetch("answers", queryset=Answer.objects.all(), to_attr="all_answers")
        ).order_by("id")

        question_map = {q.id: q for q in questions_with_answers}

        submission = Submission.objects.create(quiz=quiz, student=request.user)

        total_points_earned = 0
        total_possible_points = sum(q.points for q in questions_with_answers)

        for ans_data in user_answers_raw:
            question_id = ans_data.get("questionId")
            if question_id not in allowed_ids:
                # Prevent submitting answers for questions that were not shown
                continue

            selected_answer_ids = ans_data.get("selectedAnswerIds", [])
            text_answer = ans_data.get("textAnswer", "")

            question_obj = question_map.get(question_id)
            if not question_obj:
                continue

            question_points_earned = 0

            if question_obj.type in ["MC", "MM", "TF"]:
                correct_answer_ids = {a.id for a in question_obj.all_answers if a.is_correct}
                selected_ids = {i for i in selected_answer_ids if i is not None}

                if selected_ids == correct_answer_ids and correct_answer_ids:
                    question_points_earned = question_obj.points

                # Save selected answers (keep your current schema)
                if selected_ids:
                    is_first = True
                    for selected_id in selected_ids:
                        selected_obj = next((a for a in question_obj.all_answers if a.id == selected_id), None)
                        if selected_obj:
                            StudentAnswer.objects.create(
                                submission=submission,
                                question=question_obj,
                                selected_answer=selected_obj,
                                points_awarded=question_points_earned if is_first else 0,
                            )
                            is_first = False
                else:
                    StudentAnswer.objects.create(
                        submission=submission,
                        question=question_obj,
                        selected_answer=None,
                        points_awarded=0,
                    )

                total_points_earned += question_points_earned

            elif question_obj.type == "OT":
                StudentAnswer.objects.create(
                    submission=submission,
                    question=question_obj,
                    text_response=text_answer,
                    selected_answer=None,
                    points_awarded=0,
                )

        submission.score = round((total_points_earned / total_possible_points) * 100, 2) if total_possible_points else 0
        submission.save()

        attempt.is_complete = True
        attempt.save(update_fields=["is_complete"])

        return JsonResponse({
            "message": "Тестът е успешно изпратен!",
            "score": submission.score,
            "redirect_url": reverse("quizz:quiz_results", kwargs={"pk": quiz.pk}),
        })

@login_required
def quiz_results(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)

    # Student-only + enrollment check (същите правила като QuizTakeView)
    if not hasattr(request.user, "studentprofile"):
        raise PermissionDenied("Само студенти могат да виждат резултати.")

    is_enrolled = Enrollment.objects.filter(
        student=request.user.studentprofile,
        course=quiz.course,
        is_paid=True,
    ).exists()
    if not is_enrolled:
        raise PermissionDenied("Нямате достъп до резултатите за този тест.")

    submission = Submission.objects.filter(
        quiz=quiz,
        student=request.user
    ).order_by("-submitted_at").first()

    if not submission:
        return HttpResponseForbidden("Нямате резултати за този тест.")

    return render(request, "quiz/quiz_results.html", {"quiz": quiz, "submission": submission})
