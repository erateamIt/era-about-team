from django.db import models
from django.utils.text import slugify

from core.i18n import TranslatableMixin, TranslationBase
from core.validators import validate_image_file


class Project(TranslatableMixin, models.Model):
    translation_fields = ("title", "summary", "description", "meta_title", "meta_description")
    translation_fallback_fields = ("title",)
    translation_required_fields = ("title", "summary", "description")
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    summary = models.CharField(max_length=255)
    description = models.TextField()
    cover_image = models.ImageField(
        upload_to="projects/cover/",
        blank=True,
        null=True,
        validators=[validate_image_file],
    )
    technologies = models.JSONField(default=list, blank=True)
    project_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "project"
        verbose_name_plural = "projects"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class ProjectTranslation(TranslationBase):
    project = models.ForeignKey(Project, related_name="translations", on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    summary = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        unique_together = ("project", "language")
        verbose_name = "project translation"
        verbose_name_plural = "project translations"

    def __str__(self):
        return f"{self.project_id} [{self.language}]"


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to="projects/gallery/",
        validators=[validate_image_file],
    )
    alt_text = models.CharField(max_length=150, blank=True)
    is_cover = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.project.title} image"
