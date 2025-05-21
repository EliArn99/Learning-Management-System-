from django.urls import path
from . import views

app_name = 'dashboards'

urlpatterns = [
    path('', views.dashboard_home_view, name='dashboard_home'),
    path('teacher/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('about/', views.about, name='about'),
    path('contacts/', views.contacts, name='contacts'),
    path('student/', views.student_dashboard_view, name='student_dashboard'),
]
