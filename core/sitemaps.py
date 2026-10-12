from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from projects.models import Project
from services.models import Service


class StaticPageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    page_names = (
        "core:home",
        "core:about",
        "core:services",
        "core:projects",
        "core:privacy",
        "contact:contact",
    )

    def items(self):
        return self.page_names

    def location(self, item):
        return reverse(item)


class ServiceSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Service.objects.filter(is_active=True)

    def location(self, item):
        return reverse("core:service_detail", kwargs={"slug": item.slug})


class ProjectSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Project.objects.filter(is_published=True)

    def location(self, item):
        return reverse("core:project_detail", kwargs={"slug": item.slug})
