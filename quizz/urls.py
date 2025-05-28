from django.urls import path
from .views import (
    QuizListView, QuizCreateView, QuizDetailView,
    quiz_take, quiz_results
)

app_name = 'quizz'

urlpatterns = [
    path('', QuizListView.as_view(), name='quiz_list'),
    path('create/', QuizCreateView.as_view(), name='quiz_create'),
    path('<int:pk>/', QuizDetailView.as_view(), name='quiz_detail'),
    path('<int:pk>/take/', quiz_take, name='quiz_take'),
    path('<int:pk>/results/', quiz_results, name='quiz_results'),
]
