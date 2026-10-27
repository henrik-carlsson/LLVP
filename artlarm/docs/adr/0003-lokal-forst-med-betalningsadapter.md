# Köra lokalt först, med en betalningsadapter och simulerad betalning

Tjänsten byggs så att den körs lokalt med Docker Compose (webb, arbetsprocess, PostgreSQL med PostGIS och en mejlfångare) med samma containerbilder som på AWS. Betalning går genom en adapter med två lägen, simulerad betalning och Stripe, och den simulerade kassan skickar samma webhook-händelser som Stripe så att aktivering sker genom samma flöde. Skiftet till Stripe i testläge och sedan skarpt läge sker bara via konfiguration, och tjänsten vägrar starta om simulerad betalning och skarpa Stripe-nycklar är påslagna samtidigt.

## Considered Options

- **Bygga direkt mot Stripe i testläge:** avvisades som första steg eftersom det kräver konto, nycklar och webhook-vidarebefordran innan något går att prova, och eftersom felfall (misslyckad betalning, försenad webhook) är svåra att framkalla på beställning.
- **Aktivera bevakningen direkt vid köp i den simulerade kassan:** avvisades eftersom aktiveringen då skulle prövas genom en annan väg än den skarpa. Webhook-aktivering (B6) är den enda vägen.
