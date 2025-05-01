from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Message
from django.contrib import messages


# Create your views here.

@login_required
def messages_home(request):
    unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
    return render(request, 'messaging/messages_home.html', {'unread_count': unread_count})
@login_required
def inbox_view(request):
    inbox_messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')
    return render(request, 'messaging/inbox.html', {'messages': inbox_messages})

@login_required
def sent_view(request):
    sent_messages = Message.objects.filter(sender=request.user).order_by('-timestamp')
    return render(request, 'messaging/sent.html', {'sent_messages': sent_messages})


@login_required
def send_message_view(request):
    User = get_user_model()
    users = User.objects.exclude(id=request.user.id)

    if request.method == 'POST':
        receiver_id = request.POST.get('receiver')
        subject = request.POST.get('subject', '')
        content = request.POST.get('content')

        receiver = User.objects.get(id=receiver_id)
        Message.objects.create(
            sender=request.user,
            receiver=receiver,
            subject=subject,
            content=content
        )
        messages.success(request, "Съобщението беше изпратено успешно.")
        return redirect('messaging:sent')

    return render(request, 'messaging/send_message.html', {'users': users})
