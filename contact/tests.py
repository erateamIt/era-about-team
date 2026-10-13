from urllib.error import URLError

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.core.cache import cache
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

from .models import Lead


class ContactFormTests(TestCase):
    def setUp(self):
        cache.clear()

    @override_settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID="")
    @patch("contact.views.threading.Thread")
    def test_contact_form_renders_and_saves_a_lead(self, thread_class):
        response = self.client.get(reverse("contact:contact"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="project_type"')
        self.assertContains(response, "Web sayt")
        self.assertContains(
            response,
            'href="/uz/contact/" class="active" aria-current="page"',
        )

        response = self.client.post(
            reverse("contact:contact"),
            {
                "full_name": "Test client",
                "company": "Test company",
                "email": "client@example.test",
                "phone": "+998901234567",
                "project_type": "website",
                "message": "Sayt kerak",
            },
        )
        self.assertRedirects(response, reverse("contact:contact"))
        self.assertTrue(Lead.objects.filter(full_name="Test client", status="new").exists())

    def test_honeypot_submission_is_acknowledged_but_not_saved(self):
        response = self.client.post(
            reverse("contact:contact"),
            {
                "full_name": "Bot",
                "email": "bot@example.test",
                "message": "Spam",
                "website": "https://spam.example",
                "project_type": "website",
            },
        )
        self.assertRedirects(response, reverse("contact:contact"))
        self.assertFalse(Lead.objects.exists())

    @override_settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID="")
    @patch("contact.views.threading.Thread")
    def test_phone_accepts_uzbek_format_and_rejects_other_prefixes(self, thread_class):
        base_data = {
            "full_name": "Phone test",
            "email": "phone@example.test",
            "message": "Hello",
            "project_type": "website",
        }
        valid_response = self.client.post(
            reverse("contact:contact"),
            {**base_data, "phone": "+998 (90) 123-45-67"},
        )
        self.assertRedirects(valid_response, reverse("contact:contact"))
        self.assertTrue(Lead.objects.filter(phone="+998901234567").exists())

        invalid_response = self.client.post(
            reverse("contact:contact"),
            {**base_data, "email": "other@example.test", "phone": "+1 415 555 0100"},
        )
        self.assertEqual(invalid_response.status_code, 200)
        self.assertContains(invalid_response, "Telefon raqami +998 bilan boshlanib")
        self.assertFalse(Lead.objects.filter(email="other@example.test").exists())

    @override_settings(TELEGRAM_BOT_TOKEN="token", TELEGRAM_CHAT_ID="chat")
    @patch("contact.views.threading.Thread")
    def test_telegram_notification_runs_in_background(self, thread_class):
        response = self.client.post(
            reverse("contact:contact"),
            {
                "full_name": "Async client",
                "email": "async@example.test",
                "message": "Please call",
                "phone": "",
                "project_type": "website",
            },
        )
        lead = Lead.objects.get(email="async@example.test")
        self.assertRedirects(response, reverse("contact:contact"))
        thread_class.assert_called_once()
        thread_class.return_value.start.assert_called_once()
        self.assertEqual(thread_class.call_args.kwargs["args"], (lead.pk,))

    @patch("contact.views.threading.Thread")
    def test_contact_submission_rate_limit_is_three_per_five_minutes(self, thread_class):
        payload = {
            "full_name": "Rate client",
            "email": "rate@example.test",
            "message": "Please call",
            "phone": "",
            "project_type": "website",
        }
        for _ in range(3):
            self.assertEqual(self.client.post(reverse("contact:contact"), payload).status_code, 302)
        response = self.client.post(
            reverse("contact:contact"),
            {**payload, "email": "fourth@example.test"},
        )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(Lead.objects.count(), 3)
        self.assertEqual(thread_class.call_count, 3)

    @override_settings(TELEGRAM_BOT_TOKEN="token", TELEGRAM_CHAT_ID="chat")
    @patch("contact.views.request.urlopen", side_effect=URLError("offline"))
    def test_telegram_failures_are_logged(self, urlopen):
        lead = Lead.objects.create(
            full_name="Logged client",
            email="logged@example.test",
            message="Test",
        )
        with self.assertLogs("contact.views", level="ERROR") as log_messages:
            from .views import send_telegram_notification

            self.assertFalse(send_telegram_notification(lead.pk))
        self.assertIn("Failed to send Telegram notification", log_messages.output[0])


class LeadRenameMigrationTests(TransactionTestCase):
    migrate_from = ("contact", "0001_initial")
    migrate_to = ("contact", "0002_lead_delete_contactrequest")

    def test_existing_contact_requests_are_preserved_and_statuses_mapped(self):
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        old_apps = executor.loader.project_state([self.migrate_from]).apps
        OldLead = old_apps.get_model("contact", "ContactRequest")
        OldLead.objects.create(
            full_name="Existing customer",
            email="existing@example.test",
            message="Existing request",
            status="answered",
        )

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        new_apps = executor.loader.project_state([self.migrate_to]).apps
        LeadModel = new_apps.get_model("contact", "Lead")
        migrated = LeadModel.objects.get(email="existing@example.test")
        self.assertEqual(migrated.full_name, "Existing customer")
        self.assertEqual(migrated.status, "negotiating")
