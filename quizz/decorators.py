from functools import wraps

from django.core.exceptions import PermissionDenied


def teacher_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not hasattr(request.user, "teacherprofile"):
            raise PermissionDenied("Нямате права на преподавател.")
        return view_func(request, *args, **kwargs)

    return wrapper


def student_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not hasattr(request.user, "studentprofile"):
            raise PermissionDenied("Само студенти имат достъп.")
        return view_func(request, *args, **kwargs)

    return wrapper
