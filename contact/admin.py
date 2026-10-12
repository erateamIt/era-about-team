from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "project_type", "status", "created_at")
    list_filter = ("status", "project_type")
    search_fields = ("full_name", "email", "phone", "company")
