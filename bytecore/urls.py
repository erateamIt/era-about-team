from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from core.sitemaps import ProjectSitemap, ServiceSitemap, StaticPageSitemap

sitemaps = {
    "static": StaticPageSitemap,
    "services": ServiceSitemap,
    "projects": ProjectSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("dashboard/", include("dashboard.urls")),
    path("", include("core.urls")),
    path("", include("contact.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "core.views.page_not_found"
handler500 = "core.views.server_error"
