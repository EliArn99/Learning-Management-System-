from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Assignment, Submission
from .forms import AssignmentSubmissionForm
from users.models import StudentProfile
from django.contrib.auth.decorators import login_required

@login_required
def assignment_list_view(request):
    assignments = Assignment.objects.all().order_by('due_date')
    return render(request, 'assignments/assignment_list.html', {'assignments': assignments})


@login_required
def my_assignments_view(request):
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    my_courses = student_profile.courses.all()
    assignments = Assignment.objects.filter(course__in=my_courses).order_by('due_date')

    assignments_with_status = []
    for assignment in assignments:
        submission = Submission.objects.filter(assignment=assignment, student=student_profile).first()
        assignments_with_status.append({
            'assignment': assignment,
            'submission': submission,  # None ако не е предадено
        })

    return render(request, 'assignments/my_assignments.html', {'assignments_with_status': assignments_with_status})
