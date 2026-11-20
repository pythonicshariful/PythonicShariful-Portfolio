"""
Pythonic Shariful — portfolio website (Flask, SQLite, no ORM).
Main website for Shariful Islam — Web Scraping & Automation Expert.
Run:  python app.py   (or: flask run / gunicorn app:app)
"""
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask, abort, flash, g, jsonify, redirect, render_template,
    request, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

# ---------------------------------------------------------------- config
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
DATABASE = os.path.join(INSTANCE_DIR, "site.db")

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)
    print("WARNING: SECRET_KEY env var not set — using a random key for this "
          "run only. Set SECRET_KEY in production or sessions will reset "
          "on every restart.")

ADMIN_PASSWORD_ENV = os.environ.get("ADMIN_PASSWORD")  # None => fallback
DEFAULT_ADMIN_PASSWORD = "admin123"  # first-run fallback ONLY; change it

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["DATABASE"] = DATABASE
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# ---------------------------------------------------------------- db
SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL DEFAULT 'automation',
    summary TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    tech TEXT NOT NULL DEFAULT '',
    image_url TEXT NOT NULL DEFAULT '',
    github_url TEXT NOT NULL DEFAULT '',
    live_url TEXT NOT NULL DEFAULT '',
    featured INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_published INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    icon TEXT NOT NULL DEFAULT 'code',
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_published INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Core',
    level INTEGER NOT NULL DEFAULT 80
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    project_type TEXT NOT NULL DEFAULT '',
    budget TEXT NOT NULL DEFAULT '',
    message TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS admin_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def slugify(text):
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "project"


