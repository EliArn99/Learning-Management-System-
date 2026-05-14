import json
from collections import defaultdict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import teacher_required
from .forms import CourseForm
from .models import Course, Enrollment
from .services import verify_and_capture_paypal_order


def course_list_view(request):
    courses = Course.objects.all().select_related("teacher__user")

    paginator = Paginator(courses, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "courses/course_list.html",
        {
            "page_obj": page_obj,
            "courses": page_obj.object_list,
        },
    )


def checkout(request):
    return render(request, "courses/checkout.html")


def simple_checkout(request):
    return render(request, "courses/simple_checkout.html")


@login_required
def my_courses_view(request):
    if request.user.is_student:
        enrollments = Enrollment.objects.filter(
            student=request.user.studentprofile,
        ).select_related(
            "course",
            "course__teacher__user",
        )
        courses = [enrollment.course for enrollment in enrollments]

    elif request.user.is_teacher:
        courses = Course.objects.filter(
            teacher=request.user.teacherprofile,
        ).select_related("teacher__user")

    else:
        courses = []

    return render(
        request,
        "courses/my_courses.html",
        {
            "courses": courses,
        },
    )


@login_required
@teacher_required
def create_course_view(request):
    if request.method == "POST":
        form = CourseForm(request.POST)

        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user.teacherprofile
            course.save()

            messages.success(request, "Курсът е създаден успешно!")
            return redirect("courses:course_detail", slug=course.slug)

    else:
        form = CourseForm()

    return render(
        request,
        "courses/create_course.html",
        {
            "form": form,
        },
    )


@login_required
def course_detail_view(request, slug):
    course = get_object_or_404(
        Course.objects.select_related("teacher__user").prefetch_related(
            "modules__category",
            "enrollments__student__user",
        ),
        slug=slug,
    )

    current_enrollment = None
    has_paid_access = False

    if request.user.is_student:
        current_enrollment = Enrollment.objects.filter(
            student=request.user.studentprofile,
            course=course,
        ).first()

        has_paid_access = bool(current_enrollment and current_enrollment.is_paid)

    if request.user.is_student and request.method == "POST" and not current_enrollment:
        new_enrollment = Enrollment.objects.create(
            student=request.user.studentprofile,
            course=course,
            is_paid=False,
        )

        messages.info(
            request,
            f'Записът за курса "{course.name}" е създаден. Пренасочваме към плащане...',
        )

        return redirect(
            "courses:checkout_with_id",
            enrollment_id=new_enrollment.id,
        )

    modules = course.modules.select_related("category").all()

    grouped_modules = defaultdict(list)

    for module in modules:
        category_name = module.category.name if module.category else "Без категория"

        grouped_modules[category_name].append(
            {
                "id": module.id,
                "title": module.title,
                "code": module.code,
                "description": module.description if has_paid_access else "",
            }
        )

    enrolled_students = []

    if (
        request.user.is_teacher
        and course.teacher
        and request.user.teacherprofile == course.teacher
    ):
        enrolled_students = Enrollment.objects.filter(
            course=course,
            is_paid=True,
        ).select_related("student__user").order_by("-enrolled_at")

    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "has_paid_access": has_paid_access,
            "is_enrolled": current_enrollment is not None,
            "current_enrollment_id": current_enrollment.id if current_enrollment else None,
            "enrolled_students": enrolled_students,
            "grouped_modules": dict(grouped_modules),
        },
    )


@login_required
def checkout_with_id(request, enrollment_id):
    enrollment = get_object_or_404(
        Enrollment.objects.select_related("course", "student__user"),
        id=enrollment_id,
        student=request.user.studentprofile,
        is_paid=False,
    )

    course = enrollment.course
    amount_to_pay = course.price or Decimal("0.00")

    return render(
        request,
        "courses/checkout.html",
        {
            "enrollment": enrollment,
            "course": course,
            "amount_to_pay": amount_to_pay,
        },
    )


@login_required
def payment_confirm_view(request, enrollment_id):
    if request.method != "POST":
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid method.",
            },
            status=405,
        )

    enrollment = get_object_or_404(
        Enrollment.objects.select_related("course", "student__user"),
        id=enrollment_id,
        student=request.user.studentprofile,
        is_paid=False,
    )

    order_id = None

    if request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON.")

        order_id = (
            payload.get("orderID")
            or payload.get("order_id")
            or payload.get("transaction_id")
        )
    else:
        order_id = (
            request.POST.get("orderID")
            or request.POST.get("order_id")
            or request.POST.get("transaction_id")
        )

    if not order_id:
        return JsonResponse(
            {
                "status": "error",
                "message": "Missing PayPal order id.",
            },
            status=400,
        )

    try:
        expected_amount = enrollment.course.price or Decimal("0.00")
        transaction_reference = verify_and_capture_paypal_order(
            order_id=str(order_id),
            expected_amount=expected_amount,
        )

    except Exception as exc:
        return JsonResponse(
            {
                "status": "error",
                "message": f"Payment verification failed: {exc}",
            },
            status=400,
        )

    enrollment.is_paid = True
    enrollment.transaction_id = transaction_reference
    enrollment.save(update_fields=["is_paid", "transaction_id"])

    return JsonResponse(
        {
            "status": "success",
            "redirect_url": enrollment.course.get_absolute_url(),
        }
    )
