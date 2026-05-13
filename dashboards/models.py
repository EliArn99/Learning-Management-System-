from django.conf import settings
from django.db import models
from django.urls import reverse


class DashboardNotification(models.Model):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"

    LEVEL_CHOICES = [
        (INFO, "Info"),
        (SUCCESS, "Success"),
        (WARNING, "Warning"),
        (DANGER, "Danger"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard_notifications",
    )
    title = models.CharField(max_length=120)
    message = models.TextField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default=INFO)
    url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.user}"

    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=["is_read"])
