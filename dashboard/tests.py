from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from contact.models import Lead
from core.models import SiteSettings
from core.translation_service import TranslationServiceError
from projects.models import Project
from services.models import Service, ServiceTranslation
from team.models import TeamMember


User = get_user_model()


class DashboardAccessTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(
            username="staff",
            password="safe-test-password",
            is_staff=True,
        )
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.test",
            password="safe-test-password",
        )

    def test_dashboard_redirects_anonymous_users_to_login(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertRedirects(
            response,
            f"{reverse('dashboard:login')}?next={reverse('dashboard:home')}",
        )

    def test_non_staff_user_cannot_access_dashboard(self):
        user = User.objects.create_user(username="member", password="safe-test-password")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("dashboard:home")).status_code, 403)

    def test_staff_without_permissions_sees_no_private_metrics(self):
        self.client.force_login(self.staff)
        lead = Lead.objects.create(full_name="Private client", email="private@example.test", message="Private")
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Buyurtmalar bo‘limiga ruxsat yo‘q")
        self.assertNotContains(response, lead.full_name)
        self.assertIsNone(response.context["stats"]["total_leads"])

    def test_staff_without_lead_permission_cannot_view_customer_data(self):
        self.client.force_login(self.staff)
        lead = Lead.objects.create(full_name="Private client", email="private@example.test", message="Private")
        self.assertEqual(self.client.get(reverse("dashboard:leads")).status_code, 403)
        self.assertEqual(
            self.client.get(reverse("dashboard:lead_detail", args=[lead.pk])).status_code,
            403,
        )

    def test_non_staff_cannot_log_in_to_dashboard(self):
        User.objects.create_user(username="member", password="safe-test-password")
        response = self.client.post(
            reverse("dashboard:login"),
            {"username": "member", "password": "safe-test-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard faqat staff foydalanuvchilar uchun.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_successful_staff_login_and_post_logout(self):
        response = self.client.post(
            reverse("dashboard:login"),
            {"username": self.staff.username, "password": "safe-test-password"},
        )
        self.assertRedirects(response, reverse("dashboard:home"))
        response = self.client.post(reverse("dashboard:logout"))
        self.assertRedirects(response, reverse("dashboard:login"))

    def test_login_is_rate_limited_per_remote_address(self):
        for _ in range(10):
            self.client.post(reverse("dashboard:login"), {"username": "invalid", "password": "invalid"})
        response = self.client.post(reverse("dashboard:login"), {"username": "invalid", "password": "invalid"})
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Kirish urinishlari limiti tugadi", status_code=429)


class DashboardDataTests(TestCase):
    def setUp(self):
        translation_patch = patch(
            "core.translation_service.translate_text",
            side_effect=lambda text, language: f"{language}:{text}",
        )
        self.mock_translation = translation_patch.start()
        self.addCleanup(translation_patch.stop)
        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@example.test",
            password="safe-test-password",
        )
        self.client.force_login(self.user)

    def test_home_statistics_are_database_counts(self):
        Lead.objects.create(full_name="New person", email="new@example.test", phone="+998901234567", message="New")
        Lead.objects.create(
            full_name="Review person",
            email="review@example.test",
            message="Review",
            status="reviewing",
        )
        Service.objects.create(
            title="Active",
            slug="active",
            short_description="Active service",
            description="Details",
            is_active=True,
        )
        Service.objects.create(
            title="Inactive",
            slug="inactive",
            short_description="Inactive service",
            description="Details",
            is_active=False,
        )
        Project.objects.create(
            title="Published",
            slug="published",
            summary="Published project",
            description="Details",
            is_published=True,
        )
        Project.objects.create(
            title="Draft",
            slug="draft",
            summary="Draft project",
            description="Details",
            is_published=False,
        )
        TeamMember.objects.create(name="Active person", position="Engineer", bio="Bio", is_active=True)
        TeamMember.objects.create(name="Inactive person", position="Engineer", bio="Bio", is_active=False)

        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["stats"],
            {
                "total_leads": 2,
                "new_leads": 1,
                "reviewing_leads": 1,
                "completed_projects": 1,
                "active_services": 1,
                "team_members": 1,
            },
        )

    def test_order_search_status_date_and_pagination(self):
        for index in range(23):
            Lead.objects.create(
                full_name=f"Client {index:02}",
                email=f"client{index}@example.test",
                phone=f"+99890000{index:04}",
                message="Test request",
                status="reviewing" if index == 0 else "new",
            )
        search = self.client.get(reverse("dashboard:leads"), {"q": "Client 00"})
        self.assertEqual(search.context["page_obj"].paginator.count, 1)
        self.assertEqual(search.context["page_obj"].object_list[0].full_name, "Client 00")

        filtered = self.client.get(reverse("dashboard:leads"), {"status": "reviewing"})
        self.assertEqual(filtered.context["page_obj"].paginator.count, 1)

        today = timezone.localdate().isoformat()
        dated = self.client.get(reverse("dashboard:leads"), {"date_from": today, "date_to": today})
        self.assertEqual(dated.context["page_obj"].paginator.count, 23)

        page = self.client.get(reverse("dashboard:leads"), {"page": 2})
        self.assertEqual(page.context["page_obj"].number, 2)
        self.assertEqual(len(page.context["page_obj"].object_list), 3)

    def test_lead_status_update_requires_post_and_saves_validated_choice(self):
        lead = Lead.objects.create(full_name="A client", email="a@example.test", message="Help")
        detail_url = reverse("dashboard:lead_detail", args=[lead.pk])
        self.assertEqual(self.client.get(detail_url).status_code, 200)
        response = self.client.post(detail_url, {"status": "negotiating", "admin_notes": "Bog‘lanildi"})
        self.assertRedirects(response, detail_url)
        lead.refresh_from_db()
        self.assertEqual(lead.status, "negotiating")
        self.assertEqual(lead.admin_notes, "Bog‘lanildi")

        self.client.post(detail_url, {"status": "unknown", "admin_notes": ""})
        lead.refresh_from_db()
        self.assertEqual(lead.status, "negotiating")

    def test_service_translation_formset_preserves_and_updates_each_language(self):
        service = Service.objects.create(
            title="Website",
            slug="website",
            short_description="Short",
            description="Description",
        )
        russian = ServiceTranslation.objects.create(
            service=service,
            language="ru",
            title="Веб-сайт",
            short_description="Создание сайтов",
            description="Подробное описание",
        )
        edit_url = reverse("dashboard:service_edit", args=[service.pk])
        response = self.client.get(edit_url)
        formset = response.context["formset"]
        self.assertEqual(
            [form.language_code for form in formset.forms],
            ["ru", "tr", "en"],
        )

        response = self.client.post(
            edit_url,
            {
                "title": "Website",
                "slug": "website",
                "short_description": "Short",
                "description": "Description",
                "icon": "globe",
                "order": "0",
                "is_active": "on",
                "translations-TOTAL_FORMS": "3",
                "translations-INITIAL_FORMS": "1",
                "translations-MIN_NUM_FORMS": "0",
                "translations-MAX_NUM_FORMS": "3",
                "translations-0-id": str(russian.pk),
                "translations-0-language": "ru",
                "translations-0-title": "Веб-платформы",
                "translations-0-short_description": "Разработка сайтов",
                "translations-0-description": "Обновлённое описание",
                "translations-0-meta_title": "",
                "translations-0-meta_description": "",
                "translations-1-language": "tr",
                "translations-1-title": "Web siteleri",
                "translations-1-short_description": "Kurumsal web sitesi geliştirme",
                "translations-1-description": "İşletmeler için modern web siteleri.",
                "translations-1-meta_title": "",
                "translations-1-meta_description": "",
                "translations-2-language": "en",
                "translations-2-title": "Websites",
                "translations-2-short_description": "Business website development",
                "translations-2-description": "Modern websites for businesses.",
                "translations-2-meta_title": "",
                "translations-2-meta_description": "",
            },
        )
        self.assertRedirects(response, reverse("dashboard:services"))
        service.refresh_from_db()
        russian.refresh_from_db()
        self.assertEqual(service.title, "Website")
        self.assertEqual(russian.title, "Веб-платформы")
        self.assertEqual(russian.description, "Обновлённое описание")
        self.assertEqual(service.translations.get(language="tr").title, "Web siteleri")
        self.assertEqual(service.translations.get(language="en").title, "Websites")

    def test_dashboard_crud_for_services_projects_team_and_settings(self):
        service_url = reverse("dashboard:service_create")
        response = self.client.post(
            service_url,
            {
                "title": "Dashboard service",
                "slug": "",
                "short_description": "Short description",
                "description": "Service body",
                "icon": "globe",
                "order": "2",
                "is_active": "on",
            },
        )
        self.assertRedirects(response, reverse("dashboard:services"))
        service = Service.objects.get(title="Dashboard service")
        self.assertEqual(service.slug, "dashboard-service")
        self.client.post(reverse("dashboard:service_toggle", args=[service.pk]))
        service.refresh_from_db()
        self.assertFalse(service.is_active)
        response = self.client.post(
            reverse("dashboard:service_edit", args=[service.pk]),
            {
                "title": "Updated service",
                "slug": "updated-service",
                "short_description": "Updated short description",
                "description": "Updated body",
                "icon": "code",
                "order": "3",
                "is_active": "on",
            },
        )
        self.assertRedirects(response, reverse("dashboard:services"))
        service.refresh_from_db()
        self.assertEqual(service.title, "Updated service")
        delete_url = reverse("dashboard:service_delete", args=[service.pk])
        self.assertEqual(self.client.get(delete_url).status_code, 200)
        self.client.post(delete_url)
        self.assertFalse(Service.objects.filter(pk=service.pk).exists())

        response = self.client.post(
            reverse("dashboard:project_create"),
            {
                "title": "Dashboard project",
                "slug": "",
                "summary": "Project summary",
                "description": "Project body",
                "technologies_text": "Django, PostgreSQL\nCSS",
                "is_featured": "on",
                "is_published": "",
                "order": "0",
            },
        )
        self.assertRedirects(response, reverse("dashboard:projects"))
        project = Project.objects.get(title="Dashboard project")
        self.assertEqual(project.technologies, ["Django", "PostgreSQL", "CSS"])
        self.assertEqual(project.translations.get(language="ru").title, "ru:Dashboard project")
        self.assertEqual(project.translations.get(language="en").description, "en:Project body")
        self.assertFalse(project.is_published)
        response = self.client.post(
            reverse("dashboard:project_edit", args=[project.pk]),
            {
                "title": "Updated project",
                "slug": "updated-project",
                "summary": "Updated summary",
                "description": "Updated project body",
                "technologies_text": "Python, Django",
                "project_url": "",
                "is_featured": "",
                "is_published": "on",
                "order": "1",
            },
        )
        self.assertRedirects(response, reverse("dashboard:projects"))
        project.refresh_from_db()
        self.assertEqual(project.title, "Updated project")
        self.assertTrue(project.is_published)
        public_projects = self.client.get(reverse("core:projects"))
        self.assertContains(public_projects, project.title)
        project_delete_url = reverse("dashboard:project_delete", args=[project.pk])
        self.assertEqual(self.client.get(project_delete_url).status_code, 200)
        self.client.post(project_delete_url)
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())

        response = self.client.post(
            reverse("dashboard:team_create"),
            {"name": "Dashboard teammate", "position": "Engineer", "bio": "Profile", "order": "1", "is_active": "on"},
        )
        self.assertRedirects(response, reverse("dashboard:team"))
        member = TeamMember.objects.get(name="Dashboard teammate", is_active=True)
        self.assertEqual(member.translations.get(language="tr").position, "tr:Engineer")
        self.assertEqual(member.translations.get(language="en").bio, "en:Profile")
        response = self.client.post(
            reverse("dashboard:team_edit", args=[member.pk]),
            {
                "name": "Updated teammate",
                "position": "Lead engineer",
                "bio": "Updated profile",
                "telegram_url": "",
                "linkedin_url": "",
                "is_active": "on",
                "order": "2",
            },
        )
        self.assertRedirects(response, reverse("dashboard:team"))
        member.refresh_from_db()
        self.assertEqual(member.name, "Updated teammate")
        member_delete_url = reverse("dashboard:team_delete", args=[member.pk])
        self.assertEqual(self.client.get(member_delete_url).status_code, 200)
        self.client.post(member_delete_url)
        self.assertFalse(TeamMember.objects.filter(pk=member.pk).exists())

        settings_url = reverse("dashboard:settings")
        settings = SiteSettings.get_instance()
        response = self.client.post(
            settings_url,
            {
                "company_name": "EraGate Studio",
                "tagline": "Better products",
                "footer_text": "Build with care",
                "phone": "+998901234567",
                "email": "hello@example.test",
                "address": "Tashkent",
                "telegram_username": "bytecore",
                "instagram_url": "https://instagram.com/bytecore",
                "linkedin_url": "https://linkedin.com/company/bytecore",
                "experience_stat": "8+ yil",
                "projects_stat": "12 loyiha",
                "support_stat": "",
                "meta_title": "EraGate Studio",
                "meta_description": "Digital products",
            },
        )
        self.assertRedirects(response, settings_url)
        settings.refresh_from_db()
        self.assertEqual(settings.company_name, "EraGate Studio")
        self.assertEqual(settings.footer_text, "Build with care")
        self.assertEqual(settings.experience_stat, "8+ yil")
        self.assertEqual(settings.projects_stat, "12 loyiha")

    def test_dashboard_service_search_and_status_filter(self):
        Service.objects.create(title="Alpha", slug="alpha", short_description="A", description="A", is_active=True)
        Service.objects.create(title="Beta", slug="beta", short_description="B", description="B", is_active=False)
        response = self.client.get(reverse("dashboard:services"), {"q": "Alpha", "active": "true"})
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        self.assertContains(response, "Alpha")
        self.assertNotContains(response, "Beta")

    def test_service_form_rejects_duplicate_slug(self):
        Service.objects.create(title="Existing", slug="taken", short_description="Short", description="Body")
        response = self.client.post(
            reverse("dashboard:service_create"),
            {
                "title": "Another",
                "slug": "taken",
                "short_description": "Short",
                "description": "Body",
                "icon": "globe",
                "order": "0",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bu slug bilan xizmat mavjud.")
        self.assertEqual(Service.objects.count(), 1)

    def test_save_and_translate_persists_uzbek_source_and_all_three_translations(self):
        with patch(
            "core.translation_service.translate_text",
            side_effect=lambda text, language: f"{language}:{text}",
        ) as translate:
            response = self.client.post(
                reverse("dashboard:service_create"),
                {
                    "title": "Veb-sayt",
                    "slug": "",
                    "short_description": "Qisqa tavsif",
                    "description": "To‘liq tavsif",
                    "meta_title": "SEO sarlavha",
                    "meta_description": "SEO tavsifi",
                    "icon": "globe",
                    "order": "0",
                    "is_active": "on",
                },
                follow=True,
            )

        service = Service.objects.get(slug="veb-sayt")
        self.assertEqual(service.title, "Veb-sayt")
        self.assertEqual(
            set(service.translations.values_list("language", flat=True)),
            {"ru", "en", "tr"},
        )
        for language in ("ru", "en", "tr"):
            translation = service.translations.get(language=language)
            translation.refresh_from_db()
            self.assertEqual(translation.title, f"{language}:Veb-sayt")
            self.assertEqual(translation.status, translation.STATUS_COMPLETE)
            self.assertFalse(translation.is_manual)
            self.assertEqual(service.get_translated("title", language), translation.title)
        self.assertEqual(translate.call_count, 15)
        self.assertContains(response, "tarjimalari saqlandi")
        self.assertContains(response, "RU: Tayyor")

    def test_translation_error_keeps_uzbek_content_and_can_be_retried(self):
        payload = {
            "title": "Sinov xizmati",
            "slug": "",
            "short_description": "Qisqa",
            "description": "Batafsil",
            "icon": "globe",
            "order": "0",
            "is_active": "on",
        }
        with patch(
            "core.translation_service.translate_text",
            side_effect=TranslationServiceError("Provider unavailable"),
        ):
            response = self.client.post(reverse("dashboard:service_create"), payload, follow=True)

        service = Service.objects.get(slug="sinov-xizmati")
        self.assertEqual(service.title, "Sinov xizmati")
        self.assertContains(response, "Provider unavailable")
        self.assertContains(response, "RU: Xatolik")
        self.assertEqual(
            set(service.translations.filter(status="failed").values_list("language", flat=True)),
            {"ru", "en", "tr"},
        )

        with patch(
            "core.translation_service.translate_text",
            side_effect=lambda text, language: f"{language}:{text}",
        ):
            self.client.post(reverse("dashboard:service_edit", args=[service.pk]), payload)
        service.refresh_from_db()
        self.assertEqual(service.translations.get(language="en").status, "complete")
        response = self.client.get(f"/en/services/{service.slug}/")
        self.assertContains(response, "Sinov xizmati")

    def test_retranslation_preserves_manual_values_without_confirmation(self):
        service = Service.objects.create(
            title="Veb-sayt",
            slug="manual-translation",
            short_description="Qisqa",
            description="Batafsil",
        )
        manual = ServiceTranslation.objects.create(
            service=service,
            language="ru",
            title="Редакторский перевод",
            short_description="Кратко",
            description="Подробное описание",
            status="complete",
        )
        payload = {
            "title": service.title,
            "slug": service.slug,
            "short_description": service.short_description,
            "description": service.description,
            "icon": service.icon,
            "order": "0",
            "is_active": "on",
        }
        self.mock_translation.reset_mock()
        self.client.post(reverse("dashboard:service_edit", args=[service.pk]), payload)

        manual.refresh_from_db()
        self.assertEqual(manual.title, "Редакторский перевод")
        self.assertTrue(manual.is_manual)
        self.assertNotIn("ru", [call.args[1] for call in self.mock_translation.call_args_list])

    def test_confirmed_retranslation_can_replace_manual_translation(self):
        service = Service.objects.create(
            title="Veb-sayt",
            slug="confirmed-translation",
            short_description="Qisqa",
            description="Batafsil",
        )
        translation = ServiceTranslation.objects.create(
            service=service,
            language="ru",
            title="Manual",
            short_description="Manual short",
            description="Manual description",
            status="complete",
        )
        with patch(
            "core.translation_service.translate_text",
            side_effect=lambda text, language: f"{language}:{text}",
        ):
            self.client.post(
                reverse("dashboard:service_translate", args=[service.pk]),
                {
                    "overwrite_manual": "1",
                },
            )

        translation.refresh_from_db()
        self.assertEqual(translation.title, "ru:Veb-sayt")
        self.assertFalse(translation.is_manual)

    def test_dashboard_permissions_are_enforced_per_section_and_action(self):
        limited_staff = User.objects.create_user(username="limited", password="safe-test-password", is_staff=True)
        limited_staff.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="services",
                codename="view_service",
            )
        )
        self.client.force_login(limited_staff)
        self.assertEqual(self.client.get(reverse("dashboard:services")).status_code, 200)
        self.assertEqual(self.client.get(reverse("dashboard:service_create")).status_code, 403)

    def test_csrf_is_enforced_on_dashboard_mutations(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        service = Service.objects.create(
            title="Toggle me",
            slug="toggle-me",
            short_description="Short",
            description="Body",
        )
        response = client.post(reverse("dashboard:service_toggle", args=[service.pk]))
        self.assertEqual(response.status_code, 403)
        service.refresh_from_db()
        self.assertTrue(service.is_active)
        lead = Lead.objects.create(full_name="Private", email="private@example.test", message="Text")
        response = client.post(
            reverse("dashboard:lead_detail", args=[lead.pk]),
            {"status": "completed", "admin_notes": ""},
        )
        self.assertEqual(response.status_code, 403)
        lead.refresh_from_db()
        self.assertEqual(lead.status, "new")
