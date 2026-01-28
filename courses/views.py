import json
import os
from decimal import Decimal, InvalidOperation
from collections import defaultdict

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404

from .models import Course, Enrollment


def course_list_view(request):
    courses = Course.objects.all().select_related("teacher__user")
    return render(request, "courses/course_list.html", {"courses": courses})


def checkout(request):
    return render(request, "courses/checkout.html")


def simple_checkout(request):
    return render(request, "courses/simple_checkout.html")


@login_required
def my_courses_view(request):
    if request.user.is_student:
        enrollments = (
            Enrollment.objects.filter(student=request.user.studentprofile)
            .select_related("course", "course__teacher__user")
        )
        courses = [e.course for e in enrollments]
    elif request.user.is_teacher:
        courses = Course.objects.filter(teacher=request.user.teacherprofile).select_related("teacher__user")
    else:
        courses = []
    return render(request, "courses/my_courses.html", {"courses": courses})


@login_required
def create_course_view(request):
    if not request.user.is_teacher:
        messages.error(request, "Само преподавател може да създава курс.")
        return redirect("courses:course_list")

    from .forms import CourseForm  # local import to keep forms slim

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

    return render(request, "courses/create_course.html", {"form": form})


@login_required
def course_detail_view(request, slug):
    course = get_object_or_404(Course, slug=slug)

    current_enrollment = None
    has_paid_access = False

    if request.user.is_student:
        current_enrollment = Enrollment.objects.filter(
            student=request.user.studentprofile, course=course
        ).first()
        has_paid_access = bool(current_enrollment and current_enrollment.is_paid)

    if request.user.is_student and request.method == "POST" and not current_enrollment:
        new_enrollment = Enrollment.objects.create(
            student=request.user.studentprofile,
            course=course,
            is_paid=False,
        )
        messages.info(request, f'Записът за курса "{course.name}" е създаден. Пренасочваме към плащане...')
        return redirect("courses:checkout_with_id", enrollment_id=new_enrollment.id)

    modules = course.modules.select_related("category").all()

    grouped_modules = defaultdict(list)
    for m in modules:
        category_name = m.category.name if m.category else "Без категория"

        grouped_modules[category_name].append({
            "id": m.id,
            "title": m.title,
            "code": m.code,
            "description": m.description if has_paid_access else "",
        })

    enrolled_students = []
    if request.user.is_teacher and course.teacher and request.user.teacherprofile == course.teacher:
        enrolled_students = (
            Enrollment.objects.filter(course=course, is_paid=True)
            .select_related("student__user")
            .order_by("-enrolled_at")
        )

    context = {
        "course": course,
        "has_paid_access": has_paid_access,
        "is_enrolled": current_enrollment is not None,
        "current_enrollment_id": current_enrollment.id if current_enrollment else None,
        "enrolled_students": enrolled_students,
        "grouped_modules": dict(grouped_modules),
    }
    return render(request, "courses/course_detail.html", context)


@login_required
def checkout_with_id(request, enrollment_id):
    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id,
        student=request.user.studentprofile,
        is_paid=False,
    )

    course = enrollment.course
    amount_to_pay = course.price or Decimal("0.00")

    context = {
        "enrollment": enrollment,
        "course": course,
        "amount_to_pay": amount_to_pay,
    }
    return render(request, "courses/checkout.html", context)


def _paypal_base_url() -> str:
    mode = os.environ.get("PAYPAL_MODE", "sandbox").lower()
    return "https://api-m.paypal.com" if mode == "live" else "https://api-m.sandbox.paypal.com"


def _paypal_access_token() -> str:
    client_id = os.environ.get("PAYPAL_CLIENT_ID")
    secret = os.environ.get("PAYPAL_SECRET")
    if not client_id or not secret:
        raise RuntimeError("PayPal credentials are missing (PAYPAL_CLIENT_ID / PAYPAL_SECRET).")

    url = f"{_paypal_base_url()}/v1/oauth2/token"
    resp = requests.post(
        url,
        auth=(client_id, secret),
        headers={"Accept": "application/json"},
        data={"grant_type": "client_credentials"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _verify_and_capture_paypal_order(order_id: str, expected_amount: Decimal) -> str:
    """
    Verifies and captures the PayPal order.
    Returns a transaction reference (capture id or order id) if successful.
    Raises exception if verification fails.
    """
    token = _paypal_access_token()
    base = _paypal_base_url()

    # Capture the order (recommended flow)
    capture_url = f"{base}/v2/checkout/orders/{order_id}/capture"
    capture_resp = requests.post(
        capture_url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={},
        timeout=15,
    )
    capture_resp.raise_for_status()
    capture_data = capture_resp.json()

    status = capture_data.get("status")
    if status not in {"COMPLETED", "APPROVED"}:
        raise ValueError(f"PayPal capture status not acceptable: {status}")

    capture_id = None
    captured_amount = None

    pus = capture_data.get("purchase_units") or []
    if pus:
        payments = (pus[0].get("payments") or {})
        captures = payments.get("captures") or []
        if captures:
            capture_id = captures[0].get("id")
            amt = captures[0].get("amount") or {}
            try:
                captured_amount = Decimal(str(amt.get("value")))
            except (InvalidOperation, TypeError):
                captured_amount = None

    # Amount check (best-effort)
    if captured_amount is not None and expected_amount is not None:
        if captured_amount != expected_amount:
            raise ValueError(f"Amount mismatch. expected={expected_amount} got={captured_amount}")

    return capture_id or order_id


@login_required
def payment_confirm_view(request, enrollment_id):
    """
    Browser callback endpoint:
    - User is logged in
    - Front-end sends PayPal orderID/transaction_id after approval
    - Server verifies/captures via PayPal API and then marks enrollment paid
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid method."}, status=405)

    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id,
        student=request.user.studentprofile,
        is_paid=False,
    )

    # Parse payload (JSON or form-encoded)
    order_id = None
    if request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON.")
        order_id = payload.get("orderID") or payload.get("order_id") or payload.get("transaction_id")
    else:
        order_id = request.POST.get("orderID") or request.POST.get("order_id") or request.POST.get("transaction_id")

    if not order_id:
        return JsonResponse({"status": "error", "message": "Missing PayPal order id."}, status=400)

    try:
        expected_amount = enrollment.course.price or Decimal("0.00")
        tx_ref = _verify_and_capture_paypal_order(order_id=str(order_id), expected_amount=expected_amount)
    except Exception as exc:
        return JsonResponse({"status": "error", "message": f"Payment verification failed: {exc}"}, status=400)

    enrollment.is_paid = True
    enrollment.transaction_id = tx_ref
    enrollment.save(update_fields=["is_paid", "transaction_id"])

    return JsonResponse({
        "status": "success",
        "redirect_url": enrollment.course.get_absolute_url(),
    })
