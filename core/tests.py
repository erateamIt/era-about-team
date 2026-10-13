from io import StringIO
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .i18n import LANGUAGE_CODES
from .models import SiteSettings
from .translation_service import TranslationServiceError, translate_instance, translate_text
from .validators import MAX_IMAGE_SIZE, validate_image_file
from projects.models import Project
from projects.models import ProjectTranslation
from services.models import Service, ServiceTranslation
from team.models import TeamMember


class ImageUploadValidationTests(SimpleTestCase):
    def test_rejects_non_image_extensions(self):
        upload = SimpleUploadedFile("document.txt", b"not an image", content_type="text/plain")
        with self.assertRaises(ValidationError):
            validate_image_file(upload)


class HomepageStatisticsTests(TestCase):
    def test_empty_statistics_are_hidden_and_configured_values_are_rendered(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Yillik tajriba")

        settings = SiteSettings.get_instance()
        settings.experience_stat = "8+ yil"
        settings.projects_stat = "12 loyiha"
        settings.save()
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "8+ yil")
        self.assertContains(response, "12 loyiha")
        self.assertNotContains(response, "24/7")

    def test_static_files_use_whitenoise_with_manifest_storage_in_production_mode(self):
        self.assertIn("whitenoise.middleware.WhiteNoiseMiddleware", settings.MIDDLEWARE)
        self.assertIn(
            settings.STORAGES["staticfiles"]["BACKEND"],
            {
                "django.contrib.staticfiles.storage.StaticFilesStorage",
                "whitenoise.storage.CompressedManifestStaticFilesStorage",
            },
        )


class LanguageRoutingTests(TestCase):
    def setUp(self):
        translation_patch = patch(
            "core.translation_service.translate_text",
            side_effect=lambda text, language: f"{language}:{text}",
        )
        self.mock_translation = translation_patch.start()
        self.addCleanup(translation_patch.stop)

    def test_main_pages_are_available_with_language_prefixes(self):
        paths = ("", "about/", "services/", "projects/", "team/", "contact/", "privacy/")
        home_titles = {
            "uz": "ByteCore | IT xizmatlari va raqamli mahsulotlar",
            "ru": "ByteCore | IT-услуги и цифровые продукты",
            "tr": "ByteCore | BT hizmetleri ve dijital ürünler",
            "en": "ByteCore | IT services and digital products",
        }
        for language in LANGUAGE_CODES:
            for path in paths:
                with self.subTest(language=language, path=path):
                    response = self.client.get(f"/{language}/{path}")
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, f'<html lang="{language}">')
                    self.assertContains(response, f'hreflang="{language}"')
                    if not path:
                        self.assertContains(response, f"<title>{home_titles[language]}</title>")

    def test_language_switcher_keeps_the_current_page_and_persists_choice(self):
        response = self.client.get("/tr/projects/")
        self.assertContains(response, 'href="/ru/projects/"')
        self.assertEqual(response.cookies["bytecore_language"].value, "tr")

        redirect_response = self.client.get("/")
        self.assertRedirects(redirect_response, "/tr/")

    @override_settings(CONTENT_TRANSLATION_ON_DEMAND=False)
    def test_untranslated_dynamic_content_falls_back_to_uzbek(self):
        service = Service.objects.create(
            title="Tarjima qilinmagan xizmat",
            slug="untranslated-service",
            short_description="Qisqa tavsif",
            description="To‘liq tavsif",
        )
        response = self.client.get(f"/en/services/{service.slug}/")
        self.assertContains(response, service.title)
        self.assertContains(self.client.get(f"/ru/services/{service.slug}/"), service.title)
        self.assertContains(self.client.get(f"/uz/services/{service.slug}/"), service.title)

    def test_first_non_uzbek_visit_generates_and_persists_translation_only_once(self):
        service = Service.objects.create(
            title="Tarjima talab qilinadi",
            slug="on-demand-service",
            short_description="Qisqa",
            description="Batafsil",
        )
        response = self.client.get(f"/en/services/{service.slug}/")
        self.assertContains(response, "en:Tarjima talab qilinadi")
        self.assertEqual(service.translations.get(language="en").status, "complete")
        first_call_count = self.mock_translation.call_count
        self.client.get(f"/en/services/{service.slug}/")
        self.assertEqual(self.mock_translation.call_count, first_call_count)

    def test_admin_translations_render_in_requested_language(self):
        service = Service.objects.create(
            title="Veb-sayt",
            slug="web-site",
            short_description="Qisqa",
            description="Batafsil",
        )
        ServiceTranslation.objects.create(
            service=service,
            language="ru",
            title="Веб-сайт",
            short_description="Создание веб-сайтов",
            description="Разработка современных сайтов для бизнеса.",
        )
        response = self.client.get("/ru/services/")
        self.assertContains(response, "Веб-сайт")
        self.assertContains(response, "Создание веб-сайтов")

        project = Project.objects.create(
            title="Loyiha",
            slug="translated-project",
            summary="Qisqacha",
            description="Batafsil",
        )
        ProjectTranslation.objects.create(
            project=project,
            language="ru",
            title="Переведённый проект",
            summary="Краткое описание",
            description="Подробное описание проекта.",
        )
        response = self.client.get(f"/ru/projects/{project.slug}/")
        self.assertContains(response, "Переведённый проект")
        self.assertContains(response, "Подробное описание проекта.")

    def test_language_prefix_redirect_uses_saved_language(self):
        self.client.get("/en/")
        response = self.client.get("/services/")
        self.assertRedirects(response, "/en/services/")

    def test_seed_content_includes_translations_without_overwriting_editor_changes(self):
        call_command("seed_data", stdout=StringIO())
        service = Service.objects.get(slug="web-saytlar-va-landing-page")
        service.translations.filter(language="ru").update(title="Редакционный перевод")

        call_command("seed_data", stdout=StringIO())

        self.assertEqual(
            service.translations.get(language="ru").title,
            "Редакционный перевод",
        )
        self.assertEqual(
            set(service.translations.values_list("language", flat=True)),
            {"ru", "tr", "en"},
        )


