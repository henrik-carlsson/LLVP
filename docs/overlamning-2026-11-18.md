# Överlämning till ny session, 2026-11-18

Sammanfattning av det som rörde repot LLVP i en lång session som sedan flyttade till repot artbevakning. Skriven som utgångspunkt för en ny session mot LLVP.

## Vad LLVP är

Två oberoende saker ligger i repot `henrik-carlsson/LLVP`:

1. **Värmepumpsplaneraren** (repots egentliga syfte). Räknar varje dag fram en måltemperatur per timme för luft/luft-värmepumpen Mitsubishi Hero 2.0 LN25 i stugan vid Björka fäbod (elområde SE3, lat 60,95 / lon 14,55) utifrån spotpris (elprisetjustnu.se) och väderprognos (Open-Meteo). Status: **torrkörning**, inget styrs. Filer: `plan.py`, `config.json`, `simulate.py`, `sensitivity.py`, `lookahead.py`, `ceiling.py`, `hourly_stats.py`, `chart.py`, `tests/test_plan.py`, resultat i `plans/` och `sim/`.
2. **Mappen `artlarm/`**: den första prototypen av det som blev tjänsten Artbevakning. Behålls i LLVP för att prototypen finns där; allt vidare arbete sker i repot `henrik-carlsson/artbevakning` (PRD, glossarium, ADR, Django-tjänst).

## Värmepumpsplaneraren: logik och läge

- Grundtemperatur 14 °C, aldrig under 12 eller över 16 (`config.json`). Billigaste tredjedelen av timmarna: förvärm +2 °C. Dyraste tredjedelen: sänk −2 °C. Liten prisskillnad (< 0,10 kr/kWh): håll grundtemperaturen. Under −10 °C ute: ingen sänkning.
- 2026-10-31 (i den här sessionen): **förvärmning inför kyla med prognos framåt** och **simulering av prognosfel** (`f4721b4`, `15ac4db`, `68ea525`). Nya inställningar: `forecast_days` 5, `lookahead_hours` (0 = av), `cold_trigger_c` −8, `precold_preheat_c` +6, `precold_mode` "all", samt `simulation.forecast_sd_base_k`/`forecast_sd_per_hour_k`/`forecast_seed`. Simuleringen för januari 2026 (`sim/2026-01-lookahead.md`) visar ca 8–9 % besparing mot konstant 14 °C, bäst vid 24–48 h horisont; osäker prognos kostar ungefär en procentenhet. Framförhållningen är avstängd i `config.json` (`lookahead_hours: 0`) tills styrningen är på riktigt.
- Daglig körning: GitHub Actions-jobbet **"Daglig plan (torrkörning)"** (`.github/workflows/plan.yml`) kl 12:30 UTC kör testerna, `plan.py`, och committar `plans/latest.md` och `plans/latest.json` som "Ny plan ÅÅÅÅ-MM-DD".
- **Jobbet är avstängt sedan 2026-11-17** (`gh workflow disable`, status disabled_manually) efter ett misslyckande 2026-11-16: TLS-handskakningen mot api.open-meteo.com fick timeout. Orsaken var tillfällig; `fetch_json` i `plan.py` gör bara ett försök utan omförsök. Slå på igen med `gh workflow enable "Daglig plan (torrkörning)" --repo henrik-carlsson/LLVP`, gärna efter att omförsök lagts in.
- Nästa steg enligt README: koppla styrning mot MELCloud Home, vilket först kräver att det inofficiella API:t som kan skriva scheman verifieras.
- Lokala klonen `/Users/henrikcarlsson/workspace_privat/LLVP` låg 2026-11-18 på `68ea525`, 16 commits (alla "Ny plan") efter `origin/main`. Börja med `git pull`.

## Artlarm-prototypen (oktober 2026)

- Byggd 2026-10-09 till 2026-10-22 som FastAPI-app (`artlarm/app.py`) med SQLite, SOS-API (Artdatabanken) för artfynd, Lantmäteriets fastighetsindelning för fastighetsgeometri, Forestand-filer som alternativ geometri, SMS via 46elks (aldrig aktiverat, bara loggat) och e-post via SMTP (one.com för mjukvaruverkstan.se). Markerar fynd med osäkert läge utanför fastigheten. Dygnssammanfattning kl 09:00 per e-postadress. Flera mottagare per prenumeration.
- Provkörd på Östra Storbyn 85:1 och Mora Oxberg 95:1. En bevakning för Oxberg 95:1 lades in med timvis polling och mejl till henrik.carlsson@mjukvaruverkstan.se och lars@gitcon.se, körd som **LaunchAgent** `se.mjukvaruverkstan.artlarm` (`~/Library/LaunchAgents/se.mjukvaruverkstan.artlarm.plist`, KeepAlive).
- **LaunchAgenten är fortfarande laddad** 2026-11-18. Loggen `artlarm/logs/artlarm.log` skrevs senast 2026-11-17 22:58 och visar fel ("Kunde inte polla fastighet 1"). Eftersom Artbevakning ersätter prototypen bör den avlastas: `launchctl unload ~/Library/LaunchAgents/se.mjukvaruverkstan.artlarm.plist`.
- Hemligheter (SOS-nyckel, LM-nycklar, SMTP) ligger i `artlarm/.env`, inte i repot. Samma nycklar används i artbevakning.
- PRD, glossarium (`CONTEXT.md`) och `docs/` för Artbevakning låg först i `artlarm/` men flyttades 2026-10-31 till repot artbevakning och togs bort här.

## Konventioner från sessionen

- Commit-meddelanden på svenska, i imperativ. Attributionsrad `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Inga hemligheter i chatt eller repo; `.env` är git-ignorerad.
- Repot ska ligga på kontot `henrik-carlsson` på GitHub (ett tidigt misstag hamnade på fel konto och rättades).
