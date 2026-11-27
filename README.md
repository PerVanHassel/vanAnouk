# vanAnouk — grafisch ontwerp

Statische herbouw van [vananouk.nl](https://vananouk.nl/). De site ziet er hetzelfde uit en werkt hetzelfde als de huidige WordPress-site (Bridge-thema), maar heeft geen WordPress, database of plugins meer nodig. Het is gewone HTML, CSS en JavaScript.

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

## Bekijken op telefoon en laptop (GitHub Pages)

1. Ga op GitHub naar deze repository → **Settings** → **Pages**.
2. Kies bij **Source** voor **Deploy from a branch**.
3. Kies de branch `claude/wizardly-galileo-0yn0as` en de map `/ (root)` en klik op **Save**.
4. Na ongeveer een minuut staat de site op `https://pervanhassel.github.io/vanAnouk/`.

GitHub Pages is gratis voor openbare repositories; voor een privé-repository is een betaald GitHub-abonnement nodig.

Lokaal bekijken kan ook: open een terminal in deze map, start `python3 -m http.server 8000` en ga naar <http://localhost:8000>.

## Contactformulier

Het formulier geeft dezelfde meldingen als het origineel. Het echte versturen gebeurt door `contact.php` en werkt dus alleen op hosting met PHP, zoals bhosted. GitHub Pages draait geen PHP: daar kan het formulier in de preview niet versturen.

## Later live zetten op bhosted

1. Maak eerst een volledige back-up van de huidige WordPress-site (bestanden én database).
2. Zet de WordPress-bestanden in de webmap opzij (niet meteen verwijderen).
3. Upload alle bestanden uit deze repository naar de webmap (via FTP).
4. Controleer de pagina's en verstuur een testbericht via het contactformulier.

## Bewust ongewijzigd overgenomen

De nieuwe versie is een exacte kopie, dus ook deze eigenschappen van de huidige site zijn hetzelfde gebleven:

- Zoekmachines worden geweerd (`noindex` op elke pagina en `Disallow: /` in `robots.txt`). De site is daardoor niet vindbaar in Google.
- De paginatitel van de homepage is "vanAnouk – En nog een WordPress site" (de standaardtekst van WordPress).
- De knop "Terug naar de startpagina" op de 404-pagina is wit op wit en dus onzichtbaar.

## Licenties van gebruikte onderdelen

- Lettertypen Assistant, Montserrat en Raleway: SIL Open Font License 1.1.
- Iconen: een deelverzameling van Font Awesome 4.7, SIL Open Font License 1.1.
