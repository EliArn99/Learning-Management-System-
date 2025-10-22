from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Message
from django.contrib import messages
from django.db.models import Q

User = get_user_model()


@login_required
def messages_home(request):
    unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
    return render(request, 'messaging/messages_home.html', {'unread_count': unread_count})


@login_required
def inbox_view(request):
    inbox_messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')
    for msg in inbox_messages:
        if not msg.is_read:
            msg.is_read = True
            msg.save()
    return render(request, 'messaging/inbox.html', {'messages': inbox_messages})


@login_required
def sent_view(request):
    sent_messages = Message.objects.filter(sender=request.user).order_by('-timestamp')
    return render(request, 'messaging/sent.html', {'sent_messages': sent_messages})


@login_required
def message_detail_view(request, pk):
    message = get_object_or_404(Message, pk=pk, receiver=request.user)
    if not message.is_read:
        message.is_read = True
        message.save()
    return render(request, 'messaging/message_detail.html', {'message': message})


@login_required
def send_message_view(request):
    if request.user.is_student:
        allowed_recipients = User.objects.filter(
            is_teacher=True,
            teacherprofile__is_approved=True
        ).order_by('username')
    elif request.user.is_teacher:
        allowed_recipients = User.objects.filter(
            Q(is_student=True, studentprofile__is_approved=True) |
            Q(is_teacher=True, teacherprofile__is_approved=True)
        ).exclude(id=request.user.id).order_by('username')
    else:
        allowed_recipients = User.objects.exclude(id=request.user.id).order_by('username')

    if request.method == 'POST':
        receiver_id = request.POST.get('receiver')
        subject = request.POST.get('subject', '').strip()
        content = request.POST.get('content', '').strip()

        print(f"DEBUG: POST data - receiver: {receiver_id}, subject: {subject}, content: {content}")

        if not receiver_id:
            messages.error(request, "Моля, изберете получател.")
            return render(request, 'messaging/messaging_message.html', {'users': allowed_recipients})

        if not content:
            messages.error(request, "Моля, въведете съдържание на съобщението.")
            return render(request, 'messaging/messaging_message.html', {'users': allowed_recipients})

        try:
            receiver = User.objects.get(id=receiver_id)

            allowed_ids = list(allowed_recipients.values_list('id', flat=True))
            if receiver.id not in allowed_ids:
                messages.error(request, "Нямате право да изпращате съобщения на този потребител.")
                return render(request, 'messaging/messaging_message.html', {'users': allowed_recipients})

            message = Message.objects.create(
                sender=request.user,
                receiver=receiver,
                subject=subject,
                content=content
            )

            print(f"DEBUG: Message created with ID: {message.id}")
            messages.success(request, "Съобщението беше изпратено успешно!")

            return redirect('messaging:sent')

        except User.DoesNotExist:
            messages.error(request, "Избраният получател не съществува.")
            return render(request, 'messaging/messaging_message.html', {'users': allowed_recipients})
        except Exception as e:
            print(f"DEBUG: Error creating message: {str(e)}")
            messages.error(request, f"Възникна грешка при изпращане на съобщението: {str(e)}")
            return render(request, 'messaging/messaging_message.html', {'users': allowed_recipients})

    return render(request, 'messaging/messaging_message.html', {'users': allowed_recipients})
