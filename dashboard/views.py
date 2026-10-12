from functools import wraps
from hashlib import sha256

from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from contact.models import Lead
from core.models import SiteSettings
from projects.models import Project
from services.models import Service
from team.models import TeamMember

from .decorators import staff_required
from .forms import (
    LeadFilterForm,
    LeadStatusForm,
    ProjectForm,
    ServiceForm,
    SiteSettingsForm,
    TeamMemberForm,
)


class DashboardLoginView(LoginView):
    template_name = "dashboard/login.html"
    redirect_authenticated_user = False
    next_page = reverse_lazy("dashboard:home")

    def dispatch(self, request, *args, **kwargs):
        self.rate_limit_key = ""
        if request.method == "POST":
            address = request.META.get("REMOTE_ADDR", "unknown")
            address_hash = sha256(address.encode("utf-8")).hexdigest()
            self.rate_limit_key = f"dashboard-login:{address_hash}"
            if cache.get(self.rate_limit_key, 0) >= 10:
                return render(
                    request,
                    self.template_name,
                    {
                        "form": AuthenticationForm(request),
                        "rate_limited": True,
                    },
                    status=429,
                )
            if not cache.add(self.rate_limit_key, 1, timeout=900):
                try:
                    cache.incr(self.rate_limit_key)
                except ValueError:
                    cache.add(self.rate_limit_key, 1, timeout=900)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not form.get_user().is_staff:
            form.add_error(None, "Dashboard faqat staff foydalanuvchilar uchun.")
            return self.form_invalid(form)
        if self.rate_limit_key:
            cache.delete(self.rate_limit_key)
        return super().form_valid(form)

    def get_success_url(self):
        return self.get_redirect_url() or str(self.next_page)


def has_permission(permission):
    def decorator(view_func):
        @wraps(view_func)
        @staff_required
        def wrapped(request, *args, **kwargs):
            if not request.user.has_perm(permission):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def _can(user, permission):
    return user.has_perm(permission)


@staff_required
def home(request):
    can_view_leads = _can(request.user, "contact.view_lead")
    stats = {
        "total_leads": Lead.objects.count() if can_view_leads else None,
        "new_leads": Lead.objects.filter(status="new").count() if can_view_leads else None,
        "reviewing_leads": Lead.objects.filter(status="reviewing").count() if can_view_leads else None,
        "completed_projects": Project.objects.filter(is_published=True).count()
        if _can(request.user, "projects.view_project")
        else None,
        "active_services": Service.objects.filter(is_active=True).count()
        if _can(request.user, "services.view_service")
        else None,
        "team_members": TeamMember.objects.filter(is_active=True).count()
        if _can(request.user, "team.view_teammember")
        else None,
    }
    recent_leads = Lead.objects.order_by("-created_at")[:8] if can_view_leads else Lead.objects.none()
    return render(request, "dashboard/home.html", {"stats": stats, "recent_leads": recent_leads})


@has_permission("contact.view_lead")
def lead_list(request):
    filter_form = LeadFilterForm(request.GET or None)
    leads = Lead.objects.all()
    if filter_form.is_valid():
        search = filter_form.cleaned_data["q"].strip()
        if search:
            leads = leads.filter(Q(full_name__icontains=search) | Q(phone__icontains=search))
        if filter_form.cleaned_data["status"]:
            leads = leads.filter(status=filter_form.cleaned_data["status"])
        if filter_form.cleaned_data["date_from"]:
            leads = leads.filter(created_at__date__gte=filter_form.cleaned_data["date_from"])
        if filter_form.cleaned_data["date_to"]:
            leads = leads.filter(created_at__date__lte=filter_form.cleaned_data["date_to"])

    page_obj = Paginator(leads, 20).get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(
        request,
        "dashboard/leads/list.html",
        {
            "filter_form": filter_form,
            "page_obj": page_obj,
            "filter_query": query_params.urlencode(),
        },
    )


@staff_required
def lead_detail(request, pk):
    if not request.user.has_perm("contact.view_lead"):
        raise PermissionDenied
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == "POST":
        if not request.user.has_perm("contact.change_lead"):
            raise PermissionDenied
        form = LeadStatusForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, "Buyurtma yangilandi.")
            return redirect("dashboard:lead_detail", pk=lead.pk)
    else:
        form = LeadStatusForm(instance=lead)
    return render(request, "dashboard/leads/detail.html", {"lead": lead, "form": form})


@has_permission("services.view_service")
def service_list(request):
    services = Service.objects.all()
    search = request.GET.get("q", "").strip()
    active = request.GET.get("active", "")
    if search:
        services = services.filter(Q(title__icontains=search) | Q(slug__icontains=search))
    if active in {"true", "false"}:
        services = services.filter(is_active=(active == "true"))
    page_obj = Paginator(services, 20).get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(
        request,
        "dashboard/services/list.html",
        {"page_obj": page_obj, "filter_query": query_params.urlencode()},
    )


