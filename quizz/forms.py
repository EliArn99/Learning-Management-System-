from django import forms
from .models import Quiz, Question, Answer, QUESTION_TYPE_CHOICES


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'course', 'available_from', 'available_until', 'time_limit', 'num_questions_to_select']
        widgets = {
            'available_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'available_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'points', 'type']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={'placeholder': 'Текст на отговора'}),
        }
