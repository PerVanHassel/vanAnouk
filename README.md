# vanAnouk.nl – statische 1-op-1 kopie

Dit is een exacte kopie van **https://vananouk.nl/**, gemaakt op 27 november 2026
vanaf de publieke website. De HTML, CSS, JavaScript, lettertypen, afbeeldingen en de
pdf zijn byte voor byte overgenomen zoals de server ze levert. Aan de inhoud en de
vormgeving is niets veranderd. Alleen de links naar `https://vananouk.nl/...` zijn
omgezet naar relatieve paden, zodat de kopie op elke host en lokaal werkt.

## Inhoud van deze repository

| Map | Wat |
| --- | --- |
| `site/` | De complete website, klaar om te hosten (alle pagina's, het thema, de plugins en de uploads) |
| `site/404.html` | De originele "Pagina niet gevonden"-pagina |
| `content-export/` | De ruwe inhoud uit de WordPress-API (pagina's, berichten en de mediabibliotheek) als JSON, handig voor een latere herbouw |
| `tools/` | De scripts waarmee de kopie is gemaakt, zodat dit later te herhalen is |

## Lokaal bekijken

```bash
cd site
python3 -m http.server 8000
```

Open daarna http://localhost:8000/ in de browser.

## Online zetten

Upload de inhoud van `site/` naar de webroot van een host (bijvoorbeeld `public_html`
bij bhosted, of Netlify, Cloudflare Pages of GitHub Pages). Er is geen PHP of database
nodig. `404.html` gebruikt paden vanaf de root (`/wp-content/...`), dus de site moet
op de root van een domein staan en niet in een submap.

## Wat zonder WordPress niet werkt

Dit is een statische kopie. De onderdelen die een server nodig hebben, werken niet
zonder WordPress:

- **Contactformulier** (Contact Form 7 op `/contact/`): het formulier is zichtbaar,
  maar verzenden gaat via de WordPress-API van de live site. Voor een werkend formulier
  is een formulierdienst nodig (bijvoorbeeld Formspree of Netlify Forms).
- **Cookiemelding**: werkt gewoon, dit draait volledig in de browser.
- RSS-feeds, `xmlrpc.php` en de oEmbed-links in de `<head>` wijzen nog naar de live
  site. Ze zijn niet zichtbaar en hebben geen invloed op de weergave.

## Wat er níet in zit

De PHP-bestanden van WordPress, het thema (Bridge + Bridge child) en de plugins, de
database (`anouk11_db`) en de instellingen in wp-admin. Die zijn alleen bereikbaar via
FTP of het controlepaneel van bhosted, en de cloudomgeving waarin deze kopie is gemaakt
kan alleen HTTPS gebruiken (geen FTP op poort 21 en geen MySQL). Voor een volledige
WordPress-back-up: download via FTP vanaf je eigen computer, of exporteer de database
via phpMyAdmin in het bhosted-controlepaneel.

## Gebruikte techniek op de live site

WordPress 5.2.21 · thema Bridge (Qode) met child-thema · WPBakery Page Builder 5.7 ·
Slider Revolution 5.4.8.3 · Contact Form 7 5.1.3 · Cookie Notice 1.2.46 · Zero Spam 3.0.6
