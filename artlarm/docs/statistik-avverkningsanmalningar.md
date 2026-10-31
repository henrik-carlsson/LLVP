# Statistik: avverkningsanmälningar per år och region

Underlag för prissättning och företagsavtal (PRD avsnitt 15.3). Framtaget 2026-10-27 ur Skogsstyrelsens öppna fil [sksAvverkAnm_gpkg.zip](https://geodpags.skogsstyrelsen.se/geodataport/data/sksAvverkAnm_gpkg.zip) (CC0, 129 908 ytor, 129 781 ärenden) samt Skogsstyrelsens publicerade statistik.

## Viktigt om underlaget

- Filen innehåller inget om ägare. Fälten är län, kommun, ärendeår, beteckning, avverkningstyp, ändamål, skogstyp, inkomdatum och anmäld areal. Uppdelning på privatägd skog och bolag går alltså inte att göra ur filen; se avsnittet om ägare nedan.
- Filen når bara tillbaka till 2021-10-26 och ger lägre siffror än Skogsstyrelsens officiella statistik: för 2025 ger filen 29 725 ärenden och 111 983 ha, medan Skogsstyrelsen anger 241 646 ha föryngringsavverkning i normal skog. Orsaken är inte utredd. Använd därför siffrorna nedan för fördelning mellan län och storlekar, inte som absoluta årsvolymer.
- Filen har två klasser i fältet `AvverkningsanmalanKlass`: `Avverkningsamalan` (inkomdatum till och med 2026-09-14, 123 347 ytor) och `NyAvverkningsanmalan` (från 2026-09-15, 6 561 ytor). Takten är ungefär dubbelt så hög efter bytet, och skillnaden är inte utredd; siffror före och efter 15 september är därför kanske inte jämförbara.
- Ett ärende kan ha flera ytor; här är ytorna sammanlagda per ärende (beteckning).
- 2021 och 2026 är ofullständiga år (filen startar 26 okt 2021 och slutar 26 okt 2026).

## Per kalenderår (ur filen)

| År | Ärenden | Anmäld areal (ha) |
| --- | --- | --- |
| 2021 (från 26 okt) | 3 639 | 14 463 |
| 2022 | 17 745 | 59 551 |
| 2023 | 22 601 | 82 035 |
| 2024 | 21 615 | 76 850 |
| 2025 | 29 725 | 111 983 |
| 2026 (till 26 okt) | 34 456 | 142 525 |

Siffrorna för äldre år är sannolikt för låga eftersom äldre ärenden försvinner ur filen; senaste tolv månaderna är därför mest jämförbara.

## Per län, senaste tolv månaderna (27 okt 2025 – 26 okt 2026)

Totalt 41 255 ärenden och 168 830 ha; medianen är 2,3 ha, 90:e percentilen 9,0 ha och största ärendet 317 ha.

| Län | Ärenden | Areal (ha) | Genomsnitt (ha) |
| --- | --- | --- | --- |
| Västerbotten | 4 159 | 23 304 | 5,6 |
| Gävleborg | 5 642 | 22 033 | 3,9 |
| Jämtland | 2 971 | 17 782 | 6,0 |
| Norrbotten | 2 750 | 17 754 | 6,5 |
| Dalarna | 3 881 | 17 718 | 4,6 |
| Västernorrland | 3 795 | 13 955 | 3,7 |
| Värmland | 2 997 | 11 903 | 4,0 |
| Västra Götaland | 2 972 | 8 767 | 2,9 |
| Uppsala | 1 145 | 4 344 | 3,8 |
| Kalmar | 1 420 | 4 143 | 2,9 |
| Östergötland | 1 439 | 4 081 | 2,8 |
| Jönköping | 1 582 | 3 849 | 2,4 |
| Örebro | 1 161 | 3 608 | 3,1 |
| Kronoberg | 1 235 | 3 170 | 2,6 |
| Skåne | 1 051 | 2 988 | 2,8 |
| Västmanland | 699 | 2 318 | 3,3 |
| Södermanland | 637 | 2 050 | 3,2 |
| Halland | 690 | 1 822 | 2,6 |
| Stockholm | 458 | 1 612 | 3,5 |
| Blekinge | 481 | 1 304 | 2,7 |
| Gotland | 90 | 324 | 3,6 |

Sju län (Västerbotten, Gävleborg, Jämtland, Norrbotten, Dalarna, Västernorrland, Värmland) står för 124 449 ha, 74 % av arealen.

## Storleksfördelning, senaste tolv månaderna

| Anmäld areal per ärende | Ärenden | Areal (ha) |
| --- | --- | --- |
| under 1 ha | 7 123 | 4 690 |
| 1–2 ha | 10 844 | 15 277 |
| 2–5 ha | 13 766 | 43 046 |
| 5–10 ha | 6 080 | 42 032 |
| 10–20 ha | 2 540 | 34 429 |
| 20–50 ha | 834 | 23 686 |
| över 50 ha | 68 | 5 671 |

Slutsatser för bevakningen: de flesta anmälningar är små (hälften under 2,3 ha), så en bevakad fastighet kostar ofta bara några kronor per dag; stora ytor över 20 ha är 2 % av ärendena men 17 % av arealen. Av arealen är 97 % föryngringsavverkning (163 665 av 168 830 ha).

## Ägare: privatägd skog, bolag med mera

Ägaruppgifter finns inte i den öppna filen. Skogsstyrelsen redovisar ägare i sin [statistik över avverkningsanmälningar](https://www.skogsstyrelsen.se/statistik/avverkning/avverkningsanmalningar/) i två grupper: enskilda ägare (fysiska personer, dödsbon och bolag som inte är aktiebolag) och övriga ägare (staten, statliga och privata aktiebolag, övriga allmänna och privata ägare). Aktiebolag och allmänna ägare kan alltså inte skiljas åt.

| År | Totalt (ha) | Enskilda ägare (ha) | Övriga ägare (ha) | Källa |
| --- | --- | --- | --- | --- |
| 2021 | 267 823 | 169 970 | 97 542 | [Statistikfaktablad 2021](https://www.skogsstyrelsen.se/globalassets/statistik/statistikfaktablad/JO0314-statistikfaktablad-avverkningsanmalningar-2021.pdf) |
| 2022 | 240 881 | 133 456 | 94 631 | [Statistikfaktablad 2022](https://wwwprod.skogsstyrelsen.se/globalassets/statistik/statistikfaktablad/jo0314-statistikfaktablad-avverkningsanmalningar-2022-korr20230221.pdf) |
| 2025 (föryngringsavverkning, normal skog) | 241 646 | 135 033 | ej verifierat | [Skogsstyrelsens statistiksida](https://www.skogsstyrelsen.se/statistik/avverkning/avverkningsanmalningar/) |

Genomsnittlig anmäld areal 2022: 3,4 ha för enskilda ägare och 5,1 ha för övriga ägare. Enskilda ägare står alltså för ungefär 55–63 % av arealen (2021: 63 %, 2022: 55 %, 2025: 56 %) men har mindre ytor. Siffrorna för 2025 och för övriga ägare 2023–2025 bör hämtas ur Skogsstyrelsens statistikdatabas innan de används; de kom från en sökning och inte från en genomläst tabell.

## Att göra härnäst

- Ta reda på varför filen ger ungefär hälften av Skogsstyrelsens officiella areal (filtrering på status, bortfall av äldre ärenden eller annat) innan siffrorna används i prissättningen.
- Hämta ägarfördelning per län och år ur Skogsstyrelsens statistikdatabas (öppen data) om den behövs för företagsavtalet.
