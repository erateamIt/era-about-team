import html
import json
import logging
import threading
from hashlib import sha256
from urllib import request
from urllib.error import URLError

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.db import close_old_connections
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .forms import ContactForm
from .models import Lead


logger = logging.getLogger(__name__)
CONTACT_RATE_LIMIT = 3
CONTACT_RATE_WINDOW = 5 * 60


def _contact_rate_limit_key(request):
    address = request.META.get("REMOTE_ADDR", "unknown")
    address_hash = sha256(address.encode("utf-8")).hexdigest()
    return f"contact-submission:{address_hash}"


def _consume_contact_submission(key):
    if cache.add(key, 1, timeout=CONTACT_RATE_WINDOW):
        return 1
    try:
        return cache.incr(key)
    except ValueError:
        cache.add(key, 1, timeout=CONTACT_RATE_WINDOW)
        return cache.get(key, 1)


def send_telegram_notification(lead_id):
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "")
    if not bot_token or not chat_id:
        return False

    try:
        close_old_connections()
        lead = Lead.objects.get(pk=lead_id)
        text = (
            "<b>Yangi buyurtma</b>\n"
            f"<b>Ism:</b> {html.escape(lead.full_name)}\n"
            f"<b>Kompaniya:</b> {html.escape(lead.company or '-')}\n"
            f"<b>Email:</b> {html.escape(lead.email)}\n"
            f"<b>Telefon:</b> {html.escape(lead.phone or '-')}\n"
            f"<b>Loyiha turi:</b> {html.escape(lead.get_project_type_display())}\n"
            f"<b>Xabar:</b> {html.escape(lead.message)}"
        )
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        data = json.dumps(payload).encode("utf-8")
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        req = request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            if response.status != 200 or not result.get("ok"):
                logger.warning("Telegram notification was rejected for lead %s.", lead_id)
                return False
            return True
    except Lead.DoesNotExist:
        logger.error("Cannot send Telegram notification: lead %s no longer exists.", lead_id)
    except (URLError, OSError, TimeoutError, json.JSONDecodeError):
        logger.exception("Failed to send Telegram notification for lead %s.", lead_id)
    finally:
        close_old_connections()
    return False


def _start_telegram_notification(lead_id):
    thread = threading.Thread(
        target=send_telegram_notification,
        args=(lead_id,),
        name=f"telegram-lead-{lead_id}",
        daemon=True,
    )
    try:
        thread.start()
    except RuntimeError:
        logger.exception("Failed to start Telegram notification thread for lead %s.", lead_id)


def contact_page(request):
    if request.method == "POST":
        rate_limit_key = _contact_rate_limit_key(request)
        if cache.get(rate_limit_key, 0) >= CONTACT_RATE_LIMIT:
            return HttpResponse(
                "Juda ko‘p so‘rov yuborildi. 5 daqiqadan so‘ng qayta urinib ko‘ring.",
                status=429,
                content_type="text/plain; charset=utf-8",
            )
        form = ContactForm(request.POST)
        if form.is_valid():
            if form.cleaned_data["website"]:
                messages.success(request, "Murojaatingiz qabul qilindi. Tez orada biz bilan bog‘lanamiz.")
                return redirect("contact:contact")
            if _consume_contact_submission(rate_limit_key) > CONTACT_RATE_LIMIT:
                return HttpResponse(
                    "Juda ko‘p so‘rov yuborildi. 5 daqiqadan so‘ng qayta urinib ko‘ring.",
                    status=429,
                    content_type="text/plain; charset=utf-8",
                )
            lead = form.save()
            _start_telegram_notification(lead.pk)
            messages.success(request, "Murojaatingiz qabul qilindi. Tez orada biz bilan bog‘lanamiz.")
            return redirect("contact:contact")
    else:
        form = ContactForm()

    return render(request, "contact.html", {"form": form})
