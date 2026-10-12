from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .models import SiteSettings
from .validators import MAX_IMAGE_SIZE, validate_image_file
from projects.models import Project
from services.models import Service


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
        self.assertNotContains(response, "draft-project")

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
