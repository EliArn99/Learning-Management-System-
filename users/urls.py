from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from users import views as user_views

app_name = 'users'

urlpatterns = [
    path('profile/', views.profile_redirect_view, name='profile_redirect'),
    path('student/', views.student_profile_view, name='student_profile'),
    path('teacher/', views.teacher_profile_view, name='teacher_profile'),
    path('approval-pending/', views.approval_pending_view, name='approval_pending'),
    path('register/student/', views.register_student, name='register_student'),
    path('register/teacher/', views.register_teacher, name='register_teacher'),


]


urlpatterns += [
    path('login/', user_views.custom_login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
