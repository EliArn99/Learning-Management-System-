# courses/views.py
from collections import defaultdict

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from .models import Course, Enrollment
from .forms import CourseForm, EnrollmentForm


def course_list_view(request):
    courses = Course.objects.all().select_related('teacher')
    return render(request, 'courses/course_list.html', {'courses': courses})


def checkout(request):
    return render(request, 'courses/checkout.html')


def simple_checkout(request):
    return render(request, 'courses/simple_checkout.html')


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


@login_required
def course_detail_view(request, slug):
    course = get_object_or_404(Course, slug=slug)

    # 1. Инициализиране на статуси за достъп и запис
    current_enrollment = None
    has_paid_access = False

    if request.user.is_student:
        try:
            # Опитваме се да намерим съществуващ запис (платен или неплатен)
            current_enrollment = Enrollment.objects.get(
                student=request.user.studentprofile,
                course=course
            )
            # Проверяваме дали записът е платен
            has_paid_access = current_enrollment.is_paid
        except Enrollment.DoesNotExist:
            # Няма създаден запис
            pass

    # 2. Логика за ЗАПИСВАНЕ (POST заявка)
    # Позволяваме създаване на запис само ако потребителят е студент, изпраща POST и няма съществуващ запис.
    if request.user.is_student and request.method == 'POST' and not current_enrollment:
        # Вместо да използваме EnrollmentForm за директно запазване,
        # създаваме обекта ръчно, за да контролираме is_paid=False.

        # NOTE: Ако EnrollmentForm има само course и student, може да го прескочиш.
        # Ако има други полета, може да го използваш така:
        # enroll_form = EnrollmentForm(request.POST) # или data={'...'}
        # if enroll_form.is_valid():

        # Създаване на НЕПЛАТЕН запис
        new_enrollment = Enrollment.objects.create(
            student=request.user.studentprofile,
            course=course,
            is_paid=False  # Записът е създаден, но още не е платен
        )

        messages.info(request, f'Записът за курса "{course.name}" е създаден. Пренасочваме към плащане...')

        # *** ТРЯБВА ДА СЕ ПРОМЕНИ: Пренасочване към Checkout с ID на записа ***
        # Уверете се, че имате URL с име 'checkout_with_id', което приема enrollment_id
        return redirect('courses:checkout_with_id', enrollment_id=new_enrollment.id)

        # 3. Извличане на съдържанието на курса
    modules = course.modules.select_related('category')

    grouped_modules = defaultdict(list)
    for module in modules:
        category_name = module.category.name if module.category else "Без категория"
        # !!! ВАЖНО: Трябва да имате логика, която проверява дали has_paid_access е True,
        # преди да покаже пълното съдържание на модула.
        # Ако has_paid_access е False, покажете само заглавията/въведението, а не ресурсите.
        grouped_modules[category_name].append(module)

    # ... Останалата логика за преподаватели ...
    enrolled_students = []
    if request.user.is_teacher and request.user.teacherprofile == course.teacher:
        # Може да филтрирате само платените студенти, ако желаете
        enrolled_students = Enrollment.objects.filter(course=course, is_paid=True).select_related('student__user')

    context = {
        'course': course,
        'has_paid_access': has_paid_access,  # Новият ключ за фронтенда
        'is_enrolled': current_enrollment is not None,  # Дали има запис (платен или не)
        'current_enrollment_id': current_enrollment.id if current_enrollment else None,  # ID за плащане/пренасочване
        # 'enroll_form': enroll_form, # Може да го премахнете, ако не се използва
        'enrolled_students': enrolled_students,
        'grouped_modules': dict(grouped_modules),
    }
    return render(request, 'courses/course_detail.html', context)


# @login_required
# def course_detail_view(request, slug):
#     course = get_object_or_404(Course, slug=slug)
#     is_enrolled = False
#     if request.user.is_student:
#         is_enrolled = Enrollment.objects.filter(student=request.user.studentprofile, course=course).exists()
#
#     if request.user.is_student and request.method == 'POST' and not is_enrolled:
#         enroll_form = EnrollmentForm(data={'student': request.user.studentprofile.id, 'course': course.id})
#         if enroll_form.is_valid():
#             enroll_form.save()
#             messages.success(request, 'Успешно се записахте в курса!')
#             return redirect('courses:course_detail', slug=slug)
#     else:
#         enroll_form = EnrollmentForm()
#
#     modules = course.modules.select_related('category')
#
#     grouped_modules = defaultdict(list)
#     for module in modules:
#         category_name = module.category.name if module.category else "Без категория"
#         grouped_modules[category_name].append(module)
#
#     enrolled_students = []
#     if request.user.is_teacher and request.user.teacherprofile == course.teacher:
#         enrolled_students = Enrollment.objects.filter(course=course).select_related('student__user')
#
#     context = {
#         'course': course,
#         'is_enrolled': is_enrolled,
#         'enroll_form': enroll_form,
#         'enrolled_students': enrolled_students,
#         'grouped_modules': dict(grouped_modules),  # важно!
#     }
#     return render(request, 'courses/course_detail.html', context)


@login_required
def course_enroll(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.student = request.user.student
            enrollment.course = course
            enrollment.save()
            return redirect('course_detail', course_id=course.id)
    else:
        form = EnrollmentForm()

    return render(request, 'courses/course_enroll.html', {
        'course': course,
        'form': form
    })


@login_required
def checkout_with_id(request, enrollment_id):
    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id,
        student=request.user.studentprofile,
        is_paid=False
    )

    course = enrollment.course
    amount_to_pay = getattr(
        course, 'price', 0.00
    )

    context = {
        'enrollment': enrollment,
        'course': course,
        'amount_to_pay': amount_to_pay,
    }
    # Пренасочваме към темплейта, който съдържа PayPal бутона
    return render(request, 'courses/checkout.html', context)


# Използвай декоратора, ако ще го викаш през AJAX/fetch от PayPal
@csrf_exempt
@login_required
def payment_success_webhook(request, enrollment_id):
    if request.method == 'POST':
        try:
            enrollment = Enrollment.objects.get(
                id=enrollment_id,
                student=request.user.studentprofile,
                is_paid=False
            )
        except Enrollment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Записът не е намерен или вече е платен.'}, status=400)

        # Получаване на данни от PayPal (трябва да се верифицират!)
        # За простота, приемаме, че request.POST или request.body съдържа transaction_id
        transaction_id = request.POST.get('transaction_id') or request.body.get('transaction_id')

        # !!! ВАЖНО: В реално приложение ТРЯБВА да верифицираш транзакцията
        # със сървърна заявка към PayPal/Stripe, преди да маркираш като платено.

        enrollment.is_paid = True
        enrollment.transaction_id = transaction_id
        enrollment.save()

        # Можеш да добавиш съобщение за успех или да върнеш JSON
        messages.success(request, f'Плащането за курса "{enrollment.course.title}" е успешно! Имаш пълен достъп.')

        return JsonResponse({
            'status': 'success',
            'redirect_url': enrollment.course.get_absolute_url()
        })

    return JsonResponse({'status': 'error', 'message': 'Невалиден метод на заявка.'}, status=405)
