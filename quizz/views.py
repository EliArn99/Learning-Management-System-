import json
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden, JsonResponse
from .models import Quiz, Answer, Submission, StudentAnswer, Question
from .forms import QuizForm, QuestionForm, AnswerForm
from django.forms import inlineformset_factory
from django.db import transaction
from django.db.models import Prefetch
from django.core.exceptions import PermissionDenied

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
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True,
)


class QuizQuestionsUpdateView(LoginRequiredMixin, UpdateView):
    model = Quiz
    template_name = 'quiz/quiz_add_question.html'
    context_object_name = 'quiz'
    fields = []

    def get_object(self, queryset=None):
        quiz = super().get_object(queryset)
        if self.request.user.teacherprofile != quiz.created_by:
            raise HttpResponseForbidden("Нямате право да редактирате този тест.")
        return quiz

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.get_object()

        if self.request.POST:
            context['question_formset'] = QuestionFormSet(self.request.POST, instance=quiz)
        else:
            context['question_formset'] = QuestionFormSet(instance=quiz)

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        quiz = self.object

        if self.request.user.teacherprofile != quiz.created_by:
            return HttpResponseForbidden("Нямате право да редактирате този тест.")

        formset = QuestionFormSet(request.POST, instance=quiz)

        if formset.is_valid():
            with transaction.atomic():
                formset.save()
            return redirect('quizz:quiz_detail', pk=quiz.pk)
        else:
            return self.render_to_response(self.get_context_data(question_formset=formset))


class QuestionUpdateView(LoginRequiredMixin, UpdateView):
    model = Question
    template_name = 'quiz/question_form.html'
    context_object_name = 'question'
    fields = ['text', 'points']

    def get_object(self, queryset=None):
        """Retrieve the question object and check permissions."""
        question = super().get_object(queryset)
        if self.request.user.teacherprofile != question.quiz.created_by:
            raise HttpResponseForbidden("Нямате право да редактирате този въпрос.")
        return question

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question = self.get_object()

        if self.request.POST:
            context['answer_formset'] = AnswerFormSet(self.request.POST, instance=question)
        else:
            context['answer_formset'] = AnswerFormSet(instance=question)
        return context

    def form_valid(self, form):
        with transaction.atomic():
            question = form.save()

            answer_formset = AnswerFormSet(self.request.POST, instance=question)
            if answer_formset.is_valid():
                answer_formset.save()
            else:
                return self.render_to_response(self.get_context_data(form=form, answer_formset=answer_formset))

            return redirect('quizz:quiz_detail', pk=question.quiz.pk)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class QuizListView(ListView):
    model = Quiz
    template_name = 'quiz/quiz_list.html'
    context_object_name = 'quizzes'


class QuizCreateView(LoginRequiredMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'quiz/quiz_form.html'
    success_url = reverse_lazy('quizz:quiz_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user.teacherprofile
        response = super().form_valid(form)
        return redirect('quizz:quiz_add_questions', pk=form.instance.pk)

    def get_form(self):
        form = super().get_form()
        form.fields['course'].queryset = self.request.user.teacherprofile.taught_courses.all()
        return form


class QuizDetailView(DetailView):
    model = Quiz
    template_name = 'quiz/quiz_detail.html'
    context_object_name = 'quiz'


class QuizTakeView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = 'quiz/quiz_take.html'
    context_object_name = 'quiz'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.get_object()

        if not quiz.is_active():
            raise PermissionDenied("Този тест не е активен в момента.")

        session_key = f'quiz_{quiz.pk}_start_time'
        if session_key not in self.request.session:
            self.request.session[session_key] = timezone.now().timestamp()

        context['time_limit'] = quiz.time_limit
        context['start_time'] = self.request.session[session_key]

        all_questions = quiz.questions.all().prefetch_related('answers')

        num_select = quiz.num_questions_to_select
        if num_select > 0 and num_select < all_questions.count():
            questions = all_questions.order_by('?')[:num_select]
        else:
            questions = all_questions.order_by('id')

        quiz_data = []
        for q_obj in questions:
            options_data = []
            if q_obj.type != 'OT':
                for a_obj in q_obj.answers.all().order_by('id'):
                    options_data.append({
                        'id': a_obj.id,
                        'text': a_obj.text
                    })

            quiz_data.append({
                'id': q_obj.id,
                'question': q_obj.text,
                'options': options_data,
                'type': q_obj.type,
            })

        context['quiz_data_json'] = json.dumps(quiz_data)
        return context

    def post(self, request, *args, **kwargs):
        quiz = self.get_object()
        student = request.user

        if not quiz.is_active():
            return JsonResponse({'error': 'Този тест не е активен.'}, status=403)

        session_key = f'quiz_{quiz.pk}_start_time'
        start_time_stamp = self.request.session.get(session_key)

        if start_time_stamp:
            start_time = timezone.datetime.fromtimestamp(start_time_stamp, tz=timezone.get_current_timezone())
            time_difference = timezone.now() - start_time
            if time_difference.total_seconds() > (quiz.time_limit * 60 + 5):  # Добавете толеранс от 5 секунди
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

        score = 0
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

                is_correct = False
                if selected_ids == correct_answer_ids and correct_answer_ids:
                    is_correct = True
                    question_points_earned = question_obj.points

                sa_instance = StudentAnswer.objects.create(
                    submission=submission,
                    question=question_obj,
                    text_response=f"Selected IDs: {selected_ids}",  
                    points_awarded=question_points_earned, 
                    selected_answer=None  
                )

                if selected_ids:

                    sa_instance.delete()

                    for selected_id in selected_ids:
                        selected_answer_obj = next((a for a in question_obj.all_answers if a.id == selected_id), None)
                        if selected_answer_obj:
                            StudentAnswer.objects.create(
                                submission=submission,
                                question=question_obj,
                                selected_answer=selected_answer_obj,  
                                points_awarded=question_points_earned if question_obj.type in ['MC',
                                                                                               'TF'] and is_correct else 0
                            )


                
                StudentAnswer.objects.filter(submission=submission, question=question_obj).delete()

                if selected_ids:
                    is_first_answer = True
                    for selected_id in selected_ids:
                        selected_answer_obj = next((a for a in question_obj.all_answers if a.id == selected_id), None)

                        if selected_answer_obj:
                            # Точките се записват САМО на първия SA запис, за да не се дублират.
                            points_to_award = question_points_earned if is_first_answer else 0

                            StudentAnswer.objects.create(
                                submission=submission,
                                question=question_obj,
                                selected_answer=selected_answer_obj,
                                points_awarded=points_to_award  
                            )
                            is_first_answer = False
                else:
                    StudentAnswer.objects.create(
                        submission=submission,
                        question=question_obj,
                        selected_answer=None,
                        points_awarded=0
                    )

                if is_correct:
                    total_points_earned += question_obj.points
                    score += 1

            elif question_obj.type == 'OT':
                StudentAnswer.objects.create(
                    submission=submission,
                    question=question_obj,
                    text_response=text_answer,
                    selected_answer=None,
                    points_awarded=0
                )
                pass

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


def quiz_form_view(request):
    form = QuizForm()
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user.teacherprofile
            quiz.save()
            return redirect('quizz:quiz_detail', pk=quiz.pk)
    return render(request, 'quiz/quiz_form.html', {'form': form})
