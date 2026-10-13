from django.contrib import admin
from django import forms

from core.admin import TranslationInlineMixin, TranslationStatusMixin
from .models import Project, ProjectImage, ProjectTranslation


class ProjectAdminForm(forms.ModelForm):
    technologies = forms.CharField(
        label="Texnologiyalar",
        required=False,
        help_text="Texnologiyalarni vergul bilan ajrating.",
    )

    class Meta:
        model = Project
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["technologies"].initial = ", ".join(self.instance.technologies or [])

    def clean_technologies(self):
        value = self.cleaned_data["technologies"]
        return [technology.strip() for technology in value.split(",") if technology.strip()]


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1


class ProjectTranslationInline(TranslationInlineMixin, admin.TabularInline):
    model = ProjectTranslation
    fields = (
        "language",
        "title",
        "summary",
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


@admin.register(Project)
class ProjectAdmin(TranslationStatusMixin, admin.ModelAdmin):
    form = ProjectAdminForm
    list_display = ("title", "is_featured", "is_published", "order", "translation_status")
    list_filter = ("is_featured", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProjectTranslationInline, ProjectImageInline]
