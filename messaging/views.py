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
    # Може да маркирате съобщенията като прочетени, когато потребителят ги види
    # for msg in inbox_messages:
    #     if not msg.is_read:
    #         msg.is_read = True
    #         msg.save()
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
    # Филтрирайте потребителите въз основа на ролята на текущия потребител,
    # използвайки is_student и is_teacher булеви полета.
    if request.user.is_student:
        # Студентът може да изпраща съобщения само на одобрени преподаватели
        allowed_recipients = User.objects.filter(
            is_teacher=True,
            teacherprofile__is_approved=True
        ).order_by('username')
    elif request.user.is_teacher:
        # Преподавателят може да изпраща съобщения на всички одобрени студенти
        # и други одобрени преподаватели (без себе си)
        allowed_recipients = User.objects.filter(
            Q(is_student=True, studentprofile__is_approved=True) |
            Q(is_teacher=True, teacherprofile__is_approved=True)
        ).exclude(id=request.user.id).order_by('username')
        # Ако преподавателите могат да пишат само на студенти, използвайте:
        # allowed_recipients = User.objects.filter(
        #     is_student=True,
        #     studentprofile__is_approved=True
        # ).order_by('username')
    else:
        # За други потребители (напр. администратор), може да изпращат до всички
        allowed_recipients = User.objects.exclude(id=request.user.id).order_by('username')


    if request.method == 'POST':
        receiver_id = request.POST.get('receiver')
        subject = request.POST.get('subject', '')
        content = request.POST.get('content')

        try:
            receiver = User.objects.get(id=receiver_id)
            # Допълнителна проверка: Уверете се, че избраният получател е сред разрешените
            # Това е важно, за да се предотврати ръчно въвеждане на ID от недобросъвестен потребител
            # Проверяваме `id` на получателя, защото `allowed_recipients` е QuerySet от User обекти
            if receiver.id not in allowed_recipients.values_list('id', flat=True):
                messages.error(request, "Нямате право да изпращате съобщения на този потребител.")
                return redirect('Messaging_message') # Използвайте правилното име на URL

            Message.objects.create(
                sender=request.user,
                receiver=receiver,
                subject=subject,
                content=content
            )
            messages.success(request, "Съобщението беше изпратено успешно.")
            return redirect('messaging:sent')
        except User.DoesNotExist:
            messages.error(request, "Избраният получател не съществува.")
            return redirect('Messaging_message') # Използвайте правилното име на URL

    return render(request, 'messaging/messaging_message.html', {'users': allowed_recipients})
