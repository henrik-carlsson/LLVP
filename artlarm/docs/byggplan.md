# Byggplan: Artbevakning, första lösningen

Planen bygger hela version 1 som den första lösningen i PRD:ns fas 0b: lokalt på Mac eller Linux med Docker Compose, simulerad Stripe och simulerad Bokio, för fastigheter i Dalarna (D12, D13, D18–D20). Stripe i testläge, AWS och lansering (PRD fas 1–4) kommer efter och berörs bara i slutet. Underlag: [PRD.md](PRD.md), ADR 0001–0005 och [CONTEXT.md](../CONTEXT.md). Prototypen används inte.

Varje steg slutar i något som går att köra och visa, och är klart när de angivna acceptanskriterierna i PRD avsnitt 10 har automatiska tester som går igenom. Stegen ligger i beroendeordning; steg som inte beror på varandra står markerade och kan göras parallellt.

## Före start

**Beslut som behövs (förslag i kursiv):**

1. **Teknik.** Beslutat i [ADR 0006](adr/0006-django-med-geodjango-och-serverrenderade-sidor.md): Python 3.12, Django 5.2 med GeoDjango, serverrenderade sidor med htmx, arbetsprocessen som ett eget Django-kommando med databaslås, pytest med pytest-django.
2. **Var koden ska ligga.** *Ett nytt repo `artbevakning`, så att prototypen och utredningsfilerna i LLVP inte blandas in. PRD, ADR och CONTEXT.md flyttas dit.*
3. **Reklamplatserna (avsnitt 16, R1–R9).** Avsnittet är fortfarande ett förslag. *Ingår inte i första lösningen; platserna läggs till när reklambeslutet tas.*

**Rättat i PRD:n:** acceptanskriterierna för P13 och P14 följer nu förval per rad, D10 är ersatt av D22, och avsnitt 9 nämner organisationsnummer i stället för telefonnummer.

## Steg

| Steg | Innehåll | Krav | Klart när | Storlek | Modell |
| --- | --- | --- | --- | --- | --- |
| 1. Skelett och lokal körning | Docker Compose med webb, arbetsprocess, PostGIS och Mailpit; skript för installation, start, stopp och rensning; konfiguration via miljövariabler och `.env`; klocka som kan ställas fram; databasmigreringar; spärren mot simulerad betalning med skarpa nycklar; märket "simulerad betalning"; automatisk testkörning (CI) på Linux | D12, D15, D16, D18, D22 | Ett tomt skal startar med ett kommando på Mac (Apple-silikon) och i CI på Linux (x86-64); start med skarpa Stripe-nycklar och simulerad betalning avbryts | S | Sonnet 5.5 |
| 2. Konto och inloggning | Registrering med organisationsnummer, intyg och båda godkännandena med version; e-postverifiering och lösenordsåterställning via Mailpit; adressbyte med meddelande till gamla adressen; begränsning av inloggningsförsök; administratörsroll med tvåfaktor och loggning av alla åtgärder; IP-adresser i loggar högst 30 dagar | K1–K10, M1, M2, A1, A6, D23 | Kriterierna för K7/K8, B10 (registreringen), A1, M1 och K9/K10 | M | Opus 5.5 |
| 3a. Fastighet och område | Uppslag mot Lantmäteriet bland Dalarnas 15 kommuner med begripligt fel; Forestand-fil och GeoJSON; areal, kommun och beteckning visas; länet som inställning | P2, P6, D20 | Oxberg 95:1 och Östra Storbyn 85:1 slås upp; en fastighet utanför Dalarna avvisas | M | Sonnet 5.5 |
| 3b. Avverkningsanmälningar | Nattlig hämtning av Skogsstyrelsens fil, filtrerad på Dalarna, till PostGIS; nya och försvunna ytor upptäcks via OBJECTID; skärning mot fastighet med areal, typ och skogstyp | P3 (data), P13 (lista), P19 (upptäckt), D2 | Oxberg 95:1 ger tre anmälningar (3,7 ha) och Östra Storbyn 85:1 två (12,6 ha), som i PRD avsnitt 7 | M | Opus 5.5 |
| 3c. Observationer | Klient mot SOS med licensfältet, uppdelning i tidsfönster över 10 000 träffar, begränsning till länet; inspelade svar för tester | D8, D16, L6 (data) | Testerna går utan nät och nycklar | S | Sonnet 5.5 |
| 4. Bevakning och varukorg | Datamodell för bevakning och rader; perioder och förval per rad; varning över 3 månader; ytavrundning och pris i öre; grundpris; tak och minsta belopp; köpsspärr vid 0 ha; varukorg i 7 dagar med prislås vid kassan; ögonblicksbild vid köp; sidorna Ny bevakning och Varukorg, också på mobil | P1, P3–P5 (pris), P7, P8, P12–P18, B1–B4, B9, B11, B16, B17, A4, D17 | Kriterierna för P4, P13, P14, P17/P18 och B16; skärmbild 2 och 3 ger samma belopp (301,60 kr och 1 049,60 kr) | L | Opus 5.5 för modell och pris, Sonnet 5.5 för sidorna |
| 5. Betalning och bokföring | Betalningsadapter med simulerad kassa ("Betala", "Misslyckad betalning") som skickar Stripe-liknande webhooks; idempotent aktivering av hela varukorgen eller inget; köp på 0 kr; faktura per bevakning och rad med moms, mejlad; avstämning av uteblivet besked; Bokio-adapter med simulerat läge, verifikat per faktura och avgift, BAS-konton som inställning, CSV | B5–B8, B10, B15, B17, D11 (betalning), D13, D19, ADR 0003 | Kriterierna för B4/B6, B17 och D12–D15; ett köp ger faktura, mejl och verifikat | L | Opus 5.5 |
| 6. Rabatter | Rabattkoder; erbjudanden med tid; förstagångsrabatt per organisationsnummer med kontroll mot bokföringsunderlaget; en rabatt per köp; återställning vid återbetalning; administratörens sidor för detta | B13–B15, B18–B22, A2, A3, A5, A8–A10, K10 (rabatt) | Kriterierna för B13/A2/A4 och B18–B21 | M | Opus 5.5 |
| 7. Kontroll och notiser | Kontroll var 15:e minut i arbetsprocessen med lås; en SOS-sökning per bevakning och filtrering per rad; reglerna O1–O9 inklusive osäkert läge och 14 dagar efter slut; licensfilter som administratören styr; startrapport; ett mejl per bevakning och kontroll; 50 i mejlet och resten som CSV; inga dubbletter, omförsök; ikappkörning efter avbrott; mejl om källavbrott över 24 timmar | L1–L10, O1–O9, P5, D2–D4, D11, D21, T4 | Kriterierna för L2, L6, L7/O8, L8/L9, P3 (notiser), P17 och D21 | L | Opus 5.5 |
| 8. Nya avverkningsanmälningar | Informationsmejl om nya ytor i aktiva bevakningar; markering vid inloggning; komplettering via varukorgen; utgången rad läggs till igen; markering när en anmälan försvunnit | P9–P11, P15, P19 | Kriterierna för P8–P12 och P19 | M | Sonnet 5.5 |
| 9. Sammanfattning *(kan göras parallellt med 8)* | Val på kontot; ett mejl per konto kl 09:00 svensk tid, även utan nya notiser | S1–S4 | Kriteriet för S3, och sommartidsbytet ger fortfarande 09:00 | S | Sonnet 5.5 |
| 10. Mina bevakningar och avslut | Lista med status per bevakning och rad (aktiv, delvis utgången, utgången); förlängning per rad; borttagning med bekräftelse; utgångna döljs efter 12 månader; kontoavslut med bekräftelse | H1–H7, K6 | Kriterierna för H2, H4/H5, K6 och B17/H7 | M | Sonnet 5.5 |
| 11. Statistik och administratörsinsyn *(kan göras parallellt med 8–10)* | Sidvisningar utan kakor och IP, anonymt id per dygn; händelser per konto; tratt och nyckeltal för administratören; gallring; supportinsyn med loggning | T1–T8, A7 | Kriterierna för T1–T8 och A7 | M | Sonnet 5.5 |
| 12. Godkännande av första lösningen | Genomgång av hela acceptanstabellen; installation på en ren Mac och en ren Linux-maskin; mobil och iPad; säkerhetsgranskning; README med installation | D17, D18, alla | Fas 0b i PRD:n uppfylld | M | Opus 5.5 för granskningen |

