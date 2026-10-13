from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from core.sitemaps import ProjectSitemap, ServiceSitemap, StaticPageSitemap
from core.views import robots_txt

sitemaps = {
    "static": StaticPageSitemap,
    "services": ServiceSitemap,
    "projects": ProjectSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("dashboard/", include("dashboard.urls")),
]

urlpatterns += i18n_patterns(
    path("", include("core.urls")),
    path("", include("contact.urls")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "core.views.page_not_found"
handler500 = "core.views.server_error"
