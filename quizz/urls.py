from django.urls import path
from .views import (
    QuizListView, QuizCreateView, QuizDetailView,
    QuizTakeView, quiz_results, QuizQuestionsUpdateView, QuestionUpdateView
)
from . import views


app_name = 'quizz'

urlpatterns = [
    path('', QuizListView.as_view(), name='quiz_list'),
    path('create/', QuizCreateView.as_view(), name='quiz_create'),
    path('<int:pk>/', QuizDetailView.as_view(), name='quiz_detail'),
    path('<int:pk>/add_questions/', QuizQuestionsUpdateView.as_view(), name='quiz_add_questions'),
    path('question/<int:pk>/edit/', QuestionUpdateView.as_view(), name='question_edit'),
    path('<int:pk>/take/', QuizTakeView.as_view(), name='quiz_take'),
    path('<int:pk>/results/', quiz_results, name='quiz_results'),
]
