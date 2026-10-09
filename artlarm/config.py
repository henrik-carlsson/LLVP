"""Konfiguration via miljövariabler."""
import os

DB_PATH = os.environ.get("ARTLARM_DB", "artlarm.db")
POLL_SECONDS = int(os.environ.get("ARTLARM_POLL_SECONDS", "60"))

# Artdatabankens SOS-API. Nyckel hämtas på https://api-portal.artdatabanken.se/
SOS_BASE_URL = os.environ.get(
    "SOS_BASE_URL", "https://api.artdatabanken.se/species-observation-system/v1"
)
SOS_API_KEY = os.environ.get("SOS_API_KEY", "")

# 46elks. Utan nycklar skrivs SMS bara ut i loggen (torrkörning).
ELKS_USER = os.environ.get("ELKS_USER", "")
ELKS_PASSWORD = os.environ.get("ELKS_PASSWORD", "")
SMS_SENDER = os.environ.get("SMS_SENDER", "Artlarm")  # max 11 tecken

# E-post via SMTP. Utan SMTP_HOST loggas e-post bara (torrkörning).
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))  # STARTTLS
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "artlarm@localhost")

# Max antal enskilda SMS per fastighet och körning; resten sammanfattas i ett SMS.
MAX_SMS_PER_RUN = int(os.environ.get("ARTLARM_MAX_SMS_PER_RUN", "20"))

ARTPORTALEN_SIGHTING_URL = "https://www.artportalen.se/Sighting/{id}"
