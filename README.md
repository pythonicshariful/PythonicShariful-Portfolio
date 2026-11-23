# Pythonic Shariful — Portfolio Website

Main portfolio website for **Shariful Islam (Pythonic Shariful)** — Web Scraping
& Automation Expert.

GitHub repo: **https://github.com/pythonicshariful/PythonicShariful-Portfolio**

Stack: **Python Flask only** (Flask + Werkzeug, stdlib `sqlite3` — no SQLAlchemy,
no Node build step). Custom CSS in `static/css/`, vanilla JS in `static/js/`
(nav, scroll reveal, stats count-up, tools marquee — no build step, no 3D).

Design: light premium agency theme (pale mint `#EEFDF9` background, deep navy
`#213D63` headings, violet `#5B3FF8` + teal `#0AA692` accents), Plus Jakarta
Sans + JetBrains Mono, responsive mobile-first (375 / 768 / 1024 / 1440px),
from the ui-ux-pro-max design skill. The homepage story section shows his
portrait (photo left, text right); the hero itself stays text-free of photos — split layout with an animated bot GIF (hero-bot.gif, built with PIL in ~/workspace/hero-bot-gif/), animated gradient headline, social pills incl. WhatsApp, a browser-frame terminal with live typing animation, drifting gradient orbs, floating proof cards and tool chips. (Marketplace rating badges were removed 2026-11-23 — ratings change, so static numbers go stale.)

## Features

- Public site: Home (centred hero, count-up stats, story, services, tools
  marquee, dark How-I-Work section, featured work, FAQ, contact CTA card),
  About (photo + timeline + skill bars), Services, filterable
  Projects + project detail pages, Contact form (saved to SQLite, honeypot
  anti-spam), `/health` / `/api/health` JSON endpoint.
- Admin dashboard (`/admin`): session auth, stats, full CRUD for projects,
  services and skills, messages inbox (mark read/unread, delete), site
  settings (hero text, about text, links) and admin password change.
- SQLite database `instance/site.db`, created and seeded automatically on
  first run. Seeding only fills empty tables — restarting never wipes data.

## Run locally

```bash
cd PythonicShariful-Portfolio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# First run (dev only — change the password immediately after login):
SECRET_KEY="dev-secret-change-me" ADMIN_PASSWORD="admin123" python app.py
# or: flask run --port 5002
```

Then open http://127.0.0.1:5002/

**Default admin login (first run only):**

- URL: http://127.0.0.1:5002/admin/login
- Username: `admin`
- Password: the value of `ADMIN_PASSWORD`, or the fallback `admin123` if
  `ADMIN_PASSWORD` is not set.

> **MUST-CHANGE WARNING:** `admin123` is a first-run fallback only. The
> dashboard shows a prominent warning banner until you change it. Change it
> in **Admin → Settings → Change Password** (minimum 8 characters), and set
> a strong `ADMIN_PASSWORD` + `SECRET_KEY` in the environment on the server.
> Never commit real secrets to the repo.

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Flask session secret | Random per-run key (with a warning) — set a fixed one in production |
| `ADMIN_PASSWORD` | First-run admin password | `admin123` fallback (change immediately) |
| `PORT` | Port to listen on | `5002` |

## Push to GitHub

```bash
git init
git add .
git commit -m "Initial portfolio website"
git remote add origin https://github.com/pythonicshariful/PythonicShariful-Portfolio.git
git branch -M main
git push -u origin main
```

The database (`instance/`, `*.db`) and `.env` are gitignored — they are never
pushed. Clone on the server and let the app create/seed its own database.

## Deploy on Ubuntu VPS (gunicorn + systemd + nginx, port 5002)

On the VPS (same pattern as the other Flask apps on this server):

```bash
cd /var/www
git clone https://github.com/pythonicshariful/PythonicShariful-Portfolio.git
cd PythonicShariful-Portfolio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `/etc/systemd/system/pythonic-shariful.service`:

```ini
[Unit]
Description=Pythonic Shariful Portfolio
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/PythonicShariful-Portfolio
Environment="SECRET_KEY=<generate-a-long-random-secret>"
Environment="ADMIN_PASSWORD=<choose-a-strong-password>"
Environment="PORT=5002"
ExecStart=/var/www/PythonicShariful-Portfolio/.venv/bin/gunicorn -w 2 -b 127.0.0.1:5002 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now pythonic-shariful.service
sudo systemctl status pythonic-shariful.service
```

nginx snippet (inside your `server { ... }` block for the domain):

```nginx
location / {
    proxy_pass http://127.0.0.1:5002;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Then `sudo nginx -t && sudo systemctl reload nginx`. Get a certificate with
certbot as usual for the domain. After first login, change the admin password
in Admin → Settings.

## Project structure

```
app.py                  Flask app: DB helpers, auth, public + admin routes, seed
config.py               Env-var reference (app.py reads env directly)
requirements.txt        Flask, Werkzeug, gunicorn
templates/              base, index, about, services, projects,
                        project_detail, contact, 404, 500
templates/admin/        base, login, dashboard, projects, project_form,
                        services, service_form, skills, messages, settings
static/css/             main.css, admin.css
static/js/              main.js (nav, reveal, stats count-up), admin.js
instance/site.db        SQLite DB (created on first run, gitignored)
```