def get_setting(key, default=""):
    row = get_db().execute(
        "SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key, value):
    db = get_db()
    db.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    db.commit()


# ---------------------------------------------------------------- seed data
SEED_SETTINGS = {
    "hero_title": "Web Scraping & Automation Expert",
    "hero_subtitle": "I'm Shariful, a Python developer from Dhaka. Since "
                     "January 2024 I've been building scrapers and bots on "
                     "Fiverr — the kind that have to work on the real site, "
                     "with real anti-bot checks, not just in a test folder.",
    "about_text": "I'm Shariful Islam. I graduated in Economics (BA, "
                  "Government Tolaram College, Narayanganj) and I work as "
                  "an accountant by day at Nexus River View in Dhaka. Since "
                  "January 2024 I've also been working freelance on Fiverr "
                  "as a Python developer. Most of my work is web scraping, "
                  "checkout and monitoring bots, and Flask web apps. I test "
                  "everything against the live site before I hand it over, "
                  "and if something can't be done reliably, I say so "
                  "upfront.",
    "email": "pythonicshariful@gmail.com",
    "facebook_url": "https://www.facebook.com/tanvirmahamud.shariful.3",
    "fiverr_url": "https://www.fiverr.com/pythonicshariful",
    "github_url": "https://github.com/pythonicshariful",
    "linkedin_url": "https://www.linkedin.com/in/pythonicshariful141/",
}

SEED_PROJECTS = [
    {
        "title": "Microsoft Store Auto-Checkout Bot",
        "slug": "microsoft-store-auto-checkout-bot",
        "category": "automation",
        "summary": "Tampermonkey bot that watches Microsoft Store stock via the live stock API and DOM, with human-like delays and a guarded checkout flow.",
        "description": "A Python/Tampermonkey auto-checkout bot for the Microsoft Store. It checks stock through the live isInventoryAvailable API with DOM confirmation, uses random human-like delays, and keeps the final Place Order step armed only by an explicit panel checkbox. Built and iterated to v2.11 with harness tests; the stock check was live-proven on a real product page.",
        "tech": "Python, Tampermonkey, JavaScript, DOM Automation, Microsoft Stock API",
        "featured": 1, "sort_order": 1,
    },
    {
        "title": "Queue-Pass Bot",
        "slug": "queue-pass-bot",
        "category": "automation",
        "summary": "Multi-session queue automation with proxy rotation and live queue-position monitoring, with Discord updates.",
        "description": "A multi-session queue automation runner: each session runs in its own real browser session with its own proxy and profile, monitors queue position live, captures pass links and sends Discord updates. Achieved a first real live pass in a live sale period, and the two defects found live (proxies not being used, Dutch queue phrasing missed) were fixed the same day.",
        "tech": "Python, Playwright, Proxy Rotation, Discord Webhooks, Flask Dashboard",
        "featured": 1, "sort_order": 2,
    },
    {
        "title": "Lazada Restock Monitor Bot",
        "slug": "lazada-restock-monitor-bot",
        "category": "monitoring",
        "summary": "MTOP API polling with Telegram restock alerts and CAPTCHA-aware pausing, with sticky-proxy session hygiene.",
        "description": "A Lazada monitoring bot that polls stock through the MTOP API, sends Telegram alerts only on restock, pauses when a CAPTCHA appears, and keeps one sticky IP per session. Includes DOM asset blocking to keep checks fast and a panel that re-expands after a CAPTCHA clears.",
        "tech": "Python, Tampermonkey, MTOP API, Telegram Bot API, Webshare Proxy",
        "featured": 1, "sort_order": 3,
    },
    {
        "title": "Viagogo Listing Automation",
        "slug": "viagogo-listing-automation",
        "category": "automation",
        "summary": "Live event-page parser, heuristic opportunity scanner and Discord sale alerts for ticket listings.",
        "description": "A listing-automation system for Viagogo: a live parser for single-event pages, a 6-hour auto-collector, stealth browsing, NopeCHA support and a heuristic opportunity scanner with Discord alerts. Built as a smart opportunity system rather than blind bulk listing.",
        "tech": "Python, Selenium, NopeCHA, Discord Webhooks, Stealth Browsing",
        "featured": 0, "sort_order": 4,
    },
    {
        "title": "Real-Estate CRM",
        "slug": "real-estate-crm",
        "category": "web-app",
        "summary": "Flask + gunicorn CRM with lead management, Facebook leads polling and role-based access for admins and lead owners.",
        "description": "A production Flask CRM for a real-estate business: lead management, Facebook leads polling every 5 minutes, role-based access (admins see all leads, lead owners see only their own), events, calendar and an Android app. First organic leads were delivered to production in November 2026.",
        "tech": "Python, Flask, gunicorn, SQLite, Facebook Graph API, systemd",
        "featured": 0, "sort_order": 5,
    },
    {
        "title": "Nexus River View Accounts",
        "slug": "nexus-river-view-accounts",
        "category": "web-app",
        "summary": "Flask accounts app with an AI chatbot, voucher and category management, deployed on a VPS.",
        "description": "An accounts management web app for Nexus River View, built with Flask and deployed on Ubuntu with gunicorn and nginx. Includes vouchers, category management and an AI chatbot with a read-only, single-statement SQLite guard.",
        "tech": "Python, Flask, SQLite, gunicorn, nginx, AI Chatbot",
        "featured": 0, "sort_order": 6,
    },
    {
        "title": "Southeast Landmark CRM Android App",
        "slug": "southeast-landmark-crm-android-app",
        "category": "web-app",
        "summary": "Flutter Android app for the CRM with FCM push notifications, built phone-first for lead owners.",
        "description": "A Flutter Android app for the Southeast Landmark CRM, built phone-first because lead owners work from phones only. Includes full lead features, event reminders and Firebase Cloud Messaging push notifications for new leads, assignments and internal messages.",
        "tech": "Flutter, Dart, Firebase FCM, REST API, Android",
        "featured": 0, "sort_order": 7,
    },
    {
        "title": "Bangla Trainable AI",
        "slug": "bangla-trainable-ai",
        "category": "ai",
        "summary": "TF-IDF + Naive Bayes Bangla Q&A classifier and a tiny character-level transformer, both trained on CPU.",
        "description": "Two small, trainable Python AIs built from scratch: a TF-IDF + Naive Bayes Bangla Q&A classifier (13 Bangla cybersecurity Q&As, 6 intents, retrainable) and a tiny character-level transformer (TinyGPT, ~240K parameters, PyTorch on CPU) trained on a Bangla cybersecurity corpus.",
        "tech": "Python, scikit-learn, PyTorch, TF-IDF, Naive Bayes, NLP",
        "featured": 0, "sort_order": 8,
    },
]

SEED_SERVICES = [
    {
        "title": "Web Scraping & Data Extraction",
        "summary": "You tell me the site and the fields you need — I build the scraper and hand you clean CSV, JSON or Excel.",
        "description": "I build scrapers for shops, directories, marketplaces and listings. First I check the site: is it static, JavaScript-rendered, login-gated, or blocking bots? Then I build for that reality, with pagination, retries and clean output — CSV, JSON, Excel, or straight into your database.",
        "icon": "database", "sort_order": 1,
    },
    {
        "title": "Automation & Checkout Bots",
        "summary": "A bot that does the multi-step job for you — buying, booking or filling forms — and stops safely when it should.",
        "description": "Checkout and auto-purchase bots, form fillers and workflow automation. I build in human-like delays and session handling, and the final step — actually placing an order — is always guarded, so the bot never spends your money by accident. I test it on the live site before delivery.",
        "icon": "bot", "sort_order": 2,
    },
    {
        "title": "Monitoring & Restock Bots",
        "summary": "I watch the page for you and ping you on Telegram or Discord the moment stock, price or a listing changes.",
        "description": "Monitors that check stock, prices and new listings on a schedule and alert you on Telegram or Discord only when something actually changes. I tune the check speed and add CAPTCHA-aware pausing, so the monitor keeps running instead of getting blocked.",
        "icon": "bell", "sort_order": 3,
    },
    {
        "title": "Flask Web Apps & CRM",
        "summary": "A working web app or CRM on your VPS — leads, dashboards and logins included — not a half-finished demo.",
        "description": "Flask apps, lead-management CRMs and admin dashboards, deployed on Ubuntu with gunicorn, nginx and systemd and checked live. Role-based access, Facebook leads integration, and an Android app where the team works from phones.",
        "icon": "layout", "sort_order": 4,
    },
    {
        "title": "Data Pipelines & APIs",
        "summary": "Your data collected, cleaned and stored on a schedule, with a simple API or dashboard on top.",
        "description": "Pipelines that pull data from sites or APIs, clean and dedupe it, and store it on a schedule. You get a simple REST API or a dashboard to read it from, plus logging and retries — so a failed run gets noticed instead of going quiet.",
        "icon": "pipeline", "sort_order": 5,
    },
    {
        "title": "AI / ML Prototypes",
        "summary": "A small, trainable prototype — a classifier, a Bangla Q&A bot, a RAG demo — with an honest note on what it can and can't do.",
        "description": "Trainable text classifiers, Bangla NLP prototypes and small-model demos built with scikit-learn and PyTorch. I scope it honestly first: a prototype proves an idea, it is not ChatGPT, and I'll tell you that before we start.",
        "icon": "brain", "sort_order": 6,
    },
]

SEED_SKILLS = [
    ("Python", "Core", 95),
    ("Web Scraping", "Core", 95),
    ("Selenium / Playwright", "Automation", 92),
    ("Scrapy", "Automation", 90),
    ("Automation Bots", "Automation", 93),
    ("Flask", "Web", 88),
    ("REST APIs", "Web", 87),
    ("Data Pipelines / ETL", "Data", 86),
    ("Proxy Rotation & Anti-Bot", "Automation", 88),
    ("JavaScript / Tampermonkey", "Web", 84),
    ("SQLite / PostgreSQL", "Data", 82),
    ("Machine Learning / NLP", "AI", 75),
]

CATEGORIES = {
    "automation": "Automation Bots",
    "monitoring": "Monitoring Bots",
    "scraping": "Web Scraping",
    "web-app": "Web Apps & CRM",
    "ai": "AI / ML",
}


def init_db():
    """Create tables and seed only when empty — never wipe existing data."""
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()
    # admin user
    if db.execute("SELECT COUNT(*) c FROM admin_user").fetchone()["c"] == 0:
        password = ADMIN_PASSWORD_ENV or DEFAULT_ADMIN_PASSWORD
        db.execute(
            "INSERT INTO admin_user (username, password_hash) VALUES (?, ?)",
            ("admin", generate_password_hash(password)),
        )
        set_setting("admin_password_is_default",
                    "1" if ADMIN_PASSWORD_ENV is None else "0")
        if ADMIN_PASSWORD_ENV is None:
            print("WARNING: ADMIN_PASSWORD not set — first-run admin password "
                  "is the fallback 'admin123'. Change it immediately in "
                  "/admin/settings.")
    # settings
    for key, value in SEED_SETTINGS.items():
        if db.execute("SELECT COUNT(*) c FROM settings WHERE key = ?",
                      (key,)).fetchone()["c"] == 0:
            set_setting(key, value)
    # v2 content migration (2026-11-20): replace the v1 default copy with
    # the humanized copy, but ONLY where the stored value is still exactly
    # the v1 default — an admin edit is never overwritten. New keys (e.g.
    # facebook_url) are already handled by the seed loop above.
    _V1_SETTINGS = {
        "hero_subtitle": "I build Python bots, scrapers and web apps that work live — "
                         "not just in a demo. 5+ years turning repetitive, "
                         "manual work into reliable automation.",
        "about_text": "I'm Shariful Islam, a Python developer from Dhaka, "
                      "Bangladesh. Since January 2024 I have worked freelance on "
                      "Fiverr, building web scrapers, checkout and monitoring "
                      "bots, data pipelines and Flask web apps for clients "
                      "worldwide. I also work as an Accountant at Nexus River "
                      "View. My rule is simple: a bot is only done when it is "
                      "verified working live.",
    }
    for key, old in _V1_SETTINGS.items():
        row = db.execute("SELECT value FROM settings WHERE key = ?",
                         (key,)).fetchone()
        if row and row["value"] == old:
            set_setting(key, SEED_SETTINGS[key])
    _V1_SERVICES = {
        "Web Scraping & Data Extraction": (
            "Clean, structured datasets from any website — static, dynamic or API-driven.",
            "Custom scrapers for e-commerce, directories, marketplaces and social data. Handles JavaScript-rendered pages, pagination, login flows and anti-bot measures, and delivers clean CSV / JSON / Excel or straight into your database."),
        "Automation & Checkout Bots": (
            "Bots that buy, book or complete multi-step flows — with human-like behaviour.",
            "Auto-purchase and checkout bots, form fillers and workflow automation. Built with human-like delays, session handling and guarded final steps, and verified against the live site before delivery."),
        "Monitoring & Restock Bots": (
            "Know the second something changes — stock, price or a new listing.",
            "Fast polling monitors for stock, price drops and new listings, with Telegram / Discord alerts. CAPTCHA-aware pausing, proxy rotation and rate tuning keep the monitor running without getting blocked."),
        "Flask Web Apps & CRM": (
            "Production Flask apps, CRMs and dashboards, deployed on your VPS.",
            "Custom Flask web apps, lead-management CRMs, admin dashboards and APIs — built, deployed with gunicorn + nginx + systemd on Ubuntu, and verified live. Includes role-based access and third-party integrations such as Facebook leads."),
        "Data Pipelines & APIs": (
            "From raw pages to a clean API your team can actually use.",
            "ETL pipelines that collect, clean, dedupe and store data on a schedule, exposed through a simple REST API or dashboard. Includes logging, retries and monitoring so a failed run is noticed, not silent."),
        "AI / ML Prototypes": (
            "Small, trainable AI prototypes — classifiers, chatbots and RAG demos.",
            "Trainable text classifiers, Bangla NLP prototypes, small-model fine-tuning and RAG demos built with scikit-learn and PyTorch. Honest scoping: a prototype is a prototype, and I will tell you what it can and cannot do before we start."),
    }
    for s in SEED_SERVICES:
        old = _V1_SERVICES.get(s["title"])
        if old:
            db.execute(
                "UPDATE services SET summary = ?, description = ? "
                "WHERE title = ? AND summary = ? AND description = ?",
                (s["summary"], s["description"], s["title"], old[0], old[1]),
            )
    # projects
    if db.execute("SELECT COUNT(*) c FROM projects").fetchone()["c"] == 0:
        for p in SEED_PROJECTS:
            db.execute(
                "INSERT INTO projects (title, slug, category, summary, "
                "description, tech, featured, sort_order, is_published, "
                "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)",
                (p["title"], p["slug"], p["category"], p["summary"],
                 p["description"], p["tech"], p["featured"],
                 p["sort_order"], datetime.now(timezone.utc).isoformat()),
            )
    # services
    if db.execute("SELECT COUNT(*) c FROM services").fetchone()["c"] == 0:
        for s in SEED_SERVICES:
            db.execute(
                "INSERT INTO services (title, summary, description, icon, "
                "sort_order, is_published) VALUES (?, ?, ?, ?, ?, 1)",
                (s["title"], s["summary"], s["description"], s["icon"],
                 s["sort_order"]),
            )
    # skills
    if db.execute("SELECT COUNT(*) c FROM skills").fetchone()["c"] == 0:
        for name, cat, level in SEED_SKILLS:
            db.execute(
                "INSERT INTO skills (name, category, level) VALUES (?, ?, ?)",
                (name, cat, level),
            )
    db.commit()


# ---------------------------------------------------------------- csrf + auth
def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


def check_csrf():
    token = request.form.get("csrf_token", "")
    if not token or token != session.get("csrf_token"):
        abort(400, "Invalid form token. Please reload the page and try again.")


@app.context_processor
def inject_globals():
    try:
        settings = {r["key"]: r["value"] for r in
                    get_db().execute("SELECT key, value FROM settings")}
        unread = get_db().execute(
            "SELECT COUNT(*) c FROM messages WHERE is_read = 0"
        ).fetchone()["c"]
    except Exception:
        settings, unread = {}, 0
    return {
        "site": settings,
        "csrf_token": csrf_token,
        "unread_messages": unread,
        "categories": CATEGORIES,
        "now_year": datetime.now().year,
    }


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please log in to access the admin area.", "warning")
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------- public routes
@app.route("/")
def index():
    db = get_db()
    featured = db.execute(
        "SELECT * FROM projects WHERE is_published = 1 AND featured = 1 "
        "ORDER BY sort_order LIMIT 3").fetchall()
    services = db.execute(
        "SELECT * FROM services WHERE is_published = 1 "
        "ORDER BY sort_order LIMIT 6").fetchall()
    skills = db.execute("SELECT * FROM skills ORDER BY level DESC LIMIT 12"
                        ).fetchall()
    return render_template("index.html", featured=featured,
                           services=services, skills=skills)


@app.route("/about")
def about():
    skills = get_db().execute(
        "SELECT * FROM skills ORDER BY category, level DESC").fetchall()
    return render_template("about.html", skills=skills)


@app.route("/services")
def services():
    items = get_db().execute(
        "SELECT * FROM services WHERE is_published = 1 ORDER BY sort_order"
    ).fetchall()
    return render_template("services.html", services=items)


@app.route("/projects")
def projects():
    category = request.args.get("category", "")
    db = get_db()
    if category in CATEGORIES:
        items = db.execute(
            "SELECT * FROM projects WHERE is_published = 1 AND category = ? "
            "ORDER BY sort_order", (category,)).fetchall()
    else:
        category = ""
        items = db.execute(
            "SELECT * FROM projects WHERE is_published = 1 "
            "ORDER BY sort_order").fetchall()
    return render_template("projects.html", projects=items,
                           active_category=category)


@app.route("/projects/<slug>")
def project_detail(slug):
    project = get_db().execute(
        "SELECT * FROM projects WHERE slug = ? AND is_published = 1",
        (slug,)).fetchone()
    if project is None:
        abort(404)
    others = get_db().execute(
        "SELECT * FROM projects WHERE is_published = 1 AND id != ? "
        "ORDER BY sort_order LIMIT 3", (project["id"],)).fetchall()
    return render_template("project_detail.html", project=project,
                           others=others)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        check_csrf()
        # Honeypot: bots fill it, humans never see it.
        if request.form.get("website"):
            return render_template("contact.html", success=True)
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        project_type = request.form.get("project_type", "").strip()
        budget = request.form.get("budget", "").strip()
        message = request.form.get("message", "").strip()
        errors = {}
        if len(name) < 2:
            errors["name"] = "Please enter your name."
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            errors["email"] = "Please enter a valid email address."
        if len(message) < 10:
            errors["message"] = "Please tell me a little more (at least 10 characters)."
        if errors:
            return render_template("contact.html", errors=errors,
                                   form=request.form), 400
        db = get_db()
        db.execute(
            "INSERT INTO messages (name, email, project_type, budget, "
            "message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, project_type, budget, message,
             datetime.now(timezone.utc).isoformat()),
        )
        db.commit()
        return render_template("contact.html", success=True)
    return render_template("contact.html")


