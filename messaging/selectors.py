from .models import Message


def inbox_messages_for_user(user):
    return (
        Message.objects.filter(receiver=user)
        .select_related("sender", "receiver")
        .order_by("-timestamp")
    )


def sent_messages_for_user(user):
    return (
        Message.objects.filter(sender=user)
        .select_related("sender", "receiver")
        .order_by("-timestamp")
    )


def unread_messages_for_user(user):
    return Message.objects.filter(receiver=user, is_read=False)


def unread_count_for_user(user) -> int:
    return unread_messages_for_user(user).count()


def get_received_message_for_user(user, pk):
    return (
        Message.objects.select_related("sender", "receiver")
        .filter(pk=pk, receiver=user)
        .first()
    )


def get_message_owned_by_user(user, pk):
    return (
        Message.objects.select_related("sender", "receiver")
        .filter(pk=pk)
        .filter(receiver=user) | Message.objects.filter(pk=pk, sender=user)
    ).first()