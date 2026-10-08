# LLVP – värmepumpsplanerare

Räknar varje dag fram en måltemperatur per timme för luft/luft-värmepumpen (Mitsubishi Hero 2.0 LN25, stuga vid Björka fäbod, elområde SE3) utifrån spotpris och väderprognos.

**Status: torrkörning.** Planen skrivs till `plans/latest.md` och `plans/latest.json`. Ingenting skickas till MELCloud Home.

## Logik
- Grundtemperatur 14 °C, aldrig under 12 °C eller över 16 °C (`config.json`).
- Billigaste tredjedelen av timmarna: förvärm (+2 °C). Dyraste tredjedelen: sänk (−2 °C).
- Små prisskillnader (< 0,10 kr/kWh mellan billig och dyr nivå): håll grundtemperaturen.
- Under −10 °C ute sänks inte temperaturen på dyra timmar.

## Källor
- Spotpris: [elprisetjustnu.se](https://www.elprisetjustnu.se/elpris-api)
- Väder: [Open-Meteo](https://open-meteo.com/)

## Körning
```bash
python3 plan.py                      # lokalt
python3 -m unittest discover -s tests
```
GitHub Actions (`.github/workflows/plan.yml`) kör det dagligen ca 14:30 svensk tid och sparar planen i repot. Kan även startas manuellt under fliken Actions.

## Nästa steg
Koppla på styrning mot MELCloud Home (kräver att vi först verifierar vilket inofficiellt API som kan skriva scheman).
