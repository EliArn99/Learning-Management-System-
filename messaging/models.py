from django.db import models
from users.models import CustomUser


class MessageManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)

class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    subject = models.CharField(max_length=255, blank=True, null=True)
    deleted = models.BooleanField(default=False)

    objects = MessageManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username} - {self.content[:50]}... at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
