from django.shortcuts import render


def home(request):
    return render(request, 'dashboards/home.html')

def dashboard_home_view(request):
    return render(request, 'dashboards/dashboard_home.html')


def teacher_dashboard_view(request):
    return render(request, 'dashboards/teacher_dashboard.html')


def student_dashboard_view(request):
    return render(request, 'dashboards/student_dashboard.html')
