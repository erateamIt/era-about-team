from django.contrib import admin

from .models import TeamMember


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "position", "is_active", "order")
    list_filter = ("is_active",)
