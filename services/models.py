from django.db import models
from django.utils.text import slugify

from core.validators import validate_image_file


class Service(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.CharField(max_length=255)
    description = models.TextField()
    icon = models.CharField(max_length=64, default="sparkles")
    cover_image = models.ImageField(upload_to="services/", blank=True, null=True, validators=[validate_image_file])
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "service"
        verbose_name_plural = "services"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
