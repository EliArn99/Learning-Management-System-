from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.messages_home, name='messages_home'),
    path('inbox/', views.inbox_view, name='inbox'),
    path('sent/', views.sent_view, name='sent'),
    path('send/', views.send_message_view, name='send_message'),
]
