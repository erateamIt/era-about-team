-- Active: 1791783222003@@127.0.0.1@3306
# ByteCore

ByteCore is a production-style corporate website built with Django 5.2 LTS. The project includes:

- Dark premium corporate landing pages
- Four public languages: Uzbek, Russian, Turkish, and English
- Service, project, and team management via Django admin
- Dedicated staff dashboard at `/dashboard/` for daily content and order management
- Contact form with optional Telegram notifications
- PostgreSQL-ready configuration with SQLite fallback for local development

## Quick start

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   . .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

3. Run migrations and seed starter content:
   ```bash
   python manage.py migrate
   python manage.py seed_data
   ```

4. Start the local server:
   ```bash
   python manage.py runserver
   ```

For production, set `DEBUG=False`, a unique `SECRET_KEY`, and `ALLOWED_HOSTS` in `.env`, then collect static assets:

```bash
python manage.py collectstatic --noinput
```

WhiteNoise serves compressed, manifest-versioned static files when `DEBUG=False`. `SECURE_SSL_REDIRECT` defaults to `False` and `SECURE_HSTS_SECONDS` to `0` in development; in production they default to HTTPS redirect enabled and one-year HSTS. Set either environment variable explicitly to override its default. Behind a trusted HTTPS-terminating proxy, set `SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https` and ensure the proxy overwrites that header. Do not enable HSTS until HTTPS is available for the entire domain.

## Search engine metadata

`/sitemap.xml` lists the public pages, active services, and published projects. `/robots.txt` allows public crawling and references the sitemap. Home page statistics are blank by default; set verified values in site settings before showing them.

The public site is available at `http://127.0.0.1:8000/uz/`; Russian, Turkish, and English use `/ru/`, `/tr/`, and `/en/`. The language switcher keeps the current page, and the selected language is saved in a cookie. Unprefixed public URLs redirect to the preferred language.

## Translations

Static interface text uses Django gettext catalogs in `locale/`. After editing translatable interface strings, extract and compile catalogs:

```bash
python manage.py makemessages -l uz -l ru -l tr -l en
python manage.py compilemessages
```

The Django management commands require GNU gettext to be installed. Admin-managed services, projects, team profiles, and site settings have separate Russian, Turkish, and English translation rows stored in the database. Enter source content in Uzbek in the staff dashboard; **Save** stores the Uzbek fields and automatically attempts the three translations. The optional `deep-translator` Google Translate integration requires no API key, but relies on Google's external service, availability, and current usage terms. Text is validated and requests use connect/read timeouts. Translation is synchronous for this MVP, so a slow external provider can delay a dashboard save.

With `CONTENT_TRANSLATION_ON_DEMAND=True` (default), a missing non-Uzbek translation can also be generated the first time the corresponding public content is requested. A database status claim prevents concurrent duplicate work; failed requests are not repeated on every page view. If the service is unavailable, the page uses the Uzbek source text and the dashboard reports the error. Successful results are stored in PostgreSQL and served from there on later requests. Turn on-demand generation off in `.env` if public requests should never wait for the translation provider; saves and the explicit dashboard retry action still work.

Translations can be reviewed and edited individually in the dashboard or Django admin. Edited translations are marked as manual and are not overwritten by normal saves or retries. Source edits mark previous translations stale; automatic translation regenerates non-manual rows, while manual rows remain stale until an editor updates them or confirms replacement through the dashboard. Dashboard lists show complete, pending, failed, stale, and manually edited states. The `seed_data` command creates starter translations without overwriting translations already entered by editors.

Public pages emit language-specific canonical URLs, `hreflang` alternates, and translated metadata where configured. The sitemap includes each language variant.

## Dashboard and admin

Create a staff account. A superuser has all dashboard permissions:

```bash
python manage.py createsuperuser
```

- Sign in at http://127.0.0.1:8000/dashboard/login/
- Manage content at http://127.0.0.1:8000/dashboard/
- Use http://127.0.0.1:8000/admin/ for technical administration and permission assignment.

Dashboard sections check Django model permissions individually. Logout uses a CSRF-protected POST action. Lead management includes search, status/date filters, pagination, and status updates. Services, projects, team members, and site settings can be managed from the dashboard; image uploads are limited to supported image formats up to 5 MB.

Dashboard login allows up to 10 attempts per client address in 15 minutes using Django’s configured cache. The default local-memory cache is per application process; multi-worker deployments should configure a shared cache backend for consistent limits.

Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env` to enable lead notifications. Configure `DATABASE_URL` to use PostgreSQL; local development defaults to SQLite.
