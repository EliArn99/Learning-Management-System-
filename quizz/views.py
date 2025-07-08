import json

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from .models import Quiz, Answer, Submission, StudentAnswer, Question
from .forms import QuizForm, QuestionForm, AnswerForm
from django.forms import inlineformset_factory
from django.db import transaction
from django.db.models import Prefetch # Import Prefetch for optimized queries

# Formset за въпроси към тест
QuestionFormSet = inlineformset_factory(
    Quiz,
    Question,
    form=QuestionForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)

# Formset за отговори към въпрос
AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    form=AnswerForm,
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True,
)


# ✅ CBV за добавяне/редактиране на въпроси към тест
class QuizQuestionsUpdateView(LoginRequiredMixin, UpdateView):
    model = Quiz
    template_name = 'quiz/quiz_add_question.html'
    context_object_name = 'quiz'
    fields = []

    def get_object(self, queryset=None):
        """Retrieve the quiz object and check permissions."""
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
        """Called when the question form is valid."""
        with transaction.atomic():
            question = form.save()

            answer_formset = AnswerFormSet(self.request.POST, instance=question)
            if answer_formset.is_valid():
                answer_formset.save()
            else:
                return self.render_to_response(self.get_context_data(form=form, answer_formset=answer_formset))

            return redirect('quizz:quiz_detail', pk=question.quiz.pk)

    def form_invalid(self, form):
        """Called when the question form is invalid."""
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
            raise HttpResponseForbidden("Този тест не е активен в момента.")

        # Prepare quiz data for JavaScript without sending correct answers
        quiz_data = []
        # Optimize query: prefetch questions and their answers
        questions = quiz.questions.all().order_by('id').prefetch_related('answers')

        for q_obj in questions:
            options_data = []
            for a_obj in q_obj.answers.all().order_by('id'):
                options_data.append({
                    'id': a_obj.id,
                    'text': a_obj.text
                })
            quiz_data.append({
                'id': q_obj.id,
                'question': q_obj.text,
                'options': options_data,
                # IMPORTANT: 'correct_index' is REMOVED for security!
            })

        context['quiz_data_json'] = json.dumps(quiz_data)
        return context

    def post(self, request, *args, **kwargs):
        quiz = self.get_object()
        student = request.user

        if not quiz.is_active():
            return JsonResponse({'error': 'Този тест не е активен.'}, status=403)

        # Allow multiple submissions if needed, otherwise keep this check
        if Submission.objects.filter(quiz=quiz, student=student).exists():
            return JsonResponse({'error': 'Вече сте изпълнили този тест.'}, status=403)

        try:
            data = json.loads(request.body)
            user_answers_raw = data.get('userAnswers', [])
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Невалиден JSON формат.'}, status=400)

        submission = Submission.objects.create(quiz=quiz, student=student)
        score = 0
        total_points_earned = 0
        total_possible_points = 0

        # Fetch all questions and their correct answers in one go for efficient scoring
        questions_with_correct_answers = Question.objects.filter(
            quiz=quiz
        ).prefetch_related(
            Prefetch('answers', queryset=Answer.objects.filter(is_correct=True), to_attr='correct_answers')
        ).order_by('id')

        question_map = {q.id: q for q in questions_with_correct_answers}

        for ans_data in user_answers_raw:
            question_id = ans_data.get('questionId')
            selected_answer_id = ans_data.get('selectedAnswerId') # Can be null if no answer selected

            question_obj = question_map.get(question_id)

            if not question_obj:
                # Log this, as it indicates an invalid question ID sent from client
                print(f"Warning: Question ID {question_id} not found for quiz {quiz.pk}")
                continue

            # Add question points to total possible points
            total_possible_points += question_obj.points

            selected_answer_obj = None
            if selected_answer_id is not None:
                try:
                    # Verify the selected answer belongs to the current question
                    selected_answer_obj = Answer.objects.get(id=selected_answer_id, question=question_obj)
                except Answer.DoesNotExist:
                    # Log this, as it indicates an invalid answer ID for the question
                    print(f"Warning: Answer ID {selected_answer_id} not found for question {question_id}")
                    selected_answer_obj = None # Ensure it's None if not found

            # Create StudentAnswer record
            StudentAnswer.objects.create(
                submission=submission,
                question=question_obj,
                selected_answer=selected_answer_obj # Will be None if no answer selected or invalid
            )

            # Check if the selected answer is correct (server-side validation)
            is_correct = False
            if selected_answer_obj and question_obj.correct_answers:
                # Check if the selected answer is one of the correct answers for this question
                # (Handles multiple correct answers if your model allows that, though currently it's single is_correct)
                if selected_answer_obj in question_obj.correct_answers:
                    is_correct = True

            if is_correct:
                total_points_earned += question_obj.points
                score += 1 # This 'score' variable counts correct questions, not points

        # Calculate final percentage score based on points
        if total_possible_points > 0:
            submission.score = round((total_points_earned / total_possible_points) * 100, 2)
        else:
            submission.score = 0

        submission.save()

        # Return JSON response for success
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
