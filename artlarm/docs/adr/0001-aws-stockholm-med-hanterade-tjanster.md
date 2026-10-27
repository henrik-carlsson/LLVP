---
status: accepted
---

# Körs på AWS i Stockholm med hanterade tjänster

Kravet var "egen server eller molntjänst". Vi kör på AWS i eu-north-1 (Stockholm) med containrar på ECS Fargate, PostgreSQL på RDS och e-post via SES. Skälet är att data stannar i EU och att ett litet team slipper egen serverdrift, backup och uppdateringar.

## Considered Options

- **Egen server eller VPS:** lägre löpande kostnad i grunden, men driftansvaret för uppdateringar, backup och tillgänglighet läggs på teamet. Valdes bort för att tjänsten tar betalt och ett avbrott ger missade notiser.

## Consequences

- Löpande kostnad ca 935 kr per månad i en liten start och ca 1 355 kr per månad med dubblerad databas (PRD avsnitt 17).
- Innehållet är containrar och vanlig PostgreSQL, så byte av leverantör är möjligt men tar tid. Mest låsta är SES och den hanterade databasen.
