"""Konfiguration via miljövariabler."""
import os
from pathlib import Path

# Läs .env (KEY=värde) bredvid denna fil; riktiga miljövariabler har företräde.
_env = Path(__file__).with_name(".env")
if _env.exists():
    for _line in _env.read_text().splitlines():
        _k, _, _v = _line.strip().partition("=")
        if _k and _v and not _k.startswith("#"):
            os.environ.setdefault(_k, _v)

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

# Lantmäteriets OGC API Features (fastighetsindelning), Basic-autentisering.
LM_BASE_URL = os.environ.get(
    "LM_BASE_URL", "https://api.lantmateriet.se/ogc-features/v1/fastighetsindelning"
)
LM_CONSUMER_KEY = os.environ.get("LM_CONSUMER_KEY", "")
LM_CONSUMER_SECRET = os.environ.get("LM_CONSUMER_SECRET", "")

# E-post via SMTP. Utan SMTP_HOST loggas e-post bara (torrkörning).
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))  # STARTTLS
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "artlarm@localhost")

# Fynd utanför fastighetsgränsen men inom positionens osäkerhet larmas som "osäkert läge",
# så länge osäkerheten är högst så här många meter. ARTLARM_CONSIDER_ACCURACY=0 stänger av.
CONSIDER_ACCURACY = os.environ.get("ARTLARM_CONSIDER_ACCURACY", "1") != "0"
MAX_UNCERTAINTY_M = float(os.environ.get("ARTLARM_MAX_UNCERTAINTY_M", "500"))

# Max antal enskilda SMS per fastighet och körning; resten sammanfattas i ett SMS.
MAX_SMS_PER_RUN = int(os.environ.get("ARTLARM_MAX_SMS_PER_RUN", "20"))

ARTPORTALEN_SIGHTING_URL = "https://www.artportalen.se/Sighting/{id}"
