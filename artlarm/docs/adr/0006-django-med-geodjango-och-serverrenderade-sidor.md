---
status: accepted
---

# Django med GeoDjango och serverrenderade sidor

Tjänsten byggs i Python 3.12 med Django 5.2 (LTS) och GeoDjango mot PostgreSQL med PostGIS (ADR 0002). Sidorna renderas på servern med Djangos mallar och htmx för delar som uppdateras utan omladdning, till exempel pris per rad när datum ändras. Version 1 är i huvudsak formulär, inloggning, betalningsflöde och administration, och Django har konton, sessioner, lösenordsåterställning, formulärvalidering, CSRF-skydd, migreringar, rumsliga fält och ett administrationsgränssnitt inbyggt.

Arbetsprocessen (D3) är samma kodbas, startad som ett eget Django-kommando i en egen container. Den kör kontroller, sammanfattningar, nattlig hämtning av avverkningsanmälningar och betalningsavstämning, och använder PostgreSQL:s rådgivande lås så att bara en process kör varje jobb. Ingen meddelandekö behövs.

Övriga val: Argon2 för lösenord (K4); tvåfaktor för administratörer med django-otp (A1); administratörens sidor i Djangos administrationsgränssnitt, avstängt för kunder (A6); CSRF-token lagrad i sessionen i stället för i en egen kaka, så att bara inloggningens kaka sätts (T5); pytest med pytest-django; e-post genom Djangos e-postlager, till Mailpit lokalt och SES på AWS (D12, D1).

## Considered Options

- **FastAPI med SQLAlchemy:** bra för ett rent API, men inloggning, sessioner, CSRF, formulär och administration hade fått sättas ihop av flera bibliotek, och version 1 har inget API för andra klienter.
- **Ett separat ramverk för gränssnittet (React eller liknande):** mer kod och två byggen, utan krav som motiverar det. Mobil och iPad (D17) klaras med responsiva serverrenderade sidor.
- **Celery med Redis för bakgrundsjobb:** en extra tjänst att drifta lokalt och på AWS, för jobb som är få och tidsstyrda. Ett eget kommando med databaslås räcker.

## Consequences

- En framtida app (avsnitt 15.1) behöver ett API-lager, till exempel Django REST Framework eller Django Ninja, ovanpå samma modeller.
- Django 5.2 får säkerhetsuppdateringar till april 2028; byte till nästa LTS planeras före dess.