Storlek är relativ (S, M, L), inga timmar; PRD:n har inga datum.

## Arbetssätt

- **Testerna först.** Varje acceptanskriterium i PRD avsnitt 10 blir ett eller flera automatiska tester med krav-ID i namnet (till exempel `test_p17_fynd_utanfor_radens_period_ger_ingen_notis`). Siffrorna i skärmbilderna används som facit.
- **Klockan styrs i testerna.** Allt som beror på tid (15 minuter, kl 09:00, 7 dagar, 14 dagar, 12 och 13 månader) läser tjänstens klocka, så att det går att pröva utan att vänta (D16).
- **Inga riktiga anrop i testerna.** SOS, Lantmäteriet och Skogsstyrelsen körs mot inspelade svar; riktiga nycklar finns bara i `.env` och används för hand.
- **Ordet i glossariet gäller.** Kod, tabeller och texter använder CONTEXT.md: bevakning, rad, notis, kontroll, kund, konto. "Larm", "prenumeration" och "användare" används inte.
- **Modellval.** Opus 5.5 för steg där fel blir dyra och svåra att se (konton, pris, betalning, rabatter, notiser); Sonnet 5.5 för resten. Fable 5.1 är ett alternativ för steg 4, 5 och 7 om Opus 5.5 inte räcker.

## Efter första lösningen

Dessa delar ligger utanför planen men beror på saker som kan startas redan nu.

| Del | Krav | Kan startas nu |
| --- | --- | --- |
| Stripe i testläge | D14, B7 (Stripe Invoicing och Stripe Tax) | Skapa Stripe-konto när bolaget finns |
| Drift på AWS | D1, D5–D9, mätetal i avsnitt 10 | Bolag, domän och AWS-konto |
| Riktiga Bokio | D19 | Fråga Bokio om integrationstyp; bokföraren fastställer kontoplanen |
| Fler län än Dalarna | D20 | Inget, det är en inställning |
| Juridik och lansering | Avsnitt 9 och 14, fas 4 | Juristen kan börja med villkor, policy, licensfrågor och kakfri statistik |

**Externa frågor som kan stoppa lansering men inte bygget:** Artdatabankens villkor för kommersiell användning och API-kvot; Lantmäteriets avtal; vad Skogsstyrelsens två klasser betyder; Bokios integrationstyp; supportadressen.
