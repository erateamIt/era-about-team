from django.contrib.auth.views import LogoutView
from django.urls import path
from django.urls import reverse_lazy

from . import views

app_name = "dashboard"

urlpatterns = [
    path("login/", views.DashboardLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page=reverse_lazy("dashboard:login")), name="logout"),
    path("", views.home, name="home"),
    path("orders/", views.lead_list, name="leads"),
    path("orders/<int:pk>/", views.lead_detail, name="lead_detail"),
    path("services/", views.service_list, name="services"),
    path("services/new/", views.service_create, name="service_create"),
    path("services/<int:pk>/edit/", views.service_edit, name="service_edit"),
    path("services/<int:pk>/translate/", views.service_translate, name="service_translate"),
    path("services/<int:pk>/toggle/", views.service_toggle, name="service_toggle"),
    path("services/<int:pk>/delete/", views.service_delete, name="service_delete"),
    path("projects/", views.project_list, name="projects"),
    path("projects/new/", views.project_create, name="project_create"),
    path("projects/<int:pk>/edit/", views.project_edit, name="project_edit"),
    path("projects/<int:pk>/translate/", views.project_translate, name="project_translate"),
    path("projects/<int:pk>/toggle/", views.project_toggle, name="project_toggle"),
    path("projects/<int:pk>/delete/", views.project_delete, name="project_delete"),
    path("team/", views.team_list, name="team"),
    path("team/new/", views.team_create, name="team_create"),
    path("team/<int:pk>/edit/", views.team_edit, name="team_edit"),
    path("team/<int:pk>/translate/", views.team_translate, name="team_translate"),
    path("team/<int:pk>/toggle/", views.team_toggle, name="team_toggle"),
    path("team/<int:pk>/delete/", views.team_delete, name="team_delete"),
    path("settings/", views.site_settings, name="settings"),
]
