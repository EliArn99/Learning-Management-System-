# assignments/views.py
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.mail import send_mail
from courses.models import Course, Enrollment
from .models import Assignment, Submission
from .forms import AssignmentSubmissionForm, GradeSubmissionForm
from users.models import StudentProfile
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import AssignmentForm


@login_required
def assignment_list_view(request):
    assignments = Assignment.objects.all().order_by('due_date')
    return render(request, 'assignments/assignment_list.html', {'assignments': assignments})


@login_required
def my_assignments_view(request):
    student_profile = get_object_or_404(StudentProfile, user=request.user)

    my_courses = Course.objects.filter(enrollments__student=student_profile).distinct()

    assignments = Assignment.objects.filter(course__in=my_courses).order_by('due_date')

    assignments_with_status = []
    for assignment in assignments:
        submission = Submission.objects.filter(assignment=assignment, student=student_profile).first()
        assignments_with_status.append({
            'assignment': assignment,
            'submission': submission,
        })

    return render(request, 'assignments/my_assignments.html', {'assignments_with_status': assignments_with_status})


@login_required
def submit_assignment_view(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)

    student_profile = get_object_or_404(StudentProfile, user=request.user)

    submission, created = Submission.objects.get_or_create(
        assignment=assignment,
        student=student_profile
    )

    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            form.save()
            return redirect('assignments:assignment_detail', pk=assignment.id)
    else:
        form = AssignmentSubmissionForm(instance=submission)

    return render(request, 'assignments/submit_assignment.html', {
        'assignment': assignment,
        'form': form,
        'submission': submission
    })


@login_required
def assignment_detail_view(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    submission = None
    grade_form = None

    if request.user.is_authenticated and hasattr(request.user, 'studentprofile'):
        student_profile = request.user.studentprofile
        submission = Submission.objects.filter(student=student_profile, assignment=assignment).first()

    if request.user.is_authenticated and hasattr(request.user, 'teacherprofile'):
        all_submissions_for_assignment = Submission.objects.filter(assignment=assignment).order_by('-submitted_at')

        if all_submissions_for_assignment.exists():
            first_submission_for_grading = all_submissions_for_assignment.first()
            grade_form = GradeSubmissionForm(instance=first_submission_for_grading)
            submission = first_submission_for_grading

    return render(request, 'assignments/assignment_detail.html', {
        'assignment': assignment,
        'submission': submission,
        'grade_form': grade_form,
    })


def is_teacher(user):
    return hasattr(user, 'teacherprofile')


@user_passes_test(is_teacher)
def teacher_submissions_view(request):
    submissions = Submission.objects.all().order_by('-submitted_at')

    status_filter = request.GET.get('status')  # Get the 'status' parameter from the URL

    if status_filter == 'pending':
        submissions = submissions.filter(grade__isnull=True)
    elif status_filter == 'graded':
        submissions = submissions.filter(grade__isnull=False)


    return render(request, 'assignments/teacher_submissions.html', {
        'submissions': submissions,
        'current_status_filter': status_filter  # Pass the current filter to the template for UI
    })


@user_passes_test(is_teacher)
def grade_submission_view(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    if request.method == 'POST':
        form = GradeSubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            graded_submission = form.save(commit=False)
            graded_submission.graded_at = timezone.now()
            graded_submission.save()

            student_email = submission.student.user.email
            send_mail(
                'Your Assignment Has Been Graded',
                f'Hello {submission.student.user.username},\n\nYour submission for "{submission.assignment.title}" has been graded. You received a {graded_submission.grade}.\n\nFeedback: {graded_submission.feedback}',
                'no-reply@yourplatform.com',
                [student_email],
                fail_silently=True,
            )

            return redirect('assignments:teacher_submissions')
    else:
        form = GradeSubmissionForm(instance=submission)

    return render(request, 'assignments/grade_submission.html', {'form': form, 'submission': submission})


@login_required
@user_passes_test(is_teacher)
def create_assignment_view(request):
    teacher = request.user.teacherprofile

    if request.method == 'POST':
        form = AssignmentForm(request.POST, teacher=teacher)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.save()
            messages.success(request, "Успешно създаде ново задание.")
            return redirect('assignments:assignment_list')
        else:
            print("Form is NOT valid. Errors:", form.errors)
            messages.error(request, "Възникна грешка при създаването на заданието. Моля, проверете въведените данни.")
    else:
        form = AssignmentForm(teacher=teacher)

    return render(request, 'assignments/create_assignment.html', {
        'form': form,
    })


@login_required
def edit_submission_view(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    if submission.student.user != request.user:
        messages.error(request, "Нямате право да редактирате тази задача.")
        return redirect('assignments:assignment_list')

    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            form.save()
            messages.success(request, "Успешно редактирахте заданието.")
            return redirect('assignments:assignment_detail', pk=submission.assignment.id)
    else:
        form = AssignmentSubmissionForm(instance=submission)

    return render(request, 'assignments/edit_submission.html', {
        'form': form,
        'submission': submission
    })


@login_required
@user_passes_test(is_teacher)
def teacher_dashboard_view(request):
    teacher = request.user.teacherprofile
    courses = Course.objects.filter(teacher=teacher)

    total_students = StudentProfile.objects.filter(
        enrollments__course__in=courses
    ).distinct().count()

    assignments = Assignment.objects.filter(course__in=courses)
    submissions = Submission.objects.filter(assignment__in=assignments)

    total_submissions = submissions.count()
    graded_submissions = submissions.filter(grade__isnull=False).count()
    pending_submissions = submissions.filter(grade__isnull=True).count()

    recent_submissions = submissions.order_by('-submitted_at')[:5]

    selected_course_id = request.GET.get("course")
    if selected_course_id:
        submissions = submissions.filter(assignment__course__id=selected_course_id)

    return render(request, 'dashboards/teacher_dashboard.html', {
        'courses': courses,
        'assignments': assignments,
        'submissions': submissions,
        'recent_submissions': recent_submissions,
        'total_submissions': total_submissions,
        'graded_submissions': graded_submissions,
        'pending_submissions': pending_submissions,
        'selected_course_id': selected_course_id,
        'total_students': total_students,
    })


@login_required
def student_dashboard_view(request):
    student = request.user.studentprofile
    courses = Course.objects.filter(enrollments__student=student).distinct()
    assignments = Assignment.objects.filter(course__in=courses)

    upcoming_assignments = assignments.filter(due_date__gt=timezone.now()).order_by('due_date')

    total = assignments.count()
    submitted = Submission.objects.filter(student=student, assignment__in=assignments).count()
    progress = int((submitted / total) * 100) if total else 0

    return render(request, 'dashboards/student_dashboard.html', {
        'courses': courses,
        'assignments': assignments,
        'upcoming_assignments': upcoming_assignments[:5],
        'progress': progress,
    })
