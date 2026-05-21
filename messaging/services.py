from .models import Message


def mark_message_as_read(message):
    if not message.is_read:
        Message.objects.filter(pk=message.pk, is_read=False).update(is_read=True)
        message.is_read = True

    return message


def mark_all_inbox_messages_as_read(user):
    return Message.objects.filter(
        receiver=user,
        is_read=False,
    ).update(is_read=True)


def create_message(sender, receiver, subject, content):
    return Message.objects.create(
        sender=sender,
        receiver=receiver,
        subject=subject,
        content=content,
    )


def soft_delete_message(message):
    message.deleted = True
    message.save(update_fields=["deleted"])

    return message