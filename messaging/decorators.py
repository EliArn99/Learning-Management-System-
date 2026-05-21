from functools import wraps

from django.core.exceptions import PermissionDenied

from .selectors import get_received_message_for_user


def message_receiver_required(view_func):
    @wraps(view_func)
    def wrapper(request, pk, *args, **kwargs):
        message = get_received_message_for_user(request.user, pk)

        if not message:
            raise PermissionDenied("Нямате достъп до това съобщение.")

        request.message_obj = message
        return view_func(request, pk, *args, **kwargs)

    return wrapper