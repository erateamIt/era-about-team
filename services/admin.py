from django.contrib import admin

from core.admin import TranslationInlineMixin, TranslationStatusMixin
from .models import Service, ServiceTranslation


class ServiceTranslationInline(TranslationInlineMixin, admin.TabularInline):
    model = ServiceTranslation
    fields = (
        "language",
        "title",
        "short_description",
        "description",
        "meta_title",
        "meta_description",
        "status",
        "is_manual",
        "last_error",
        "translated_at",
    )
    extra = 3
    max_num = 4


@admin.register(Service)
class ServiceAdmin(TranslationStatusMixin, admin.ModelAdmin):
    list_display = ("title", "is_active", "order", "translation_status")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ServiceTranslationInline]
