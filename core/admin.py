from django.contrib import admin

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("company_name", "phone", "email")
    fieldsets = (
        ("Kompaniya", {"fields": ("company_name", "tagline", "footer_text", "logo", "favicon")}),
        ("Aloqa", {"fields": ("phone", "email", "address", "telegram_username", "instagram_url", "linkedin_url")}),
        ("Bosh sahifa statistikasi", {"fields": ("experience_stat", "projects_stat", "support_stat")}),
        ("SEO", {"fields": ("meta_title", "meta_description")}),
    )
