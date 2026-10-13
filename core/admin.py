from django.contrib import admin

from .models import SiteSettings, SiteSettingsTranslation


class TranslationStatusMixin:
    def translation_status(self, obj):
        statuses = {
            item["language"].lower(): item["status"]
            for item in obj.translation_statuses()
        }
        return " ".join(
            code.upper() if statuses[code] == "complete" else f"{code.upper()}–"
            for code in ("uz", "ru", "tr", "en")
        )

    translation_status.short_description = "Tarjimalar"


class TranslationInlineMixin:
    readonly_fields = ("status", "is_manual", "last_error", "translated_at")


class SiteSettingsTranslationInline(TranslationInlineMixin, admin.TabularInline):
    model = SiteSettingsTranslation
    fields = (
        "language",
        "tagline",
        "footer_text",
        "address",
        "meta_title",
        "meta_description",
        "status",
        "is_manual",
        "last_error",
        "translated_at",
    )
    extra = 3
    max_num = 4


@admin.register(SiteSettings)
class SiteSettingsAdmin(TranslationStatusMixin, admin.ModelAdmin):
    list_display = ("company_name", "phone", "email", "translation_status")
    inlines = [SiteSettingsTranslationInline]
    fieldsets = (
        ("Kompaniya (UZ / asosiy)", {"fields": ("company_name", "tagline", "footer_text", "logo", "favicon")}),
        ("Aloqa", {"fields": ("phone", "email", "address", "telegram_username", "instagram_url", "linkedin_url")}),
        ("Bosh sahifa statistikasi", {"fields": ("experience_stat", "projects_stat", "support_stat")}),
        ("SEO (UZ / asosiy)", {"fields": ("meta_title", "meta_description")}),
    )
