from django.urls import path
from . import views

app_name = 'quizz'

urlpatterns = [
    path('', views.quiz_list, name='quiz_list'),  # списък с всички тестове
    path('create/', views.quiz_create, name='quiz_create'),  # създаване на нов тест
    path('<int:pk>/', views.quiz_detail, name='quiz_detail'),  # преглед на конкретен тест
    path('<int:pk>/take/', views.quiz_take, name='quiz_take'),  # попълване на тест от ученик
    path('<int:pk>/results/', views.quiz_results, name='quiz_results'),  # резултати от тест
]
