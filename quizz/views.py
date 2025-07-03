import json

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from .models import Quiz, Answer, Submission, StudentAnswer, Question
from .forms import QuizForm, QuestionForm, AnswerForm
# quizz/views.py
# ... (останалите импорти)
from django.forms import inlineformset_factory
from django.db import transaction  # За атомарни операции

# ... (останалите класове и функции)

# Formset за въпроси към тест
# Quiz е родител, Question е дете
QuestionFormSet = inlineformset_factory(
    Quiz,
    Question,
    form=QuestionForm,
    extra=1,  # Колко празни форми да се покажат първоначално
    can_delete=True,
    min_num=1,  # Минимум 1 въпрос
    validate_min=True,
)

# Formset за отговори към въпрос
# Question е родител, Answer е дете
AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    form=AnswerForm,
    extra=4,  # Колко празни форми за отговори да се покажат
    can_delete=True,
    min_num=2,  # Минимум 2 отговора за въпрос
    validate_min=True,
)


# ✅ CBV за добавяне/редактиране на въпроси и отговори към тест
class QuizQuestionsUpdateView(LoginRequiredMixin, DetailView):  # Използваме DetailView за да вземем quiz обекта
    model = Quiz
    template_name = 'quiz/quiz_questions_form.html'
    context_object_name = 'quiz'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.get_object()

        # Проверка дали текущият потребител е създател на теста
        if self.request.user.teacherprofile != quiz.created_by:
            raise HttpResponseForbidden("Нямате право да редактирате този тест.")

        if self.request.POST:
            context['question_formset'] = QuestionFormSet(self.request.POST, instance=quiz)
            # За всеки въпрос, трябва да инициализираме AnswerFormSet
            # Това е по-сложно и обикновено се прави с JavaScript на фронтенда
            # За простота, тук ще покажем само QuestionFormSet
            # и ще приемем, че отговорите се добавят след като въпросът е създаден
            # или ще го направим по-сложно с вложени formsets
        else:
            context['question_formset'] = QuestionFormSet(instance=quiz)

        # Подготовка на вложени formsets за отговори
        # Това е по-сложна част и често изисква JavaScript на фронтенда
        # или отделни форми за редактиране на отговорите на всеки въпрос.
        # За целите на демонстрирането на функционалност, ще го направим по-просто:
        # ще позволим добавяне на въпроси, а отговорите ще се добавят отделно
        # или ще приемем, че всеки въпрос има фиксиран брой отговори, които се създават с него.

        # За по-лесно, ще направим така, че при създаване на въпрос да се създават и празни полета за отговори.
        # Това е по-сложно за обработка във View, ако искаме да ги обработим наведнъж.
        # Алтернатива: Отделна страница за редактиране на въпрос и неговите отговори.
        # Нека изберем по-простата алтернатива за начало.

        # Временно решение: Ще покажем само QuestionFormSet.
        # За всеки Question във formset-а, ще трябва да има AnswerFormSet.
        # Това е "вложен formset" и е по-сложно.
        # Засега, ще направим View, което позволява добавяне на въпроси.
        # След това ще добавим функционалност за редактиране на отделен въпрос и неговите отговори.

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        quiz = self.object

        if self.request.user.teacherprofile != quiz.created_by:
            return HttpResponseForbidden("Нямате право да редактирате този тест.")

        formset = QuestionFormSet(request.POST, instance=quiz)

        if formset.is_valid():
            with transaction.atomic():  # За да гарантираме, че всички промени са атомарни
                formset.save()
            return redirect('quizz:quiz_detail', pk=quiz.pk)  # Връщаме се към детайлите на теста
        else:
            return self.render_to_response(self.get_context_data(question_formset=formset))


# ✅ CBV за редактиране на отделен въпрос и неговите отговори
class QuestionUpdateView(LoginRequiredMixin, DetailView):
    model = Question
    template_name = 'quiz/question_form.html'
    context_object_name = 'question'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question = self.get_object()

        # Проверка дали текущият потребител е създател на теста, към който принадлежи въпросът
        if self.request.user.teacherprofile != question.quiz.created_by:
            raise HttpResponseForbidden("Нямате право да редактирате този въпрос.")

        if self.request.POST:
            context['answer_formset'] = AnswerFormSet(self.request.POST, instance=question)
        else:
            context['answer_formset'] = AnswerFormSet(instance=question)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        question = self.object

        if self.request.user.teacherprofile != question.quiz.created_by:
            return HttpResponseForbidden("Нямате право да редактирате този въпрос.")

        formset = AnswerFormSet(request.POST, instance=question)

        if formset.is_valid():
            with transaction.atomic():
                formset.save()
            return redirect('quizz:quiz_detail', pk=question.quiz.pk)  # Връщаме се към детайлите на теста
        else:
            return self.render_to_response(self.get_context_data(answer_formset=formset))


class QuizListView(ListView):
    model = Quiz
    template_name = 'quiz/quiz_list.html'
    context_object_name = 'quizzes'


