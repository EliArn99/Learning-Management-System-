# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import CustomUser, StudentProfile, TeacherProfile
#
#
# @receiver(post_save, sender=CustomUser)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         if instance.is_staff:
#             StudentProfile.objects.create(user=instance)
#         elif instance.is_teacher:
#             TeacherProfile.objects.create(user=instance)