@app.route("/health")
@app.route("/api/health")
def health():
    try:
        get_db().execute("SELECT 1").fetchone()
        db_ok = True
    except Exception:
        db_ok = False
    return jsonify({"status": "ok" if db_ok else "error",
                    "database": "ok" if db_ok else "error"}), \
        200 if db_ok else 500


# ---------------------------------------------------------------- admin: auth
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        check_csrf()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        row = get_db().execute(
            "SELECT * FROM admin_user WHERE username = ?", (username,)
        ).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session["admin_logged_in"] = True
            session["admin_username"] = row["username"]
            flash("Welcome back.", "success")
            nxt = request.args.get("next") or url_for("admin_dashboard")
            return redirect(nxt if nxt.startswith("/admin") else
                            url_for("admin_dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    flash("Logged out.", "success")
    return redirect(url_for("index"))


# ---------------------------------------------------------------- admin: dashboard
@app.route("/admin")
@login_required
def admin_dashboard():
    db = get_db()
    stats = {
        "projects": db.execute("SELECT COUNT(*) c FROM projects"
                               ).fetchone()["c"],
        "services": db.execute("SELECT COUNT(*) c FROM services"
                               ).fetchone()["c"],
        "messages": db.execute("SELECT COUNT(*) c FROM messages"
                               ).fetchone()["c"],
        "unread": db.execute("SELECT COUNT(*) c FROM messages "
                             "WHERE is_read = 0").fetchone()["c"],
    }
    recent = db.execute(
        "SELECT * FROM messages ORDER BY id DESC LIMIT 5").fetchall()
    default_pw = get_setting("admin_password_is_default", "0") == "1"
    return render_template("admin/dashboard.html", stats=stats,
                           recent=recent, default_pw=default_pw)


# ---------------------------------------------------------------- admin: projects
@app.route("/admin/projects")
@login_required
def admin_projects():
    items = get_db().execute(
        "SELECT * FROM projects ORDER BY sort_order, id").fetchall()
    return render_template("admin/projects.html", projects=items)


@app.route("/admin/projects/new", methods=["GET", "POST"])
@login_required
def admin_project_new():
    return _project_form(None)


@app.route("/admin/projects/<int:pid>/edit", methods=["GET", "POST"])
@login_required
def admin_project_edit(pid):
    project = get_db().execute(
        "SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
    if project is None:
        abort(404)
    return _project_form(project)


def _project_form(project):
    db = get_db()
    if request.method == "POST":
        check_csrf()
        title = request.form.get("title", "").strip()
        slug = slugify(request.form.get("slug", "") or title)
        fields = (
            title, slug,
            request.form.get("category", "automation"),
            request.form.get("summary", "").strip(),
            request.form.get("description", "").strip(),
            request.form.get("tech", "").strip(),
            request.form.get("image_url", "").strip(),
            request.form.get("github_url", "").strip(),
            request.form.get("live_url", "").strip(),
            1 if request.form.get("featured") else 0,
            int(request.form.get("sort_order") or 0),
            1 if request.form.get("is_published") else 0,
        )
        if not title:
            flash("Title is required.", "error")
            return render_template("admin/project_form.html",
                                   project=project, form=request.form)
        try:
            if project is None:
                db.execute(
                    "INSERT INTO projects (title, slug, category, summary, "
                    "description, tech, image_url, github_url, live_url, "
                    "featured, sort_order, is_published, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    fields + (datetime.now(timezone.utc).isoformat(),))
                flash("Project created.", "success")
            else:
                db.execute(
                    "UPDATE projects SET title=?, slug=?, category=?, "
                    "summary=?, description=?, tech=?, image_url=?, "
                    "github_url=?, live_url=?, featured=?, sort_order=?, "
                    "is_published=? WHERE id=?", fields + (project["id"],))
                flash("Project updated.", "success")
            db.commit()
        except sqlite3.IntegrityError:
            flash("That slug is already used by another project.", "error")
            return render_template("admin/project_form.html",
                                   project=project, form=request.form)
        return redirect(url_for("admin_projects"))
    return render_template("admin/project_form.html", project=project,
                           form=None)


@app.route("/admin/projects/<int:pid>/delete", methods=["POST"])
@login_required
def admin_project_delete(pid):
    check_csrf()
    db = get_db()
    db.execute("DELETE FROM projects WHERE id = ?", (pid,))
    db.commit()
    flash("Project deleted.", "success")
    return redirect(url_for("admin_projects"))


# ---------------------------------------------------------------- admin: services
@app.route("/admin/services")
@login_required
def admin_services():
    items = get_db().execute(
        "SELECT * FROM services ORDER BY sort_order, id").fetchall()
    return render_template("admin/services.html", services=items)


@app.route("/admin/services/new", methods=["GET", "POST"])
@login_required
def admin_service_new():
    return _service_form(None)


@app.route("/admin/services/<int:sid>/edit", methods=["GET", "POST"])
@login_required
def admin_service_edit(sid):
    service = get_db().execute(
        "SELECT * FROM services WHERE id = ?", (sid,)).fetchone()
    if service is None:
        abort(404)
    return _service_form(service)


def _service_form(service):
    db = get_db()
    if request.method == "POST":
        check_csrf()
        title = request.form.get("title", "").strip()
        if not title:
            flash("Title is required.", "error")
            return render_template("admin/service_form.html",
                                   service=service, form=request.form)
        fields = (title,
                  request.form.get("summary", "").strip(),
                  request.form.get("description", "").strip(),
                  request.form.get("icon", "code").strip() or "code",
                  int(request.form.get("sort_order") or 0),
                  1 if request.form.get("is_published") else 0)
        if service is None:
            db.execute(
                "INSERT INTO services (title, summary, description, icon, "
                "sort_order, is_published) VALUES (?, ?, ?, ?, ?, ?)", fields)
            flash("Service created.", "success")
        else:
            db.execute(
                "UPDATE services SET title=?, summary=?, description=?, "
                "icon=?, sort_order=?, is_published=? WHERE id=?",
                fields + (service["id"],))
            flash("Service updated.", "success")
        db.commit()
        return redirect(url_for("admin_services"))
    return render_template("admin/service_form.html", service=service,
                           form=None)


@app.route("/admin/services/<int:sid>/delete", methods=["POST"])
@login_required
def admin_service_delete(sid):
    check_csrf()
    db = get_db()
    db.execute("DELETE FROM services WHERE id = ?", (sid,))
    db.commit()
    flash("Service deleted.", "success")
    return redirect(url_for("admin_services"))


# ---------------------------------------------------------------- admin: skills
@app.route("/admin/skills", methods=["GET", "POST"])
@login_required
def admin_skills():
    db = get_db()
    if request.method == "POST":
        check_csrf()
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "Core").strip() or "Core"
        try:
            level = max(0, min(100, int(request.form.get("level") or 80)))
        except ValueError:
            level = 80
        if not name:
            flash("Skill name is required.", "error")
        else:
            db.execute("INSERT INTO skills (name, category, level) "
                       "VALUES (?, ?, ?)", (name, category, level))
            db.commit()
            flash("Skill added.", "success")
        return redirect(url_for("admin_skills"))
    items = db.execute(
        "SELECT * FROM skills ORDER BY category, level DESC").fetchall()
    return render_template("admin/skills.html", skills=items)


@app.route("/admin/skills/<int:skid>/delete", methods=["POST"])
@login_required
def admin_skill_delete(skid):
    check_csrf()
    db = get_db()
    db.execute("DELETE FROM skills WHERE id = ?", (skid,))
    db.commit()
    flash("Skill deleted.", "success")
    return redirect(url_for("admin_skills"))


# ---------------------------------------------------------------- admin: messages
@app.route("/admin/messages")
@login_required
def admin_messages():
    items = get_db().execute(
        "SELECT * FROM messages ORDER BY id DESC").fetchall()
    return render_template("admin/messages.html", messages=items)


@app.route("/admin/messages/<int:mid>/read", methods=["POST"])
@login_required
def admin_message_read(mid):
    check_csrf()
    db = get_db()
    db.execute("UPDATE messages SET is_read = 1 WHERE id = ?", (mid,))
    db.commit()
    return redirect(url_for("admin_messages"))


@app.route("/admin/messages/<int:mid>/unread", methods=["POST"])
@login_required
def admin_message_unread(mid):
    check_csrf()
    db = get_db()
    db.execute("UPDATE messages SET is_read = 0 WHERE id = ?", (mid,))
    db.commit()
    return redirect(url_for("admin_messages"))


@app.route("/admin/messages/<int:mid>/delete", methods=["POST"])
@login_required
def admin_message_delete(mid):
    check_csrf()
    db = get_db()
    db.execute("DELETE FROM messages WHERE id = ?", (mid,))
    db.commit()
    flash("Message deleted.", "success")
    return redirect(url_for("admin_messages"))


# ---------------------------------------------------------------- admin: settings
@app.route("/admin/settings", methods=["GET", "POST"])
@login_required
def admin_settings():
    db = get_db()
    if request.method == "POST":
        check_csrf()
        for key in ("hero_title", "hero_subtitle", "about_text", "email",
                    "facebook_url", "fiverr_url", "github_url",
                    "linkedin_url"):
            set_setting(key, request.form.get(key, "").strip())
        current = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        if new_pw:
            row = db.execute(
                "SELECT * FROM admin_user WHERE username = ?",
                (session.get("admin_username", "admin"),)).fetchone()
            if not row or not check_password_hash(row["password_hash"],
                                                  current):
                flash("Site settings saved, but the password was NOT "
                      "changed — current password is incorrect.", "error")
                return redirect(url_for("admin_settings"))
            if len(new_pw) < 8:
                flash("Site settings saved, but the new password must be "
                      "at least 8 characters.", "error")
                return redirect(url_for("admin_settings"))
            db.execute(
                "UPDATE admin_user SET password_hash = ? WHERE username = ?",
                (generate_password_hash(new_pw),
                 session.get("admin_username", "admin")))
            db.commit()
            set_setting("admin_password_is_default", "0")
            flash("Settings saved and password changed.", "success")
        else:
            flash("Settings saved.", "success")
        return redirect(url_for("admin_settings"))
    return render_template("admin/settings.html")


# ---------------------------------------------------------------- errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


# ---------------------------------------------------------------- run
with app.app_context():
    init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5002"))
    app.run(host="127.0.0.1", port=port, debug=False)