class QuizCreateView(LoginRequiredMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'quiz/quiz_form.html'
    # Define a default success_url to satisfy Django's check.
    # This URL won't typically be used because form_valid will override the redirect.
    success_url = reverse_lazy('quizz:quiz_list') # Or any other static URL you deem appropriate

    def form_valid(self, form):
        # Assign the creator before saving the form instance
        form.instance.created_by = self.request.user.teacherprofile
        # Call the parent form_valid method. This saves the form.
        # It's crucial that this line is executed BEFORE you try to access form.instance.pk
        # The return value of super().form_valid(form) is typically an HttpResponseRedirect,
        # but we're going to override it with our own redirect.
        response = super().form_valid(form) # This line saves the quiz object and populates form.instance.pk

        # After super().form_valid(form) completes, form.instance.pk will be available.
        # Now, redirect to the specific page to add questions for the newly created quiz.
        return redirect('quizz:quiz_add_questions', pk=form.instance.pk) # This is the desired redirect

    def get_form(self):
        form = super().get_form()
        # Filter courses to only those taught by the current teacher
        form.fields['course'].queryset = self.request.user.teacherprofile.taught_courses.all()
        return form

class QuizDetailView(DetailView):
    model = Quiz
    template_name = 'quiz/quiz_detail.html'
    context_object_name = 'quiz'


class QuizTakeView(LoginRequiredMixin,
                   DetailView):  # Променяме го на CBV за по-чист код и използване на LoginRequiredMixin
    model = Quiz
    template_name = 'quiz/quiz_take.html'
    context_object_name = 'quiz'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.get_object()

        # Проверка дали тестът е активен
        if not quiz.is_active():
            raise HttpResponseForbidden("Този тест не е активен в момента.")

        # Проверка дали студентът вече е изпълнил теста (може да искате да позволите многократно изпълнение)
        # Ако искате само еднократно изпълнение:
        # if Submission.objects.filter(quiz=quiz, student=self.request.user).exists():
        #     return HttpResponseForbidden("Вече сте изпълнили този тест.")

        # Подготвяме данните за въпросите и отговорите за JavaScript
        quiz_data = []
        for q_obj in quiz.questions.all().order_by('id'):  # Сортираме, за да е последователно
            options_data = []
            # Извличаме отговорите, като съхраняваме техния ID и дали са верни
            # Важно: Не изпращайте 'is_correct' към клиента, ако не е необходимо за клиента.
            # За автоматично оценяване, 'correct' ще е индекса, а не булевата стойност.
            correct_index = -1
            for idx, a_obj in enumerate(q_obj.answers.all().order_by('id')):
                options_data.append({
                    'id': a_obj.id,  # Ще използваме това при събмит, за да запазим StudentAnswer
                    'text': a_obj.text
                })
                if a_obj.is_correct:
                    correct_index = idx  # Запазваме индекса на верния отговор

            quiz_data.append({
                'id': q_obj.id,
                'question': q_obj.text,
                'options': options_data,
                'correct_index': correct_index  # Това НЕ трябва да се изпраща към клиента в реален тест!
                # Оценяването трябва да става на сървъра.
            })
        # За сигурност, НЕ ИЗПРАЩАЙТЕ correct_index към клиента за продукционни приложения.
        # Оценяването трябва да става изцяло на сървъра.
        # За целите на интерактивния UI, временно ще го оставим.

        context['quiz_data_json'] = json.dumps(quiz_data)
        return context

    def post(self, request, *args, **kwargs):
        quiz = self.get_object()
        student = request.user

        # Проверка дали тестът е активен
        if not quiz.is_active():
            return JsonResponse({'error': 'Този тест не е активен.'}, status=403)

        # Проверка дали студентът вече е изпълнил теста (ако искате еднократно изпълнение)
        if Submission.objects.filter(quiz=quiz, student=student).exists():
            return JsonResponse({'error': 'Вече сте изпълнили този тест.'}, status=403)

        try:
            # Парсваме JSON данните с отговорите от клиента
            data = json.loads(request.body)
            user_answers_raw = data.get('userAnswers', [])
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Невалиден JSON формат.'}, status=400)

        submission = Submission.objects.create(quiz=quiz, student=student)
        score = 0

        questions_in_quiz = quiz.questions.all().order_by('id')

        # Създаваме речник за бърз достъп до въпросите по техния ID
        question_map = {q.id: q for q in questions_in_quiz}

        for ans_data in user_answers_raw:
            question_id = ans_data.get('questionId')
            selected_answer_id = ans_data.get('selectedAnswerId')

            question_obj = question_map.get(question_id)

            if not question_obj:
                # Ако въпросът не принадлежи към този тест или не съществува
                continue

            try:
                # Взимаме избрания отговор от базата данни
                selected_answer_obj = Answer.objects.get(id=selected_answer_id, question=question_obj)
            except Answer.DoesNotExist:
                selected_answer_obj = None  # Или обработете грешката, ако избран отговор не съществува

            StudentAnswer.objects.create(
                submission=submission,
                question=question_obj,
                selected_answer=selected_answer_obj
            )

            if selected_answer_obj and selected_answer_obj.is_correct:
                score += 1

        # Изчисляване на резултата като процент
        total_questions_count = questions_in_quiz.count()
        if total_questions_count > 0:
            submission.score = round((score / total_questions_count) * 100, 2)
        else:
            submission.score = 0

        submission.save()

        # Връщаме JSON отговор за успех
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
