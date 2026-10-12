from django.db import models


class Lead(models.Model):
    STATUS_CHOICES = [
        ("new", "Yangi"),
        ("reviewing", "Ko'rib chiqilmoqda"),
        ("negotiating", "Muzokarada"),
        ("in_progress", "Bajarilmoqda"),
        ("completed", "Yakunlandi"),
        ("rejected", "Rad etildi"),
    ]

    PROJECT_CHOICES = [
        ("website", "Web sayt"),
        ("ecommerce", "Internet-do'kon"),
        ("telegram_bot", "Telegram bot"),
        ("crm", "CRM / avtomatlashtirish"),
        ("api", "API / backend"),
        ("design", "UI/UX dizayn"),
        ("ai", "AI integratsiyasi"),
        ("other", "Boshqa"),
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
