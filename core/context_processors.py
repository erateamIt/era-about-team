from .models import SiteSettings
from services.models import Service


def site_settings(request):
    return {
        "site_settings": SiteSettings.get_instance(),
        "footer_services": Service.objects.filter(is_active=True).order_by("order")[:5],
    }
