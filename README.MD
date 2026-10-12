-- Active: 1791783222003@@127.0.0.1@3306
# ByteCore

ByteCore is a production-style corporate website built with Django 5.2 LTS. The project includes:

- Dark premium corporate landing pages
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

The site is available at http://127.0.0.1:8000.

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
