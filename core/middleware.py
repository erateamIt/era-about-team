from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import translation


EXEMPT_PREFIXES = (
    "admin",
    "dashboard",
    "static",
    "media",
    "i18n",
    "sitemap.xml",
    "robots.txt",
)


class EnsureLanguagePrefixMiddleware:
    """Send public pages without a language prefix to /uz/, /ru/, /tr/ or /en/."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.language_codes = {code for code, _ in settings.LANGUAGES}

    def __call__(self, request):
        path = request.path_info or "/"
        stripped = path.lstrip("/")
        first = stripped.split("/", 1)[0] if stripped else ""
        if request.method != "GET" or first in EXEMPT_PREFIXES:
            return self.get_response(request)

        if first in self.language_codes:
            language = first
        else:
            language = translation.get_language_from_request(request)
            if language not in self.language_codes:
                language = settings.LANGUAGE_CODE
            target = f"/{language}{path}"
            if request.META.get("QUERY_STRING"):
                target = f"{target}?{request.META['QUERY_STRING']}"
            return HttpResponseRedirect(target)

        response = self.get_response(request)
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            language,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
        )
        return response
