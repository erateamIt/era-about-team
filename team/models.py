from django.db import models

from core.i18n import TranslatableMixin, TranslationBase
from core.validators import validate_image_file


class TeamMember(TranslatableMixin, models.Model):
    translation_fields = ("position", "bio")
    translation_fallback_fields = ("position",)
    translation_required_fields = ("position", "bio")
    name = models.CharField(max_length=120)
    position = models.CharField(max_length=120)
    bio = models.TextField()
    photo = models.ImageField(upload_to="team/", blank=True, null=True, validators=[validate_image_file])
    telegram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "team member"
        verbose_name_plural = "team members"

    def __str__(self):
        return self.name


class TeamMemberTranslation(TranslationBase):
    member = models.ForeignKey(TeamMember, related_name="translations", on_delete=models.CASCADE)
    position = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        unique_together = ("member", "language")
        verbose_name = "team member translation"
        verbose_name_plural = "team member translations"

    def __str__(self):
        return f"{self.member_id} [{self.language}]"
