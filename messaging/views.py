from django.contrib import messages as flash_messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Message
from .forms import MessageForm


@login_required
def messages_home(request):
    unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
    return render(request, "messaging/messages_home.html", {"unread_count": unread_count})


@login_required
def inbox_view(request):
    inbox_qs = (
        Message.objects.filter(receiver=request.user)
        .select_related("sender", "receiver")
        .order_by("-timestamp")
    )

    inbox_qs.filter(is_read=False).update(is_read=True)

    return render(request, "messaging/inbox.html", {"messages": inbox_qs})


@login_required
def sent_view(request):
    sent_qs = (
        Message.objects.filter(sender=request.user)
        .select_related("sender", "receiver")
        .order_by("-timestamp")
    )
    return render(request, "messaging/sent.html", {"sent_messages": sent_qs})


@login_required
def message_detail_view(request, pk):
    message = get_object_or_404(
        Message.objects.select_related("sender", "receiver"),
        pk=pk,
        receiver=request.user,
    )

    if not message.is_read:
        Message.objects.filter(pk=message.pk, receiver=request.user, is_read=False).update(is_read=True)
        message.is_read = True  # keep instance consistent

    return render(request, "messaging/message_detail.html", {"message": message})


@login_required
def send_message_view(request):
    if request.method == "POST":
        form = MessageForm(request.POST, user=request.user)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.save()
            flash_messages.success(request, "Съобщението беше изпратено успешно!")
            return redirect("messaging:sent")
        flash_messages.error(request, "Моля, коригирайте грешките във формата.")
    else:
        form = MessageForm(user=request.user)

    return render(request, "messaging/messaging_message.html", {"form": form})
