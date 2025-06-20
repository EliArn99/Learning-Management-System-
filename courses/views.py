from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
from django.shortcuts import redirect

from courses.models import Course, Enrollment
from django.shortcuts import render, get_object_or_404





def payment_confirm(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    # Ако вече е записан, не го записвай пак
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        Enrollment.objects.create(student=request.user, course=course)

    return render(request, 'courses/payment_success.html', {'course': course})


def payment_cancel(request):
    return render(request, 'courses/payment_cancel.html')


def course_list(request):
    courses = Course.objects.all()
    return render(request, 'courses/course_list.html', {'courses': courses})


def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    return render(request, 'courses/course_detail.html', {'course': course})


def enroll_course(request, course_id):
    if not request.user.is_authenticated:
        return redirect('users:register')

    course = get_object_or_404(Course, pk=course_id)

    host = request.get_host()
    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": str(course.price),
        "item_name": course.title,
        "invoice": f"{request.user.id}-{course.id}",
        "currency_code": "USD",
        "notify_url": f"http://{host}/paypal/ipn/",
        "return": f"http://{host}/courses/confirm/{course.id}/",
        "cancel_return": f"http://{host}/courses/cancel/",
        "custom": f"{request.user.id}-{course.id}",
    }

    form = PayPalPaymentsForm(initial=paypal_dict)
    return render(request, "courses/payment.html", {"course": course, "form": form})








# # courses/views.py
# from collections import defaultdict

# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages

# from .models import Course, Enrollment
# from .forms  import CourseForm, EnrollmentForm

# # ---------- списък с всички курсове ----------
# def course_list_view(request):
#     courses = Course.objects.all().select_related('teacher')
#     return render(request, 'courses/course_list.html', {'courses': courses})


# def checkout(request):
#     return render(request, 'courses/checkout.html')
# def simple_checkout(request):
#     return render(request, 'courses/simple_checkout.html')

# # ---------- „Моите курсове“ ----------
# @login_required
# def my_courses_view(request):
#     if request.user.is_student:
#         enrollments = Enrollment.objects.filter(student=request.user.studentprofile).select_related('course')
#         courses = [e.course for e in enrollments]
#     elif request.user.is_teacher:
#         courses = Course.objects.filter(teacher=request.user.teacherprofile)
#     else:
#         courses = []
#     return render(request, 'courses/my_courses.html', {'courses': courses})


# # ---------- създаване на курс (само учител) ----------
# @login_required
# def create_course_view(request):
#     if not request.user.is_teacher:
#         messages.error(request, "Само преподавател може да създава курс.")
#         return redirect('courses:course_list')

#     if request.method == "POST":
#         form = CourseForm(request.POST)
#         if form.is_valid():
#             course = form.save(commit=False)
#             course.teacher = request.user.teacherprofile
#             course.save()
#             messages.success(request, "Курсът е създаден успешно!")
#             return redirect('courses:course_detail', slug=course.slug)
#     else:
#         form = CourseForm()

#     return render(request, "courses/create_course.html", {"form": form})


# # ---------- детайли за курс + записване ----------
# @login_required
# def course_detail_view(request, slug):
#     course = get_object_or_404(Course, slug=slug)
#     is_enrolled = False
#     if request.user.is_student:
#         is_enrolled = Enrollment.objects.filter(student=request.user.studentprofile, course=course).exists()

#     if request.user.is_student and request.method == 'POST' and not is_enrolled:
#         enroll_form = EnrollmentForm(data={'student': request.user.studentprofile.id, 'course': course.id})
#         if enroll_form.is_valid():
#             enroll_form.save()
#             messages.success(request, 'Успешно се записахте в курса!')
#             return redirect('courses:course_detail', slug=slug)
#     else:
#         enroll_form = EnrollmentForm()

#     # Само модулите за този курс
#     modules = course.modules.select_related('category')

#     # Групиране по категории
#     grouped_modules = defaultdict(list)
#     for module in modules:
#         category_name = module.category.name if module.category else "Без категория"
#         grouped_modules[category_name].append(module)

#     # Записани студенти (само ако потребителят е преподавател на курса)
#     enrolled_students = []
#     if request.user.is_teacher and request.user.teacherprofile == course.teacher:
#         enrolled_students = Enrollment.objects.filter(course=course).select_related('student__user')

#     context = {
#         'course': course,
#         'is_enrolled': is_enrolled,
#         'enroll_form': enroll_form,
#         'enrolled_students': enrolled_students,
#         'grouped_modules': dict(grouped_modules),  # важно!
#     }
#     return render(request, 'courses/course_detail.html', context)


# @login_required
# def course_enroll(request, course_id):
#     course = get_object_or_404(Course, id=course_id)

#     if request.method == 'POST':
#         form = EnrollmentForm(request.POST)
#         if form.is_valid():
#             enrollment = form.save(commit=False)
#             enrollment.student = request.user.student
#             enrollment.course = course
#             enrollment.save()
#             return redirect('course_detail', course_id=course.id)
#     else:
#         form = EnrollmentForm()

#     return render(request, 'courses/course_enroll.html', {
#         'course': course,
#         'form': form
#     })
