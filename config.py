"""Optional config helper — app.py reads env vars directly.

Environment variables:
  SECRET_KEY       Flask session secret (required in production)
  ADMIN_PASSWORD   First-run admin password (default fallback: admin123)
  PORT             Port to listen on (default 5002)
  FLASK_ENV        Set to "production" on the VPS
"""
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
PORT = int(os.environ.get("PORT", "5002"))
