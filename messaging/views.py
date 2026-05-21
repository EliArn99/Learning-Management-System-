from django.contrib import messages as flash_messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from .decorators import message_receiver_required
from .forms import MessageForm
from .selectors import (
    inbox_messages_for_user,
    sent_messages_for_user,
    unread_count_for_user,
)
from .services import (
    create_message,
    mark_all_inbox_messages_as_read,
    mark_message_as_read,
)


def paginate_queryset(request, queryset, per_page=10):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)


@login_required
def messages_home(request):
    unread_count = unread_count_for_user(request.user)

    return render(
        request,
        "messaging/messages_home.html",
        {
            "unread_count": unread_count,
        },
    )


@login_required
def inbox_view(request):
    inbox_qs = inbox_messages_for_user(request.user)
    page_obj = paginate_queryset(request, inbox_qs)

    mark_all_inbox_messages_as_read(request.user)

    return render(
        request,
        "messaging/inbox.html",
        {
            "messages": page_obj.object_list,
            "page_obj": page_obj,
        },
    )


@login_required
def sent_view(request):
    sent_qs = sent_messages_for_user(request.user)
    page_obj = paginate_queryset(request, sent_qs)

    return render(
        request,
        "messaging/sent.html",
        {
            "sent_messages": page_obj.object_list,
            "page_obj": page_obj,
        },
    )


@login_required
@message_receiver_required
def message_detail_view(request, pk):
    message = mark_message_as_read(request.message_obj)

    return render(
        request,
        "messaging/message_detail.html",
        {
            "message": message,
        },
    )


@login_required
def send_message_view(request):
    if request.method == "POST":
        form = MessageForm(request.POST, user=request.user)

        if form.is_valid():
            create_message(
                sender=request.user,
                receiver=form.cleaned_data["receiver"],
                subject=form.cleaned_data.get("subject", ""),
                content=form.cleaned_data["content"],
            )

            flash_messages.success(request, "Съобщението беше изпратено успешно!")
            return redirect("messaging:sent")

        flash_messages.error(request, "Моля, коригирайте грешките във формата.")

    else:
        form = MessageForm(user=request.user)

    return render(
        request,
        "messaging/messaging_message.html",
        {
            "form": form,
        },
    )
