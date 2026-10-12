from django.db import models

from .validators import validate_image_file


class SiteSettings(models.Model):
    company_name = models.CharField(max_length=150, default="ByteCore")
    tagline = models.CharField(max_length=220, default="IT solutions for ambitious businesses")
    footer_text = models.CharField(max_length=255, blank=True, default="Raqamli kelajagingiz uchun ishonchli hamkor.")
    phone = models.CharField(max_length=32, default="+998 90 000 00 00")
    email = models.EmailField(default="hello@bytecore.uz")
    address = models.CharField(max_length=200, default="Tashkent, Uzbekistan")
    telegram_username = models.CharField(max_length=64, blank=True, default="bytecore_uz")
    instagram_url = models.URLField(blank=True, default="https://instagram.com")
    linkedin_url = models.URLField(blank=True, default="https://linkedin.com")
    experience_stat = models.CharField(
        max_length=32,
        blank=True,
        help_text="Tajribani ifodalovchi matn, masalan: 8+ yil. Bo‘sh bo‘lsa ko‘rsatilmaydi.",
    )
    projects_stat = models.CharField(
        max_length=32,
        blank=True,
        help_text="Loyihalar soni, masalan: 40+. Bo‘sh bo‘lsa ko‘rsatilmaydi.",
    )
    support_stat = models.CharField(
        max_length=32,
        blank=True,
        help_text="Qo‘llab-quvvatlash vaqti, masalan: 24/7. Bo‘sh bo‘lsa ko‘rsatilmaydi.",
    )
    logo_svg = models.TextField(blank=True, default="<svg viewBox='0 0 140 32' ...>ByteCore</svg>")
    logo = models.ImageField(upload_to="site/", blank=True, null=True, validators=[validate_image_file])
    favicon = models.ImageField(upload_to="site/", blank=True, null=True, validators=[validate_image_file])
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        verbose_name = "site settings"
        verbose_name_plural = "site settings"

    def __str__(self):
        return self.company_name

    @classmethod
    def get_instance(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
