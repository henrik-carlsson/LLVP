# Artlarm

SMS-larm när en artobservation (Artportalen via Artdatabankens SOS-API) görs på en bevakad fastighet.

## Köra
```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export SOS_API_KEY=...            # https://api-portal.artdatabanken.se/ (prenumerera på SOS)
export ELKS_USER=... ELKS_PASSWORD=...   # utan dessa loggas SMS bara (torrkörning)
export SMTP_HOST=... SMTP_USER=... SMTP_PASSWORD=... EMAIL_FROM=...   # e-post (STARTTLS, port SMTP_PORT=587); utan SMTP_HOST loggas den bara
.venv/bin/uvicorn app:get_app --factory --port 8000
```
Öppna http://localhost:8000. API: `POST/GET /api/subscriptions`, `DELETE /api/subscriptions/{id}`.

## Så fungerar det
- Ny prenumeration: bakåtblickande sökning från startdatum → larm direkt (max `ARTLARM_MAX_SMS_PER_RUN` enskilda, resten sammanfattas). Framtida startdatum väntar.
- Därefter pollas var `ARTLARM_POLL_SECONDS` (60 s) efter nya/ändrade fynd. Dubbletter förhindras per (fastighet, occurrenceId).
- Kanaler: telefonnummer (SMS), e-postadress eller båda per prenumeration. Misslyckas en kanal görs nytt försök, och den andra kanalen kan då få larmet en extra gång.
- Larmtext: `Art, ÅÅÅÅ-MM-DD TT:MM, Fastighet. <länk till Artportalen>`.

## Kända begränsningar
- **Fastighetsbeteckning → polygon är inte kopplad** (`fastighet.py`, `UnconfiguredResolver`); kräver Lantmäteriets API/avtal. Tills vidare anges GeoJSON-polygon.
- SOS-adaptern (`sos.py`) är byggd efter dokumentationen på GitHub men är **ej provkörd mot live-API** (ingen nyckel). Verifiera bas-URL, `skip/take` och svarsfältet `totalCount`.
- "Realtid" = polling; SOS filtrerar på ändringsdatum per dygn, inte klockslag. Skyddade/sekretessbelagda arter kräver inloggning och ingår inte.
- Ingen autentisering i webbgränssnittet/API:t – lägg bakom inloggning innan det exponeras.
