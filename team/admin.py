from django.contrib import admin

from core.admin import TranslationInlineMixin, TranslationStatusMixin
from .models import TeamMember, TeamMemberTranslation


class TeamMemberTranslationInline(TranslationInlineMixin, admin.TabularInline):
    model = TeamMemberTranslation
    fields = ("language", "position", "bio", "status", "is_manual", "last_error", "translated_at")
    extra = 3
    max_num = 4


@admin.register(TeamMember)
class TeamMemberAdmin(TranslationStatusMixin, admin.ModelAdmin):
    list_display = ("name", "position", "is_active", "order", "translation_status")
    list_filter = ("is_active",)
    inlines = [TeamMemberTranslationInline]
