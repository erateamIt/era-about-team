from django.contrib import admin

from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "order")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("title",)}
