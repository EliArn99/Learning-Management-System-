from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import Message

User = get_user_model()


class MessageForm(forms.ModelForm):


    class Meta:
        model = Message
        fields = ["receiver", "subject", "content"]
        widgets = {
            "receiver": forms.Select(attrs={"class": "form-control"}),
            "subject": forms.TextInput(attrs={"class": "form-control", "placeholder": "Subject"}),
            "content": forms.Textarea(attrs={"class": "form-control", "placeholder": "Type your message here...", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if not self.user:
            self.fields["receiver"].queryset = User.objects.none()
            return

        # Allowed recipients logic (same as your view, but centralized)
        if getattr(self.user, "is_student", False):
            qs = User.objects.filter(
                is_teacher=True,
                teacherprofile__is_approved=True
            )
        elif getattr(self.user, "is_teacher", False):
            qs = User.objects.filter(
                Q(is_student=True, studentprofile__is_approved=True) |
                Q(is_teacher=True, teacherprofile__is_approved=True)
            ).exclude(id=self.user.id)
        else:
            qs = User.objects.exclude(id=self.user.id)

        self.fields["receiver"].queryset = qs.order_by("username")

    def clean_receiver(self):
        receiver = self.cleaned_data.get("receiver")
        if not receiver:
            raise ValidationError("Моля, изберете получател.")
        if self.user and receiver.id == self.user.id:
            raise ValidationError("Не можете да изпратите съобщение на себе си.")
        return receiver

    def clean_content(self):
        content = (self.cleaned_data.get("content") or "").strip()
        if not content:
            raise ValidationError("Моля, въведете съдържание на съобщението.")
        return content

    def clean_subject(self):
        subject = (self.cleaned_data.get("subject") or "").strip()
        return subject
