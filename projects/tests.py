from django.test import TestCase
from django.urls import reverse

from .admin import ProjectAdminForm
from .models import Project, ProjectImage


class ProjectAdminFormTests(TestCase):
    def test_comma_separated_technologies_are_saved_as_json_list(self):
        form = ProjectAdminForm(
            data={
                "title": "Admin project",
                "slug": "admin-project",
                "summary": "A short summary",
                "description": "Project description",
                "technologies": "Django, React",
                "project_url": "",
                "is_featured": "",
                "is_published": "on",
                "order": "0",
                "meta_title": "",
                "meta_description": "",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        project = form.save()
        self.assertEqual(project.technologies, ["Django", "React"])


class ProjectGalleryTests(TestCase):
    def test_gallery_cover_and_remaining_images_are_rendered_with_alt_text(self):
        project = Project.objects.create(
            title="Gallery project",
            slug="gallery-project",
            summary="Gallery summary",
            description="Gallery description",
        )
        cover = ProjectImage.objects.create(
            project=project,
            image="projects/gallery/cover.png",
            alt_text="Muqova tasviri",
            is_cover=True,
        )
        gallery = ProjectImage.objects.create(
            project=project,
            image="projects/gallery/screen.png",
            alt_text="Asosiy ekran",
        )

        response = self.client.get(reverse("core:project_detail", args=[project.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["cover_gallery_image"], cover)
        self.assertEqual(response.context["gallery_images"], [gallery])
        self.assertContains(response, 'alt="Muqova tasviri"')
        self.assertContains(response, 'alt="Asosiy ekran"')
        self.assertContains(response, 'loading="lazy"')

    def test_project_cover_image_takes_precedence_without_marked_gallery_cover(self):
        project = Project.objects.create(
            title="Cover project",
            slug="cover-project",
            summary="Summary",
            description="Description",
            cover_image="projects/cover/main.png",
        )
        image = ProjectImage.objects.create(
            project=project,
            image="projects/gallery/other.png",
            alt_text="Other view",
        )

        response = self.client.get(reverse("core:project_detail", args=[project.slug]))

        self.assertEqual(response.context["cover_image"].name, "projects/cover/main.png")
        self.assertEqual(response.context["gallery_images"], [image])
