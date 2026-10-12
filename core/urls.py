from django.urls import path

from .views import (
    about,
    home,
    privacy,
    project_detail,
    project_list,
    robots_txt,
    service_detail,
    service_list,
)

app_name = "core"

urlpatterns = [
    path("", home, name="home"),
    path("about/", about, name="about"),
    path("services/", service_list, name="services"),
    path("services/<slug:slug>/", service_detail, name="service_detail"),
    path("projects/", project_list, name="projects"),
    path("projects/<slug:slug>/", project_detail, name="project_detail"),
    path("privacy/", privacy, name="privacy"),
    path("robots.txt", robots_txt, name="robots"),
]
