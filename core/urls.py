from django.urls import path

from .views import robots_txt
from .views import (
    about,
    home,
    privacy,
    project_detail,
    project_list,
    service_detail,
    service_list,
    team,
)

app_name = "core"

urlpatterns = [
    path("", home, name="home"),
    path("robots.txt", robots_txt, name="robots"),
    path("about/", about, name="about"),
    path("services/", service_list, name="services"),
    path("services/<slug:slug>/", service_detail, name="service_detail"),
    path("projects/", project_list, name="projects"),
    path("projects/<slug:slug>/", project_detail, name="project_detail"),
    path("team/", team, name="team"),
    path("privacy/", privacy, name="privacy"),
]
