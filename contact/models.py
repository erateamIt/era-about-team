from django.db import models
from django.utils.translation import gettext_lazy as _


class Lead(models.Model):
    STATUS_CHOICES = [
        ("new", _("New")),
        ("reviewing", _("Under review")),
        ("negotiating", _("In negotiation")),
        ("in_progress", _("In progress")),
        ("completed", _("Completed")),
        ("rejected", _("Rejected")),
    ]

    PROJECT_CHOICES = [
        ("website", _("Website")),
        ("ecommerce", _("Online store")),
        ("telegram_bot", _("Telegram bot")),
        ("crm", _("CRM / automation")),
        ("api", _("API / backend")),
        ("design", _("UI/UX design")),
        ("ai", _("AI integration")),
        ("other", _("Other")),
    ]

    full_name = models.CharField(max_length=120)
    company = models.CharField(max_length=120, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    project_type = models.CharField(max_length=30, choices=PROJECT_CHOICES, default="website")
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField(auto_now_add=True)
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "contact request"
        verbose_name_plural = "contact requests"

    def __str__(self):
        return f"{self.full_name} - {self.get_project_type_display()}"


# Keep imports used by any local integrations working through the model rename.
ContactRequest = Lead
