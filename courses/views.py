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

@login_required
def create_course_view(request):
    if not request.user.is_teacher:
        messages.error(request, "Само преподавател може да създава курс.")
        return redirect('courses:course_list')

    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user.teacherprofile
            course.save()
            messages.success(request, "Курсът е създаден успешно!")
            return redirect('courses:course_detail', slug=course.slug)
    else:
        form = CourseForm()

    return render(request, "courses/create_course.html", {"form": form})