class SearchEngineMetadataTests(TestCase):
    def test_robots_txt_points_to_sitemap(self):
        response = self.client.get(reverse("core:robots"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertContains(response, "Sitemap: http://testserver/sitemap.xml")
        self.assertContains(response, "Disallow: /dashboard/")

    def test_sitemap_contains_static_and_public_dynamic_pages_only(self):
        Service.objects.create(
            title="Visible service",
            slug="visible-service",
            short_description="Short",
            description="Details",
            is_active=True,
        )
        Service.objects.create(
            title="Hidden service",
            slug="hidden-service",
            short_description="Short",
            description="Details",
            is_active=False,
        )
        Project.objects.create(
            title="Published project",
            slug="published-project",
            summary="Short",
            description="Details",
            is_published=True,
        )
        Project.objects.create(
            title="Draft project",
            slug="draft-project",
            summary="Short",
            description="Details",
            is_published=False,
        )
        response = self.client.get(reverse("sitemap"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/")
        self.assertContains(response, "/contact/")
        self.assertContains(response, "/services/visible-service/")
        self.assertContains(response, "/projects/published-project/")
        self.assertNotContains(response, "hidden-service")


    def test_detail_pages_override_open_graph_content(self):
        project = Project.objects.create(
            title="OG project",
            slug="og-project",
            summary="Project summary",
            description="Details",
            meta_title="Custom project title",
            meta_description="Custom project description",
        )
        response = self.client.get(reverse("core:project_detail", args=[project.slug]))
        self.assertContains(response, 'property="og:title" content="Custom project title | ByteCore"')
        self.assertContains(response, 'property="og:description" content="Custom project description"')
        self.assertContains(response, 'property="og:type" content="article"')

    def test_rejects_images_over_five_megabytes(self):
        upload = SimpleUploadedFile(
            "large.png",
            b"x" * (MAX_IMAGE_SIZE + 1),
            content_type="image/png",
        )
        with self.assertRaises(ValidationError):
            validate_image_file(upload)


class TranslationInputValidationTests(SimpleTestCase):
    def test_rejects_unsupported_languages_and_oversized_or_controlled_text(self):
        with self.assertRaises(TranslationServiceError):
            translate_text("Matn", "fr")
        with self.assertRaises(TranslationServiceError):
            translate_text("x" * 5001, "en")
        with self.assertRaises(TranslationServiceError):
            translate_text("Matn\x00", "en")

    @patch("deep_translator.google.requests.get")
    def test_google_translation_uses_bounded_http_timeout(self, get):
        get.return_value.status_code = 200
        get.return_value.text = '<div class="t0">Translated</div>'

        self.assertEqual(translate_text("Matn", "en"), "Translated")
        self.assertEqual(get.call_args.kwargs["timeout"], (3, 8))

    @patch("deep_translator.GoogleTranslator")
    def test_urls_emails_phones_and_inline_code_are_not_sent_for_translation(self, translator_class):
        translator = translator_class.return_value
        translator.translate.side_effect = lambda text: text.replace("test", "translated")
        source = "Write `print(1)` or email help@example.test; visit https://example.test and call +998 90 123 45 67."

        translated = translate_text(source, "en")

        sent_text = translator.translate.call_args.args[0]
        self.assertNotIn("help@example.test", sent_text)
        self.assertNotIn("https://example.test", sent_text)
        self.assertNotIn("+998 90 123 45 67", sent_text)
        self.assertNotIn("print(1)", sent_text)
        self.assertIn("help@example.test", translated)
        self.assertIn("https://example.test", translated)
        self.assertIn("+998 90 123 45 67", translated)
        self.assertIn("`print(1)`", translated)


class AutoTranslationPersistenceTests(TestCase):
    def test_site_project_and_team_translations_are_saved_per_language(self):
        settings = SiteSettings.get_instance()
        project = Project.objects.create(
            title="Loyiha",
            slug="translation-project",
            summary="Qisqa",
            description="Batafsil",
        )
        member = TeamMember.objects.create(name="A’zo", position="Dasturchi", bio="Tajriba")

        with patch(
            "core.translation_service.translate_text",
            side_effect=lambda text, language: f"{language}:{text}",
        ):
            for instance in (settings, project, member):
                translate_instance(instance)

        settings.refresh_from_db()
        project.refresh_from_db()
        member.refresh_from_db()
        self.assertEqual(settings.translations.get(language="ru").tagline, f"ru:{settings.tagline}")
        self.assertEqual(project.translations.get(language="en").summary, "en:Qisqa")
        self.assertEqual(member.translations.get(language="tr").position, "tr:Dasturchi")
        self.assertEqual(project.get_translated("description", "en"), "en:Batafsil")

    def test_source_edit_marks_translation_stale_and_falls_back_until_regenerated(self):
        service = Service.objects.create(
            title="Old title",
            slug="stale-service",
            short_description="Old short",
            description="Old details",
        )
        with patch(
            "core.translation_service.translate_text",
            side_effect=lambda text, language: f"{language}:{text}",
        ):
            translate_instance(service)

        service.title = "New title"
        service.save()
        russian = service.translations.get(language="ru")
        russian.refresh_from_db()
        self.assertEqual(russian.status, russian.STATUS_STALE)
        self.assertEqual(service.get_translated("title", "ru"), "New title")

        with patch(
            "core.translation_service.translate_text",
            side_effect=lambda text, language: f"{language}:{text}",
        ):
            translate_instance(service)
        russian.refresh_from_db()
        self.assertEqual(russian.status, russian.STATUS_COMPLETE)
        self.assertEqual(russian.title, "ru:New title")
