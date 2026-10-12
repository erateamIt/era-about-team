from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from projects.models import Project
from services.models import Service
from team.models import TeamMember


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse("sitemap"))
    return HttpResponse(
        f"User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /dashboard/\nSitemap: {sitemap_url}\n",
        content_type="text/plain",
    )


def home(request):
    services = Service.objects.filter(is_active=True).order_by("order")[:8]
    featured_projects = Project.objects.filter(is_published=True, is_featured=True).order_by("order")[:3]
    team_members = TeamMember.objects.filter(is_active=True).order_by("order")[:6]
    return render(
        request,
        "home.html",
        {
            "services": services,
            "featured_projects": featured_projects,
            "team_members": team_members,
        },
    )


def about(request):
    team_members = TeamMember.objects.filter(is_active=True).order_by("order")
    return render(request, "about.html", {"team_members": team_members})


def service_list(request):
    services = Service.objects.filter(is_active=True).order_by("order")
    return render(request, "services/list.html", {"services": services})


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True)
    related_services = Service.objects.filter(is_active=True).exclude(pk=service.pk).order_by("order")[:3]
    return render(
        request,
        "services/detail.html",
        {
            "service": service,
            "related_services": related_services,
            "og_image": (
                request.build_absolute_uri(service.cover_image.url)
                if service.cover_image
                else ""
            ),
        },
    )


def project_list(request):
    projects = Project.objects.filter(is_published=True).order_by("order")
    return render(request, "projects/list.html", {"projects": projects})


def project_detail(request, slug):
    project = get_object_or_404(
        Project.objects.prefetch_related("images"),
        slug=slug,
        is_published=True,
    )
    gallery_images = list(project.images.all())
    cover_gallery_image = next((image for image in gallery_images if image.is_cover), None)
    if cover_gallery_image:
        cover_image = cover_gallery_image.image
    elif project.cover_image:
        cover_image = project.cover_image
    elif gallery_images:
        cover_gallery_image = gallery_images[0]
        cover_image = cover_gallery_image.image
    else:
        cover_image = None
    remaining_images = [image for image in gallery_images if image.pk != getattr(cover_gallery_image, "pk", None)]
    other_projects = Project.objects.filter(is_published=True).exclude(pk=project.pk).order_by("order")[:3]
    return render(
        request,
        "projects/detail.html",
        {
            "project": project,
            "cover_image": cover_image,
            "cover_gallery_image": cover_gallery_image,
            "gallery_images": remaining_images,
            "other_projects": other_projects,
            "og_image": (
                request.build_absolute_uri(cover_image.url)
                if cover_image
                else ""
            ),
        },
    )


def privacy(request):
    return render(request, "privacy.html")


def page_not_found(request, exception=None):
    return render(request, "404.html", status=404)


def server_error(request):
    return render(request, "500.html", status=500)
