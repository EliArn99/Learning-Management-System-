from functools import wraps
from django.conf import settings
from django.shortcuts import redirect

def _redirect_to_login():
    return redirect(settings.LOGIN_URL)

def student_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not getattr(request.user, "is_student", False):
            return _redirect_to_login()
        return view_func(request, *args, **kwargs)
    return wrapper

def teacher_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not getattr(request.user, "is_teacher", False):
            return _redirect_to_login()
        return view_func(request, *args, **kwargs)
    return wrapper
