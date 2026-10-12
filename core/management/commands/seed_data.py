from django.core.management.base import BaseCommand

from core.models import SiteSettings
from projects.models import Project
from services.models import Service
from team.models import TeamMember


class Command(BaseCommand):
    help = "Populate default ByteCore site content"

    def handle(self, *args, **options):
        SiteSettings.get_instance()

        services = [
            ("Web saytlar va landing page", "web-saytlar-va-landing-page", "Kompaniyangiz uchun zamonaviy va tezkor veb-platformalar yaratamiz.", "Web saytlar va landing page uchun eng yaxshi yechimlar.", "globe"),
            ("Internet-do'konlar", "internet-do-konlar", "Savdo jarayonlarini avtomatlashtirishga yordam beruvchi e-commerce yechimlari.", "Internet-do'konlar uchun zamonaviy interfeys va ishonchli texnologiyalar.", "shopping-cart"),
            ("Telegram botlar", "telegram-botlar", "Mijozlar bilan tezkor aloqani ta'minlovchi botlar.", "Botlar yordamida operatsion jarayonlarni avtomatlashtiramiz.", "send"),
            ("CRM va biznes avtomatlashtirish", "crm-va-biznes-avtomatlashtirish", "Biznesingizni ma'lumotlar va jarayonlar bo'yicha boshqarish.", "Jarayonlarni avtomatlashtirish va samaradorlikni oshirish.", "workflow"),
            ("API va backend development", "api-va-backend-development", "Mahsuldor va xavfsiz backend infrastruktura yaratish.", "REST API, integratsiyalar va server logikasi.", "server"),
            ("UI/UX dizayn", "ui-ux-dizayn", "Foydalanuvchi tajribasini optimallashtiruvchi dizayn.", "Minimalist va premium dizayn konsepsiyasi.", "palette"),
            ("AI integratsiyasi", "ai-integratsiyasi", "AI va avtomatlashtirishning amaliy yechimlari.", "Ko'proq qulaylik va operatsion samaradorlik.", "sparkles"),
            ("Mobil ilovalar", "mobil-ilovalar", "Android va iOS uchun zamonaviy mobil mahsulotlar.", "Tezkor va qulay mobil yechimlar.", "smartphone"),
        ]

        for title, slug, short, description, icon in services:
            Service.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "short_description": short,
                    "description": description,
                    "icon": icon,
                    "is_active": True,
                    "order": 0,
                },
            )

        projects = [
            (
                "NovaTrade",
                "novatrade",
                "B2B savdo platformasi",
                "Katalog, buyurtma va CRM integratsiyasini birlashtirgan zamonaviy platforma.",
                ["Django", "PostgreSQL", "React", "Stripe"],
                "https://example.com",
                True,
            ),
            (
                "FinFlow",
                "finflow",
                "Moliya monitoring platformasi",
                "Kreditlar, hisobotlar va boshqaruv paneli uchun amaliy moliyaviy texnologiya yechimi.",
                ["Python", "Django", "Tailwind", "Chart.js"],
                "https://example.com",
                True,
            ),
            (
                "SmartOps",
                "smartops",
                "Biznes avtomatlashtirishni boshqarish",
                "Operatsion jarayonlarni tekislash uchun CRM va avtomatlashtirish platformasi.",
                ["Django", "Celery", "Redis", "Docker"],
                "https://example.com",
                True,
            ),
        ]
        for title, slug, summary, description, technologies, project_url, is_featured in projects:
            Project.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "summary": summary,
                    "description": description,
                    "technologies": technologies,
                    "project_url": project_url,
                    "is_featured": is_featured,
                    "is_published": True,
                    "order": 0,
                },
            )

        team_members = [
            ("Asadbek Karimov", "CEO & Co-founder", "Startup va korporativ loyihalarni boshqarish, strategiya va biznes rivojlanish yo'nalishlari."),
            ("Nodir Yusupov", "Tech Lead", "Tizim arxitekturasi, backend va kengaytirish uchun texnik qarorlar qabul qiladi."),
            ("Dilnoza Mavlonova", "Product Designer", "Foydalanuvchi tajribasini optimallashtiruvchi premium interfeyslar yaratadi."),
            ("Sardor Rakhimov", "Full-Stack Developer", "Frontend va backenddagi kompleks imkoniyatlarni ishlab chiqadi."),
        ]
        for name, position, bio in team_members:
            TeamMember.objects.update_or_create(
                name=name,
                defaults={
                    "position": position,
                    "bio": bio,
                    "is_active": True,
                    "order": 0,
                },
            )

        self.stdout.write(self.style.SUCCESS("ByteCore seed data created successfully."))
