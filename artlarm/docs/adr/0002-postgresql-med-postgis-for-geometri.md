---
status: accepted
---

# PostgreSQL med PostGIS för geometri och skärningar

Prototypen använder SQLite och räknar geometri i Python (shapely) mot en 69 MB stor fil. Produkten ska lagra en geometri per bevakning (ögonblicksbild vid köp, P16), skära fastigheter mot Skogsstyrelsens 129 997 avverkningsanmälningar och söka rumsligt, så vi väljer PostgreSQL med PostGIS på RDS och gör skärningar och områdessökningar i databasen.

## Considered Options

- **SQLite och shapely mot fil:** fungerar för en användare men ger inget delat tillstånd mellan processer och inget rumsligt index vid många bevakningar. Valdes bort för att flera processer ska dela samma data och undvika dubblettnotiser.

## Consequences

- Datamodellen och sökningarna byggs kring rumsliga frågor, vilket gör ett senare byte av databas dyrt.
- Kräver att PostGIS-tillägget stöds på den hanterade databasen (RDS gör det).
