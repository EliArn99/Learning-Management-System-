from django.shortcuts import render

# Create your views here.

def messages_home(request):
    return render(request, 'messaging/messages_home.html')

def inbox_view(request):
    return render(request, 'messaging/inbox.html')

def sent_view(request):
    return render(request, 'messaging/sent.html')

def send_message_view(request):
    return render(request, 'messaging/send_message.html')
