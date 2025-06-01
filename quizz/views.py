from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy
from .models import Quiz, Question, Answer, Submission, StudentAnswer
from .forms import QuizForm

# ✅ CBV за списък с тестове
class QuizListView(ListView):
    model = Quiz
    template_name = 'quiz/quiz_list.html'
    context_object_name = 'quizzes'

# ✅ CBV за създаване на тест
class QuizCreateView(LoginRequiredMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'quiz/quiz_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user.teacherprofile  # 👈
        return super().form_valid(form)

    def get_form(self):
        form = super().get_form()
        # Ограничаваме само курсовете на този преподавател
        form.fields['course'].queryset = self.request.user.teacherprofile.courses.all()
        return form

# ✅ CBV за подробности за тест
class QuizDetailView(DetailView):
    model = Quiz
    template_name = 'quiz/quiz_detail.html'
    context_object_name = 'quiz'

# 🧠 FBV за изпълнение на теста
def quiz_take(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == 'POST':
        submission = Submission.objects.create(quiz=quiz, student=request.user)
        score = 0
        for question in quiz.questions.all():
            selected_answer_id = request.POST.get(f'question_{question.id}')
            if selected_answer_id:
                answer = Answer.objects.get(id=selected_answer_id)
                StudentAnswer.objects.create(submission=submission, question=question, selected_answer=answer)
                if answer.is_correct:
                    score += 1
        submission.score = round((score / quiz.questions.count()) * 100, 2)
        submission.save()
        return redirect('quizz:quiz_results', pk=quiz.pk)
    return render(request, 'quiz/quiz_take.html', {'quiz': quiz})

# 🧠 FBV за резултати
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
