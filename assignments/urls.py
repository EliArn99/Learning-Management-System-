from django.urls import path
from . import views

app_name = 'assignments'

urlpatterns = [
    path('', views.assignment_list_view, name='assignment_list'),
    path('my/', views.my_assignments_view, name='my_assignments'),
    path('submit/', views.submit_assignment_view, name='submit_assignment'),
    path('<int:pk>/', views.assignment_detail_view, name='assignment_detail'),

    # Нови за учителите
    path('teacher/submissions/', views.teacher_submissions_view, name='teacher_submissions'),
    path('teacher/grade/<int:submission_id>/', views.grade_submission_view, name='grade_submission'),
    path('create/', views.create_assignment_view, name='create_assignment'),


]
