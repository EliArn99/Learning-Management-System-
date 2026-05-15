from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomUser, StudentProfile, TeacherProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.is_student:
        StudentProfile.objects.get_or_create(
            user=instance,
            defaults={
                "age": 18,
                "is_approved": False,
            },
        )

    elif instance.is_teacher:
        TeacherProfile.objects.get_or_create(
            user=instance,
            defaults={
                "age": 25,
                "education": "",
                "experience_years": 0,
                "is_approved": False,
            },
        )
