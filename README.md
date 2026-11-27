# vanAnouk — grafisch ontwerp

Nieuwe versie van [vananouk.nl](https://vananouk.nl/). Eerst is de huidige WordPress-site (Bridge-thema) exact nagebouwd in gewone HTML, CSS en JavaScript, zonder WordPress, database of plugins (die 1-op-1-kopie is commit `5bb3043`). Daarna is de vernieuwing toegevoegd die hieronder staat.

De live site op vananouk.nl is nog niet aangepast. Deze versie staat alleen op GitHub, met een preview op <https://pervanhassel.github.io/vanAnouk/>.

## Vernieuwing (november 2026)

- **Een kleur per onderdeel**: Over is harmonie groen (`#7c9c80`), Portfolio en de vier portfoliopagina's zijn nuance lila paars (`#9d8fb5`) en Contact is zomers oranje (`#d98c56`). Home houdt het grijsblauw (`#759ba3`). De kleuren staan bovenaan `assets/css/style.css` en zijn daar in één keer aan te passen.
- **Signal**: op de contactpagina staat een knop die direct een Signal-chat opent met 06 28 25 52 10.
- **SEO**: echte paginatitels en beschrijvingen, één hoofdkop per pagina, alt-teksten bij alle afbeeldingen, gegevens voor Google (bedrijf, adres, Anouk Houter, kruimelpad), een `sitemap.xml` en een `robots.txt` die zoekmachines toelaat. Op de preview op github.io staat een `noindex`, zodat die niet in Google komt.
- **Sneller**: alle foto's staan er ook als WebP (31,8 MB → 4,8 MB); browsers die dat niet kennen krijgen de PNG.
- **Kleine verbeteringen**: inzoomen op telefoons kan weer, het mobiele menu werkt ook met het toetsenbord, en de knop op de 404-pagina is zichtbaar.

## Wat staat waar

| Pad | Inhoud |
| --- | --- |
| `index.html` | Home |
| `about/` | Over (Anouk Houter) |
| `portfolio/` | Portfolio-overzicht |
| `logo-en-huisstijl/`, `educatieve-uitgaven/`, `boeken/`, `magazines/` | Portfoliopagina's met lightbox |
| `contact/` | Contactpagina met formulier |
| `404.html` | Pagina niet gevonden |
| `assets/css/style.css` | Alle opmaak |
| `assets/js/site.js` | Mobiel menu, cookiemelding, lightbox, animatie op de homepage, contactformulier |
| `assets/fonts/` | Lettertypen (Assistant, Montserrat, Raleway en een kleine set iconen) |
| `wp-content/uploads/` | Alle afbeeldingen en de privacyverklaring, op dezelfde paden als op de huidige site |
| `contact.php` | Verstuurt het contactformulier naar info@vananouk.nl |

De adressen van de pagina's en bestanden zijn gelijk aan die van de huidige site, zodat bestaande links (bijvoorbeeld naar de privacyverklaring) blijven werken.

## Bekijken op telefoon en laptop

De preview staat op <https://pervanhassel.github.io/vanAnouk/> (GitHub Pages, gepubliceerd vanaf de branch `claude/wizardly-galileo-0yn0as`). Elke wijziging op die branch staat er binnen een minuut.

Lokaal bekijken kan ook: open een terminal in deze map, start `python3 -m http.server 8000` en ga naar <http://localhost:8000>.

## Contactformulier

Het formulier geeft dezelfde meldingen als het origineel. Het echte versturen gebeurt door `contact.php` en werkt dus alleen op hosting met PHP, zoals bhosted. GitHub Pages draait geen PHP: daar kan het formulier in de preview niet versturen.

## Later live zetten op bhosted

1. Maak eerst een volledige back-up van de huidige WordPress-site (bestanden én database).
2. Zet de WordPress-bestanden in de webmap opzij (niet meteen verwijderen).
3. Upload alle bestanden uit deze repository naar de webmap (via FTP).
4. Controleer de pagina's en verstuur een testbericht via het contactformulier.

## Nog te doen

- **Beheeromgeving**: portfolio-artikelen en recensies toevoegen, de Google-reviewlink snel bij de hand hebben en ingevulde contactformulieren bekijken. Daarvoor is hosting met PHP nodig (zoals bhosted); de aanpak is nog niet gekozen.
- **Uitgebreidere portfolio-artikelen met recensies**: de teksten en recensies per project moeten nog worden aangeleverd.
- **Bij het live zetten**: de site aanmelden bij Google Search Console met `https://vananouk.nl/sitemap.xml`, en een Google Bedrijfsprofiel aanmaken of bijwerken (daar komt ook de reviewlink vandaan).

## Licenties van gebruikte onderdelen

- Lettertypen Assistant, Montserrat en Raleway: SIL Open Font License 1.1.
- Iconen: een deelverzameling van Font Awesome 4.7, SIL Open Font License 1.1.
