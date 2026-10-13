from django.conf import settings
from django.urls import translate_url
from django.utils.translation import get_language

from .translation_service import ensure_language_translation
from .models import SiteSettings
from services.models import Service


def site_settings(request):
    site_settings_obj = SiteSettings.get_instance()
    current_language = (get_language() or settings.LANGUAGE_CODE).split("-")[0]
    if (
        settings.CONTENT_TRANSLATION_ON_DEMAND
        and current_language != settings.LANGUAGE_CODE
        and request.path_info.startswith(f"/{current_language}/")
    ):
        ensure_language_translation(site_settings_obj, current_language)

    path = request.get_full_path()
    language_urls = []
    for code, name in settings.LANGUAGES:
        translated = translate_url(path, code) or f"/{code}/"
        language_urls.append(
            {
                "code": code,
                "name": name,
                "url": translated,
                "active": code == get_language(),
            }
        )
    default_url = next((item["url"] for item in language_urls if item["code"] == settings.LANGUAGE_CODE), path)
    return {
        "site_settings": site_settings_obj,
        "footer_services": Service.objects.filter(is_active=True).prefetch_related("translations").order_by("order")[:5],
        "language_urls": language_urls,
        "hreflang_default_url": request.build_absolute_uri(default_url),
    }
