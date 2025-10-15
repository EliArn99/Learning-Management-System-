from django.urls import path
from .views import (
    QuizListView, QuizDetailView, QuizTakeView, quiz_results,
    QuizManageListView, QuizCreateView, QuizUpdateView, QuizDeleteView,
    manage_questions_and_answers,  # Функционален изглед за въпроси/отговори
)

app_name = 'quizz'

urlpatterns = [
    path('', QuizListView.as_view(), name='quiz_list'),
    path('<int:pk>/', QuizDetailView.as_view(), name='quiz_detail'),
    path('<int:pk>/take/', QuizTakeView.as_view(), name='quiz_take'),
    path('<int:pk>/results/', quiz_results, name='quiz_results'),

    path('manage/', QuizManageListView.as_view(), name='quiz_manage_list'),
    path('manage/create/', QuizCreateView.as_view(), name='quiz_create'),
    path('manage/<int:pk>/update/', QuizUpdateView.as_view(), name='quiz_update'),

    path('manage/<int:pk>/delete/', QuizDeleteView.as_view(), name='quiz_delete'),

    path('manage/<int:quiz_pk>/questions/', manage_questions_and_answers, name='manage_q_a'),

]
