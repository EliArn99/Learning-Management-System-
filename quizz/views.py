import json
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden, JsonResponse
from .models import Quiz, Answer, Submission, StudentAnswer, Question
from .forms import QuizForm, QuestionForm, AnswerForm
from django.forms import inlineformset_factory
from django.db import transaction
from django.db.models import Prefetch
from django.core.exceptions import PermissionDenied



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

# ... AnswerFormSet остава същият ...
AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    form=AnswerForm,
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True,
)



class QuizManageListView(TeacherRequiredMixin, ListView):
    model = Quiz
    template_name = 'quiz/quiz_manage_list.html'
    context_object_name = 'quizzes'

    def get_queryset(self):
        # Връща само тестовете, създадени от текущия учител
        return Quiz.objects.filter(created_by=self.request.user.teacherprofile).order_by('-id')



class QuizCreateView(TeacherRequiredMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'quiz/quiz_form.html'


    def form_valid(self, form):
        form.instance.created_by = self.request.user.teacherprofile
        return super().form_valid(form)

    def get_success_url(self):
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
        return Quiz.objects.filter(created_by=self.request.user.teacherprofile)

    def get_success_url(self):
        return reverse_lazy('quizz:quiz_manage_list')


class QuizDeleteView(TeacherRequiredMixin, DeleteView):
    model = Quiz
    template_name = 'quiz/quiz_confirm_delete.html'  # Трябва да създадете този шаблон
    success_url = reverse_lazy('quizz:quiz_manage_list')

    def get_queryset(self):
        return Quiz.objects.filter(created_by=self.request.user.teacherprofile)



@transaction.atomic
def manage_questions_and_answers(request, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)

    if quiz.created_by != request.user.teacherprofile:
        raise PermissionDenied("Нямате право да редактирате този тест.")

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
    template_name = 'quiz/quiz_take.html' # <--- ДОБАВЕТЕ ТОВА!

    def post(self, request, *args, **kwargs):
        quiz = self.get_object()
        student = request.user


        session_key = f'quiz_{quiz.pk}_start_time'
        start_time_stamp = self.request.session.get(session_key)

        if start_time_stamp:
            start_time = timezone.datetime.fromtimestamp(start_time_stamp, tz=timezone.get_current_timezone())
            time_difference = timezone.now() - start_time
            if time_difference.total_seconds() > (quiz.time_limit * 60 + 5):
                del self.request.session[session_key]
                return JsonResponse({'error': 'Времето за теста изтече!'}, status=403)

        try:
            data = json.loads(request.body)
            user_answers_raw = data.get('userAnswers', [])
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Невалиден JSON формат.'}, status=400)

        submission = Submission.objects.create(quiz=quiz, student=student)
        if session_key in self.request.session:
            del self.request.session[session_key]

        total_points_earned = 0
        total_possible_points = 0

        questions_with_answers = Question.objects.filter(
            quiz=quiz
        ).prefetch_related(
            Prefetch('answers', queryset=Answer.objects.all(), to_attr='all_answers')
        ).order_by('id')

        question_map = {q.id: q for q in questions_with_answers}

        for ans_data in user_answers_raw:
            question_id = ans_data.get('questionId')
            selected_answer_ids = ans_data.get('selectedAnswerIds', [])
            text_answer = ans_data.get('textAnswer', '')

            question_obj = question_map.get(question_id)
            if not question_obj:
                continue

            total_possible_points += question_obj.points
            question_points_earned = 0

            if question_obj.type in ['MC', 'MM', 'TF']:
                correct_answer_ids = {a.id for a in question_obj.all_answers if a.is_correct}
                selected_ids = {id for id in selected_answer_ids if id is not None}

                if selected_ids == correct_answer_ids and correct_answer_ids:
                    question_points_earned = question_obj.points


                if selected_ids:
                    is_first_answer = True
                    for selected_id in selected_ids:
                        selected_answer_obj = next((a for a in question_obj.all_answers if a.id == selected_id), None)

                        if selected_answer_obj:
                            points_to_award = question_points_earned if is_first_answer else 0

                            StudentAnswer.objects.create(
                                submission=submission,
                                question=question_obj,
                                selected_answer=selected_answer_obj,
                                points_awarded=points_to_award  # Записва точките (само на първия)
                            )
                            is_first_answer = False
                else:
                    StudentAnswer.objects.create(
                        submission=submission,
                        question=question_obj,
                        selected_answer=None,
                        points_awarded=0
                    )

                total_points_earned += question_points_earned  # Добавяме общите точки за въпроса към резултата

            elif question_obj.type == 'OT':
                # Записваме свободния текст. Точките са 0 до ръчна оценка.
                StudentAnswer.objects.create(
                    submission=submission,
                    question=question_obj,
                    text_response=text_answer,
                    selected_answer=None,
                    points_awarded=0
                )

        if total_possible_points > 0:
            submission.score = round((total_points_earned / total_possible_points) * 100, 2)
        else:
            submission.score = 0

        submission.save()

        return JsonResponse({
            'message': 'Тестът е успешно изпратен!',
            'score': submission.score,
            'redirect_url': reverse_lazy('quizz:quiz_results', kwargs={'pk': quiz.pk})
        })


def quiz_results(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    submission = Submission.objects.filter(quiz=quiz, student=request.user).order_by('-submitted_at').first()
    if not submission:
        return HttpResponseForbidden("Нямате резултати за този тест.")
    return render(request, 'quiz/quiz_results.html', {
        'quiz': quiz,
        'submission': submission
    })