@has_permission("services.add_service")
def service_create(request):
    return _model_form(request, ServiceForm, "dashboard:services", "Xizmat qo‘shildi.")


@has_permission("services.change_service")
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    return _model_form(request, ServiceForm, "dashboard:services", "Xizmat saqlandi.", service)


@has_permission("services.change_service")
@require_POST
def service_toggle(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.is_active = not service.is_active
    service.save(update_fields=["is_active", "updated_at"])
    messages.success(request, "Xizmat holati yangilandi.")
    return redirect("dashboard:services")


@has_permission("services.delete_service")
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        service.delete()
        messages.success(request, "Xizmat o‘chirildi.")
        return redirect("dashboard:services")
    return render(request, "dashboard/confirm_delete.html", {"object": service, "cancel_url": "dashboard:services"})


@has_permission("projects.view_project")
def project_list(request):
    projects = Project.objects.all()
    search = request.GET.get("q", "").strip()
    published = request.GET.get("published", "")
    if search:
        projects = projects.filter(Q(title__icontains=search) | Q(slug__icontains=search))
    if published in {"true", "false"}:
        projects = projects.filter(is_published=(published == "true"))
    page_obj = Paginator(projects, 20).get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(
        request,
        "dashboard/projects/list.html",
        {"page_obj": page_obj, "filter_query": query_params.urlencode()},
    )


@has_permission("projects.add_project")
def project_create(request):
    return _model_form(request, ProjectForm, "dashboard:projects", "Loyiha qo‘shildi.")


@has_permission("projects.change_project")
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return _model_form(request, ProjectForm, "dashboard:projects", "Loyiha saqlandi.", project)


@has_permission("projects.change_project")
@require_POST
def project_toggle(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project.is_published = not project.is_published
    project.save(update_fields=["is_published", "updated_at"])
    messages.success(request, "Loyiha nashr holati yangilandi.")
    return redirect("dashboard:projects")


@has_permission("projects.delete_project")
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == "POST":
        project.delete()
        messages.success(request, "Loyiha o‘chirildi.")
        return redirect("dashboard:projects")
    return render(request, "dashboard/confirm_delete.html", {"object": project, "cancel_url": "dashboard:projects"})


@has_permission("team.view_teammember")
def team_list(request):
    members = TeamMember.objects.all()
    search = request.GET.get("q", "").strip()
    active = request.GET.get("active", "")
    if search:
        members = members.filter(Q(name__icontains=search) | Q(position__icontains=search))
    if active in {"true", "false"}:
        members = members.filter(is_active=(active == "true"))
    page_obj = Paginator(members, 20).get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(
        request,
        "dashboard/team/list.html",
        {"page_obj": page_obj, "filter_query": query_params.urlencode()},
    )


@has_permission("team.add_teammember")
def team_create(request):
    return _model_form(request, TeamMemberForm, "dashboard:team", "Jamoa a’zosi qo‘shildi.")


@has_permission("team.change_teammember")
def team_edit(request, pk):
    member = get_object_or_404(TeamMember, pk=pk)
    return _model_form(request, TeamMemberForm, "dashboard:team", "Jamoa a’zosi saqlandi.", member)


@has_permission("team.change_teammember")
@require_POST
def team_toggle(request, pk):
    member = get_object_or_404(TeamMember, pk=pk)
    member.is_active = not member.is_active
    member.save(update_fields=["is_active", "updated_at"])
    messages.success(request, "Jamoa a’zosi holati yangilandi.")
    return redirect("dashboard:team")


@has_permission("team.delete_teammember")
def team_delete(request, pk):
    member = get_object_or_404(TeamMember, pk=pk)
    if request.method == "POST":
        member.delete()
        messages.success(request, "Jamoa a’zosi o‘chirildi.")
        return redirect("dashboard:team")
    return render(request, "dashboard/confirm_delete.html", {"object": member, "cancel_url": "dashboard:team"})


@has_permission("core.change_sitesettings")
def site_settings(request):
    settings_obj = SiteSettings.get_instance()
    return _model_form(request, SiteSettingsForm, "dashboard:settings", "Sayt sozlamalari saqlandi.", settings_obj)


def _model_form(request, form_class, success_url, success_message, instance=None):
    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, success_message)
        return redirect(success_url)
    return render(
        request,
        "dashboard/form.html",
        {
            "form": form,
            "object": instance,
            "cancel_url": success_url,
            "title": "Tahrirlash" if instance else "Yangi ma’lumot",
        },
    )
