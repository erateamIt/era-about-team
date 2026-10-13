from django.core.management.base import BaseCommand

from core.models import SiteSettings, SiteSettingsTranslation
from projects.models import Project, ProjectTranslation
from services.models import Service, ServiceTranslation
from team.models import TeamMember, TeamMemberTranslation


class Command(BaseCommand):
    help = "Populate default ByteCore site content"

    def handle(self, *args, **options):
        settings = SiteSettings.get_instance()
        site_translations = {
            "ru": {
                "tagline": "Цифровые решения для амбициозного бизнеса",
                "footer_text": "Ваш надёжный партнёр в цифровом развитии.",
                "address": "Ташкент, Узбекистан",
                "meta_title": "ByteCore — IT-услуги и цифровые продукты",
                "meta_description": "Разрабатываем веб-платформы, автоматизацию и цифровые продукты для развития бизнеса.",
            },
            "tr": {
                "tagline": "İddialı işletmeler için dijital çözümler",
                "footer_text": "Dijital gelişim yolculuğunuzda güvenilir iş ortağınız.",
                "address": "Taşkent, Özbekistan",
                "meta_title": "ByteCore — BT hizmetleri ve dijital ürünler",
                "meta_description": "İşletmeler için web platformları, otomasyon ve dijital ürünler geliştiriyoruz.",
            },
            "en": {
                "tagline": "Digital solutions for ambitious businesses",
                "footer_text": "Your trusted partner for digital growth.",
                "address": "Tashkent, Uzbekistan",
                "meta_title": "ByteCore — IT services and digital products",
                "meta_description": "We build web platforms, automation and digital products that help businesses grow.",
            },
        }
        for language, fields in site_translations.items():
            SiteSettingsTranslation.objects.get_or_create(
                settings=settings,
                language=language,
                defaults=fields,
            )

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
            service, _ = Service.objects.update_or_create(
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
            service_translations = {
                "web-saytlar-va-landing-page": {
                    "ru": ("Сайты и лендинги", "Создаём современные и быстрые веб-платформы для вашей компании.", "Эффективные решения для сайтов и лендингов."),
                    "tr": ("Web siteleri ve açılış sayfaları", "Şirketiniz için modern ve hızlı web platformları geliştiriyoruz.", "Web siteleri ve açılış sayfaları için güçlü çözümler."),
                    "en": ("Websites and landing pages", "We build modern, fast web platforms for your company.", "Effective solutions for websites and landing pages."),
                },
                "internet-do-konlar": {
                    "ru": ("Интернет-магазины", "Создаём решения для электронной торговли и автоматизации продаж.", "Современный интерфейс и надёжные технологии для онлайн-магазинов."),
                    "tr": ("E-ticaret mağazaları", "Satış süreçlerini otomatikleştiren e-ticaret çözümleri geliştiriyoruz.", "Online mağazalar için modern arayüz ve güvenilir teknoloji."),
                    "en": ("Online stores", "E-commerce solutions that help automate your sales operations.", "Modern interfaces and reliable technology for online stores."),
                },
                "telegram-botlar": {
                    "ru": ("Telegram-боты", "Боты для быстрой связи с клиентами и удобного обслуживания.", "Автоматизируем повседневные операции с помощью ботов."),
                    "tr": ("Telegram botları", "Müşterilerle hızlı iletişim ve kolay hizmet sunan botlar.", "Botlarla operasyonel süreçleri otomatikleştiriyoruz."),
                    "en": ("Telegram bots", "Bots that make customer communication and service faster.", "We automate everyday operations with practical bots."),
                },
                "crm-va-biznes-avtomatlashtirish": {
                    "ru": ("CRM и автоматизация бизнеса", "Управляйте данными и процессами компании в единой системе.", "Автоматизируем процессы и повышаем эффективность команды."),
                    "tr": ("CRM ve iş otomasyonu", "Şirketinizin verilerini ve süreçlerini tek bir sistemden yönetin.", "Süreçleri otomatikleştirip ekip verimliliğini artırıyoruz."),
                    "en": ("CRM and business automation", "Manage your business data and workflows in one place.", "We automate processes and improve operational efficiency."),
                },
                "api-va-backend-development": {
                    "ru": ("API и backend-разработка", "Создаём производительную и безопасную backend-инфраструктуру.", "REST API, интеграции и серверная логика для вашего продукта."),
                    "tr": ("API ve backend geliştirme", "Üretime hazır, güvenli backend altyapıları geliştiriyoruz.", "Ürününüz için REST API, entegrasyonlar ve sunucu mantığı."),
                    "en": ("API and backend development", "We build secure, high-performance backend infrastructure.", "REST APIs, integrations and server-side product logic."),
                },
                "ui-ux-dizayn": {
                    "ru": ("UI/UX-дизайн", "Проектируем интерфейсы, которые делают продукт удобнее.", "Продуманные минималистичные дизайн-концепции."),
                    "tr": ("UI/UX tasarımı", "Ürünün kullanımını kolaylaştıran arayüzler tasarlıyoruz.", "Özenli, sade ve modern tasarım konseptleri."),
                    "en": ("UI/UX design", "We design interfaces that make products easier to use.", "Thoughtful, minimal and modern design concepts."),
                },
                "ai-integratsiyasi": {
                    "ru": ("Интеграция ИИ", "Внедряем практичные решения на основе ИИ и автоматизации.", "Больше удобства и эффективности в повседневной работе."),
                    "tr": ("Yapay zekâ entegrasyonu", "Yapay zekâ ve otomasyonla pratik çözümler sunuyoruz.", "Günlük işlerde daha fazla kolaylık ve verimlilik."),
                    "en": ("AI integration", "We implement practical AI and automation solutions.", "More convenience and efficiency in everyday operations."),
                },
                "mobil-ilovalar": {
                    "ru": ("Мобильные приложения", "Создаём современные мобильные продукты для Android и iOS.", "Быстрые и удобные решения для мобильных устройств."),
                    "tr": ("Mobil uygulamalar", "Android ve iOS için modern mobil ürünler geliştiriyoruz.", "Hızlı ve kullanışlı mobil çözümler."),
                    "en": ("Mobile applications", "We build modern mobile products for Android and iOS.", "Fast, intuitive experiences for mobile users."),
                },
            }
            for language, translated_fields in service_translations[slug].items():
                ServiceTranslation.objects.get_or_create(
                    service=service,
                    language=language,
                    defaults=dict(
                        zip(
                            ("title", "short_description", "description"),
                            translated_fields,
                        )
                    ),
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
            project, _ = Project.objects.update_or_create(
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
            project_translations = {
                "novatrade": {
                    "ru": ("NovaTrade", "B2B-платформа для торговли", "Современная платформа, объединяющая каталог, заказы и интеграцию с CRM."),
                    "tr": ("NovaTrade", "B2B ticaret platformu", "Katalog, sipariş ve CRM entegrasyonunu bir araya getiren modern platform."),
                    "en": ("NovaTrade", "B2B commerce platform", "A modern platform combining product catalogues, orders and CRM integrations."),
                },
                "finflow": {
                    "ru": ("FinFlow", "Платформа финансового мониторинга", "Практичное финтех-решение для кредитов, отчётности и панели управления."),
                    "tr": ("FinFlow", "Finansal takip platformu", "Krediler, raporlar ve yönetim paneli için pratik bir finans teknolojisi çözümü."),
                    "en": ("FinFlow", "Financial monitoring platform", "A practical fintech solution for loans, reporting and management dashboards."),
                },
                "smartops": {
                    "ru": ("SmartOps", "Управление автоматизацией бизнеса", "CRM-платформа для оптимизации операционных процессов и автоматизации задач."),
                    "tr": ("SmartOps", "İş otomasyonu yönetimi", "Operasyonları düzenleyen CRM ve otomasyon platformu."),
                    "en": ("SmartOps", "Business automation management", "A CRM and automation platform that streamlines everyday operations."),
                },
            }
            for language, translated_fields in project_translations[slug].items():
                ProjectTranslation.objects.get_or_create(
                    project=project,
                    language=language,
                    defaults=dict(
                        zip(("title", "summary", "description"), translated_fields)
                    ),
                )

        team_members = [
            ("Asadbek Karimov", "CEO & Co-founder", "Startup va korporativ loyihalarni boshqarish, strategiya va biznes rivojlanish yo'nalishlari."),
            ("Nodir Yusupov", "Tech Lead", "Tizim arxitekturasi, backend va kengaytirish uchun texnik qarorlar qabul qiladi."),
            ("Dilnoza Mavlonova", "Product Designer", "Foydalanuvchi tajribasini optimallashtiruvchi premium interfeyslar yaratadi."),
            ("Sardor Rakhimov", "Full-Stack Developer", "Frontend va backenddagi kompleks imkoniyatlarni ishlab chiqadi."),
        ]
        for name, position, bio in team_members:
            member, _ = TeamMember.objects.update_or_create(
                name=name,
                defaults={
                    "position": position,
                    "bio": bio,
                    "is_active": True,
                    "order": 0,
                },
            )
            member_translations = {
                "Asadbek Karimov": {
                    "ru": ("Генеральный директор и сооснователь", "Руководит стартапами и корпоративными проектами, отвечает за стратегию и развитие бизнеса."),
                    "tr": ("CEO ve Kurucu Ortak", "Girişim ve kurumsal projeleri yönetir; strateji ve iş geliştirmeye odaklanır."),
                    "en": ("CEO & Co-founder", "Leads startup and enterprise projects, strategy and business development."),
                },
                "Nodir Yusupov": {
                    "ru": ("Технический руководитель", "Отвечает за архитектуру систем, backend и технические решения для масштабирования."),
                    "tr": ("Teknik Lider", "Sistem mimarisi, backend ve ölçeklenebilirlik için teknik kararları yönetir."),
                    "en": ("Tech Lead", "Leads system architecture, backend engineering and technical decisions for scale."),
                },
                "Dilnoza Mavlonova": {
                    "ru": ("Продуктовый дизайнер", "Создаёт продуманные интерфейсы и улучшает пользовательский опыт."),
                    "tr": ("Ürün Tasarımcısı", "Kullanıcı deneyimini geliştiren özenli arayüzler tasarlar."),
                    "en": ("Product Designer", "Creates thoughtful interfaces and improves the end-to-end user experience."),
                },
                "Sardor Rakhimov": {
                    "ru": ("Full-stack разработчик", "Разрабатывает комплексные решения для frontend- и backend-части продуктов."),
                    "tr": ("Full-Stack Geliştirici", "Ürünlerin frontend ve backend tarafındaki kapsamlı özellikleri geliştirir."),
                    "en": ("Full-Stack Developer", "Builds end-to-end product capabilities across frontend and backend."),
                },
            }
            for language, translated_fields in member_translations[name].items():
                TeamMemberTranslation.objects.get_or_create(
                    member=member,
                    language=language,
                    defaults=dict(zip(("position", "bio"), translated_fields)),
                )

        self.stdout.write(self.style.SUCCESS("ByteCore seed data created successfully."))
