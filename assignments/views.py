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
