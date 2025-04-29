# courses/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Course, Enrollment
from .forms  import CourseForm, EnrollmentForm

# ---------- списък с всички курсове ----------
def course_list_view(request):
    courses = Course.objects.all().select_related('teacher')
    return render(request, 'courses/course_list.html', {'courses': courses})


# ---------- „Моите курсове“ ----------
@login_required
def my_courses_view(request):
    if request.user.is_student:
        enrollments = Enrollment.objects.filter(student=request.user.studentprofile).select_related('course')
        courses = [e.course for e in enrollments]
    elif request.user.is_teacher:
        courses = Course.objects.filter(teacher=request.user.teacherprofile)
    else:
        courses = []
    return render(request, 'courses/my_courses.html', {'courses': courses})

