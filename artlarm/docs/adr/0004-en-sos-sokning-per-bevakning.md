# En SOS-sökning per bevakning, filtrering per rad i egen databas

Varje kontroll gör en sökning mot Artdatabankens SOS per bevakning, över de aktiva radernas samlade yta och tidigaste startdatum. Filtreringen på yta och period per rad görs efteråt i tjänstens egen databas, och utgångna rader ingår inte i sökningen. Antalet anrop är beroende av API-kvoten, som inte är känd (PRD avsnitt 7), så antalet sökningar ska växa med antalet bevakningar och inte med antalet rader.

## Considered Options

- **En sökning per rad:** enklare att förstå, men antalet anrop växer med antalet avverkningsanmälningar och kan nå kvoten tidigt, eftersom en kund kan välja många anmälningar i samma bevakning.
- **En sökning per fastighet och kontroll, delad mellan kunder:** hade minskat anropen mer, men bryter mot att varje bevakning har egen period och egna rader, och skulle göra felsökning och kundens integritet svårare.
