# Artbevakning

Betaltjänst som skickar notiser till kunder per e-post när en artobservation görs på en bevakad fastighet eller på ytor med avverkningsanmälan. Glossariet är gemensamt språk för produktkraven (PRD:n) och koden.

## Language

### Kunden och köpet

**Kund**:
Företaget eller yrkesutövaren som köper bevakningar och äger ett konto.
_Avoid_: Användare, köpare, ägare, kontoinnehavare

**Konto**:
Kundens inloggning och inställningar, knutna till kundens organisationsnummer som anges vid registreringen tillsammans med intyget om näringsverksamhet. Notiser och sammanfattning går till kontots e-postadress, som är den enda mottagaren.
_Avoid_: Profil

**Varukorg**:
De bevakningar, kompletteringar och förlängningar som kunden betalar i ett enda köp.
_Avoid_: Order

**Grundpris**:
Priset i kronor per hektar och dag, exklusive moms, som en administratör kan ändra.
_Avoid_: Taxa, dagspris

**Beloppstak**:
Den hårda gräns för varukorgens fullpris före rabatt som inte får överskridas i ett köp.
_Avoid_: Maxbelopp, spärr

**Rabattkod**:
En kod med en procentuell rabatt på varukorgens belopp.
_Avoid_: Kupong, kampanjkod

**Erbjudande**:
En tidsbegränsad procentuell rabatt som gäller alla kunder automatiskt, utan kod, och som en administratör skapar med start och slut.
_Avoid_: Kampanj, utförsäljning

**Förstagångsrabatt**:
En procentuell rabatt på ett organisationsnummers första genomförda köp.
_Avoid_: Välkomstrabatt, nykundsrabatt

### Bevakningen

**Bevakning**:
Det kunden köper: en fastighet, en bevakad yta och en bevakningsperiod som ger notiser om observationer. Vid avverkningsval består den av en rad per vald avverkningsanmälan.
_Avoid_: Prenumeration, abonnemang

**Fastighet**:
En registerenhet hos Lantmäteriet, identifierad med fastighetsbeteckning.
_Avoid_: Skifte, område

**Bevakad yta**:
Den del av fastigheten som en bevakning gäller: hela fastigheten eller de valda avverkningsanmälningarnas ytor. Fastställs vid köp.
_Avoid_: Bevakningsområde

**Bevakningsperiod**:
Tiden, med start- och slutdatum, som en bevakning gäller. Vid avverkningsval har varje rad sin egen bevakningsperiod. Priset räknas på alla dagar i perioden.
_Avoid_: Larmperiod

**Rad**:
Vid avverkningsval den del av en bevakning som gäller en vald avverkningsanmälan, med egen yta, bevakningsperiod, status och pris. En bevakning av hela fastigheten har ingen rad.
_Avoid_: Delbevakning, underbevakning

**Avverkningsanmälan**:
En anmälan om avverkning till Skogsstyrelsen, med en yta och ett inkomdatum.
_Avoid_: Anmälan, avverkningsyta

**Komplettering**:
Tillägg av nya avverkningsanmälningar som nya rader i en pågående bevakning, var och en med egen bevakningsperiod, mot betalning.
_Avoid_: Tillägg

**Förlängning**:
Senareläggning av slutdatum för en bevakning, eller vid avverkningsval för en eller flera rader, mot betalning för tillkommande dagar.
_Avoid_: Förnyelse

### Notiserna

**Observation**:
Ett publikt fynd av en art, med plats och tidpunkt, som tjänsten hämtar från Artdatabanken.
_Avoid_: Fynd, rapport

**Notis**:
Ett mejl som meddelar kunden om nya observationer på en bevakad yta; en notis per kontroll och bevakning.
_Avoid_: Larm, alert, meddelande

**Källa**:
Ett register som levererar observationer, till exempel Artportalen eller iNaturalist. Varje notis anger observationens källa.
_Avoid_: Leverantör, dataset

**Kontroll**:
En omgång där tjänsten söker efter nya observationer för alla aktiva bevakningar. En notis skickas för en bevakning om kontrollen hittar något nytt.
_Avoid_: Körning, poll

**Startrapport**:
Den första notisen vid köp, som samlar alla träffar från bevakningsperiodens start till nu.
_Avoid_: Första notis

**Sammanfattning**:
Ett dygnsmejl kl 09:00 till kontot som listar kontots aktiva bevakningar och deras notiser sedan förra sammanfattningen.
_Avoid_: Dagsrapport

**Licensfilter**:
Regeln som avgör vilka observationer som får ge notis utifrån observationens licens.
_Avoid_: Källfilter

### Drift och intäkt

**Administratör**:
Person hos tjänsten som hanterar rabattkoder, grundpris, beloppstak, licensfilter och annonser.
_Avoid_: Admin, superanvändare

**Annons**:
Reklam som visas på en annonsplats i kundens webbgränssnitt, aldrig i köp- eller bekräftelsesteg.
_Avoid_: Banner, sponsring
