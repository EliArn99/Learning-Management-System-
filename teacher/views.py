from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not getattr(request.user, 'is_teacher', False):
            return HttpResponseForbidden("Достъпът е само за преподаватели.")
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@teacher_required
def dashboard(request):
    return render(request, 'teachers/teacher_dashboard.html')




