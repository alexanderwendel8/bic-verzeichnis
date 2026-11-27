# BIC-Verzeichnis Österreich & Nachbarländer

Für eine Überweisung braucht man die Kontonummer (IBAN) und oft auch den **BIC**. Das ist eine Art
„Adresse“ der Bank, z. B. `GIBAATWWXXX` für die Erste Bank. Jede Bank hat außerdem eine
**Bankleitzahl** (BLZ), die in der IBAN steckt:

- **Österreich:** fünfstellig, an den Stellen 5 bis 9 der IBAN (`AT61 2011 1…` → `20111`)
- **Deutschland:** achtstellig, an den Stellen 5 bis 12 der IBAN (`DE89 1001 0010 …` → `10010010`)
- **Schweiz und Liechtenstein:** die IID (frühere BC-Nummer), fünfstellig an den Stellen 5 bis 9 (`CH.. 0070 0…` → `00700`, Zürcher Kantonalbank)
- **Tschechien und Slowakei:** vierstellig, an den Stellen 5 bis 8 (`CZ65 0800 …` → `0800`)
- **Ungarn:** der achtstellige Filialcode (Bankcode, Filiale, Prüfziffer) an den Stellen 5 bis 12 (`HU.. 1173 8008 …` → `11738008`, OTP Bank Debrecen)
- **Slowenien:** fünfstellig an den Stellen 5 bis 9 (`SI56 0100 0…` → `01000`)

Dieses Projekt sammelt die BICs und Bankleitzahlen aller Banken in Österreich und seinen Nachbarländern
Deutschland, Schweiz, Liechtenstein, Tschechien, Slowakei, Ungarn und Slowenien an einem Ort und hält sie aktuell.

## Was es macht

- **Jeden Morgen** lädt es die offiziellen Listen herunter:
  - Österreich: das Verzeichnis der [Oesterreichischen Nationalbank](https://www.oenb.at/Statistik/Klassifikationen/SEPA-Zahlungsverkehrs-Verzeichnis.html) (OeNB), täglich aktualisiert
  - Deutschland: die [Bankleitzahlendatei der Deutschen Bundesbank](https://www.bundesbank.de/de/aufgaben/unbarer-zahlungsverkehr/serviceangebot/bankleitzahlen/download-bankleitzahlen-602592),
    die viermal im Jahr erscheint (März, Juni, September, Dezember). Die neue Datei wird automatisch
    genau an dem Tag übernommen, ab dem sie gilt.
  - Schweiz und Liechtenstein: der [Bank Master der SIX](https://api.six-group.com/api/epcd/bankmaster/v3/bankmaster.json), täglich aktualisiert
  - Tschechien: der [Číselník kódů platebního styku](https://www.cnb.cz/cs/platebni-styk/ucty-kody-bank/) der Tschechischen
    Nationalbank (ČNB); neue Fassungen werden wie in Deutschland ab ihrem Gültigkeitstag übernommen
  - Slowakei: der [Prevodník identifikačných kódov](https://nbs.sk/platby/vseobecne-informacie/ciselniky-a-registre/prevodnik-sk/)
    der Slowakischen Nationalbank (NBS)
  - Ungarn: die [Rövid irányítókód-tábla](https://www.mnb.hu/en/payments/mnb-as-payment-authority/routing-table) der
    Ungarischen Nationalbank (MNB), monatlich aktualisiert und ab ihrem Gültigkeitstag übernommen
  - Slowenien: die [Liste der Identifikationskennungen](https://www.bsi.si/sl/d/seznam-identifikacijskih-oznak-pps) der Banka Slovenije
- **Es vergleicht sie mit dem letzten Stand** und hält fest, welche Banken neu dazugekommen sind, sich geändert
  haben oder weggefallen sind, z. B. durch eine Fusion.
- Weggefallene Banken **bleiben nachvollziehbar**. Die offiziellen Listen zeigen nur den aktuellen Stand, hier
  bleibt der letzte Stand jeder Bank erhalten – in Deutschland, der Schweiz und Liechtenstein samt
  Nachfolge-Bankleitzahl, wenn es eine gibt.

## So nutzt du es

👉 **[alexanderwendel8.github.io/bic-verzeichnis](https://alexanderwendel8.github.io/bic-verzeichnis/)**

- **Land wählen:** oben das Land umschalten (AT, DE, CH, LI, CZ, SK, HU, SI).
- **Suchen:** Bankleitzahl, BIC, Banknamen oder Ort eintippen, die Treffer erscheinen sofort.
  Ein Klick auf eine Bank zeigt alle Details, BLZ und BIC lassen sich mit einem Klick kopieren.
  In Deutschland findet die Suche auch Filial-BICs und frühere Banknamen und zeigt, zu welcher
  Bankleitzahl sie gehören. Bankleitzahlen lassen sich auch so eingeben, wie sie in der IBAN stehen
  (z. B. `0200` in der Slowakei). Entfernte oder überführte Bankleitzahlen erscheinen, wenn man sie
  genau eingibt, mit Hinweis auf den Nachfolger.
- **Änderungen ansehen:** Der Reiter „Änderungen“ zeigt Tag für Tag, was sich getan hat.
- **Herunterladen:** Über „CSV herunterladen“ bekommst du die ganze Liste des gewählten Landes als
  Datei. Sie öffnet sich direkt in Excel.
- **Per API abfragen:** Für Programme gibt es eine einfache Schnittstelle, siehe [API](#api).

Ein Projekt von Alexander Wendel. Die Daten stammen von OeNB, Deutscher Bundesbank, SIX, ČNB, NBS, MNB und
Banka Slovenije und werden ohne Gewähr weitergegeben.

## API

Die Daten jeder Bank lassen sich als JSON abrufen. Übergeben werden **Land** und **Bankleitzahl**:

```
https://alexanderwendel8.github.io/bic-verzeichnis/api/v1/{land}/{bankleitzahl}.json
```

Beispiel: [`/api/v1/AT/20111.json`](https://alexanderwendel8.github.io/bic-verzeichnis/api/v1/AT/20111.json)

```json
{
  "land": "AT",
  "bankleitzahl": "20111",
  "bic": "GIBAATWWXXX",
  "name": "Erste Bank der oesterreichischen Sparkassen AG",
  "status": "aktiv",
  "entfernt_am": null,
  "art": "Hauptanstalt",
  "sektor": "Sparkassen",
  "institutsart": "KI",
  "identnummer": "7780729",
  "firmenbuchnummer": "286283f",
  "lei": "549300HUKIA1IZQHFZ83",
  "gruendungsdatum": "2006-11-08",
  "adresse": { "strasse": "Am Belvedere 1", "plz": "1100", "ort": "Wien", "bundesland": "Wien" },
  "postadresse": { "strasse": null, "plz": null, "ort": null, "postfach": null },
  "kontakt": { "telefon": "050100/10100", "fax": null, "email": "service@s-servicecenter.at", "homepage": "https://www.erstebank.at" }
}
```

Beispiel Deutschland: [`/api/v1/DE/12070000.json`](https://alexanderwendel8.github.io/bic-verzeichnis/api/v1/DE/12070000.json)
(gekürzt – die Deutsche Bank hat unter dieser Bankleitzahl 37 weitere Orte)

```json
{
  "land": "DE",
  "bankleitzahl": "12070000",
  "bic": "DEUTDEBB160",
  "name": "Deutsche Bank",
  "kurzbezeichnung": "Deutsche Bank",
  "status": "aktiv",
  "entfernt_am": null,
  "loeschung_angekuendigt": false,
  "nachfolge_bankleitzahl": null,
  "adresse": { "plz": "14405", "ort": "Potsdam" },
  "pan": "27704",
  "pruefziffermethode": "63",
  "datensatznummer": "44796",
  "gueltig_ab": "2026-09-07",
  "gueltig_bis": "2026-12-06",
  "filialen": [
    { "name": "Deutsche Bank", "plz": "16278", "ort": "Angermünde", "bic": "DEUTDEBB171", "pan": "27704" },
    { "name": "Deutsche Bank", "plz": "16259", "ort": "Bad Freienwalde (Oder)", "bic": "DEUTDEBB172", "pan": "27704" }
  ]
}
```

| Aufruf | Ergebnis |
|---|---|
| `/api/v1/{land}/{bankleitzahl}.json` | Alle Daten einer Bank |
| `/api/v1/{land}/index.json` | Liste aller Banken (Bankleitzahl, BIC, Name, Status) |
| `/api/v1/{land}/alle.json` | Alle Banken eines Landes mit allen Daten in einer Datei (kompakt) |
| `/api/v1/index.json` | Übersicht: unterstützte Länder und Anzahl der Banken |

- **Land:** `AT`, `DE`, `CH`, `LI`, `CZ`, `SK`, `HU` oder `SI`, Kleinbuchstaben gehen auch.
- **Bankleitzahl Österreich:** wie in der IBAN fünfstellig (`00100`) oder ohne führende Nullen (`100`).
- **Bankleitzahl Deutschland:** immer achtstellig (`10010010`).
- **Bankleitzahl Schweiz/Liechtenstein:** die IID, fünfstellig (`00100`) oder ohne führende Nullen (`100`).
- **Bankleitzahl Tschechien:** vierstellig (`0800`). **Slowakei:** vierstellig (`0200`) oder ohne führende Nullen (`200`).
- **Bankleitzahl Ungarn:** der achtstellige Filialcode (`11738008`). **Slowenien:** fünfstellig (`01000`).
- **Felder je Land unterschiedlich:** Die Bundesbank liefert keine Straße, keine Kontaktdaten und keinen LEI,
  dafür Kurzbezeichnung, Prüfziffermethode, angekündigte Löschung, Nachfolge-Bankleitzahl und Filialen.
- **Deutschland – welcher BIC gilt:** Für Zahlungen gilt `bic`. Die BICs in `filialen` dienen nur der Zuordnung.
- **Deutschland – Gültigkeit:** `gueltig_ab` und `gueltig_bis` geben an, welche Bundesbank-Datei verwendet wurde.
- **Schweiz/Liechtenstein:** `art` (Hauptsitz, Filiale, QR-IID), `hauptsitz_bankleitzahl`, `qr_iid_gehoert_zu`,
  `sic_iid`, `teilnahme` (z. B. SIC, euroSIC, Instant Payments CHF) und bei überführten IIDs `nachfolge_bankleitzahl`.
  Die Schweiz enthält auch ausländische Teilnehmer am Schweizer Zahlungsverkehr; ihr Sitzland steht in `adresse.land`.
- **Tschechien:** `certis` (Teilnahme am Clearing CERTIS) und `gueltig_ab` der verwendeten Fassung. **Slowakei:** `sips`
  (Teilnahme am Clearing SIPS). Beide Quellen liefern keine Adressen.
- **Ungarn:** jede Filiale ist ein eigener Eintrag; dazu `bankcode` (die ersten drei Stellen), `viber_senden`,
  `viber_empfangen` (Großzahlungssystem VIBER) und `gueltig_ab` der verwendeten Monatstabelle.
  **Slowenien:** `institut` (die ersten zwei Stellen der Kennung).
- **Unbekannte Bankleitzahl oder unbekanntes Land:** Antwort mit HTTP-Status **404**.
- **Weggefallene Banken** liefern weiter ihren letzten Stand, mit `"status": "entfernt"` und dem Datum in `entfernt_am`.
- Leere Felder sind `null`, Datumsangaben im Format `JJJJ-MM-TT`.
- Die API darf aus jedem Browser und jeder Webseite abgefragt werden (CORS ist offen).
- Aktualisiert wird täglich zusammen mit der Webseite.

Beispiel mit der Kommandozeile:

```sh
curl https://alexanderwendel8.github.io/bic-verzeichnis/api/v1/AT/20111.json
```

Beispiel in JavaScript:

```js
const res = await fetch("https://alexanderwendel8.github.io/bic-verzeichnis/api/v1/AT/20111.json");
if (res.ok) {
  const bank = await res.json();
  console.log(bank.bic); // GIBAATWWXXX
}
```

---

## Für Entwickler

### Aufbau

Jedes Land ist ein eigenes kleines Modul in `laender/`. Alles andere – Vergleich mit dem letzten Stand,
Änderungsprotokoll, Ablage, API und Webseite – ist für alle Länder derselbe Code.

| Pfad | Inhalt |
|---|---|
| `laender/__init__.py` | Liste der Länder und Beschreibung, was ein Land-Modul bereitstellen muss |
| `laender/at.py`, `de.py`, `ch.py`, `li.py`, `cz.py`, `sk.py`, `hu.py`, `si.py` | je Land: Download, Umwandlung, API-Felder, Einstellungen der Webseite |
| `laender/_six.py` | gemeinsame SIX-Quelle für die Schweiz und Liechtenstein |
| `kern.py` | gemeinsamer Teil: Vergleich, Änderungsprotokoll, Ablage, API-Einträge |
| `update.py` | lädt alle (oder ausgewählte) Länder und protokolliert Änderungen |
| `build_site.py` | stellt Webseite, `laender.json` und API für GitHub Pages zusammen (API nicht im Repo abgelegt) |
| `web/` | Weboberfläche (statisch, ohne Build-Schritt; Länder kommen aus `laender.json`) |
| `data/<land>/bankleitzahlen.csv` | aktueller Stand, eine Zeile je Bankleitzahl |
| `data/<land>/filialen.csv` | weitere Orte je Bankleitzahl (derzeit nur Deutschland) |
| `data/<land>/meta.json` | Angaben zur verwendeten Quelldatei (z. B. Gültigkeit in DE, CZ und HU, Überführungen in CH/LI) |
| `changes/<land>/JJJJ-MM-TT.csv` | Änderungen eines Tages (nur an Tagen mit Änderungen) |
| `changes/<land>/index.json` | Liste der Tage mit Änderungen |

`<land>` ist der Ländercode in Kleinbuchstaben (`at`, `de`, `ch`, `li`, `cz`, `sk`, `hu`, `si`). Die frühere Adresse der österreichischen
Gesamtliste, `data/sepa-zv-vz_gesamt.csv`, wird auf der Webseite weiter bedient.
Ältere Gesamtstände sind über die Git-Historie der Dateien in `data/` abrufbar.

### Ein Land hinzufügen

1. `laender/<cc>.py` anlegen – am einfachsten eine Kopie von `at.py` (eine Datei, keine Filialen) oder
   `de.py` (mit Filialen und Gültigkeitsdatum) – und `laden()`, `api_eintrag()`, `QUELLE` und `WEB` anpassen.
2. Das Modul in `laender/__init__.py` in `LAENDER` aufnehmen.
3. `python3 update.py <CC>` legt den Ausgangsstand an, `python3 build_site.py /tmp/site` baut Seite und API.

Webseite, API, Workflow und Änderungsprotokoll übernehmen das neue Land automatisch.

### Format

Alle Dateien: Semikolon als Trennzeichen, UTF-8 mit BOM (öffnet sich in Excel mit korrekten Umlauten).

Die Änderungsdateien haben zwei zusätzliche Spalten vorne:

- `Änderung`: `neu`, `geändert` oder `entfernt`
- `Geänderte Felder`: bei `geändert` z. B. `SWIFT-Code: ALT -> NEU | Ort: ALT -> NEU`

Danach folgt der Eintrag (bei `entfernt` der letzte bekannte Stand). Schlüssel für den Vergleich ist die Bankleitzahl.

**Deutschland – Besonderheiten der Quelle:**

- Gelesen wird die XML-Fassung der Bankleitzahlendatei, weil nur sie im Dateikopf `ValidFrom`/`ValidTill`
  enthält. Die Bundesbank stellt jeweils die gültige und – etwa einen Monat vorher – die nächste Datei bereit;
  das Skript nimmt die, die heute gilt. Die Download-Links werden jedes Mal von der Bundesbank-Seite gelesen.
- Pro Bankleitzahl gibt es genau einen Haupteintrag (Merkmal „1“); nur dessen BIC gilt für Zahlungen.
  Zusatzeinträge (Merkmal „2“) sind weitere Orte derselben Bankleitzahl, teils mit Filial-BIC oder altem
  Namen nach Fusionen. Sie stehen in `filialen.csv` und zählen nicht als eigene Banken.
- Einträge mit Änderungskennzeichen „D“ gelten ab dem Gültigkeitstag als `entfernt`. Das Änderungskennzeichen
  selbst wird nicht abgelegt, damit nicht jedes Quartal alle Einträge als „geändert“ erscheinen.
- Ändern sich nur die Filialen einer Bankleitzahl, steht in `Geänderte Felder` z. B. `Filialen: 5 -> 4`.

**Schweiz/Liechtenstein, Tschechien, Slowakei – Besonderheiten der Quellen:**

- Vor der Umsetzung wurde geprüft, ob es die Daten in moderneren Formaten gibt: Die SIX liefert JSON (verwendet).
  ČNB und NBS bieten nur CSV und PDF an, kein XML oder JSON – daher CSV.
- **SIX:** eine Datei für die Schweiz und Liechtenstein, je Lauf nur einmal geladen (`laender/_six.py`). Überführte
  IIDs („BankMasterConcatenated“) stehen in `data/ch/meta.json` und verweisen in der API auf die neue IID.
- **ČNB:** Die gültige und meist schon die nächste Fassung stehen nebeneinander auf der Seite, Nummer und
  Gültigkeitsdatum („platný od“) nur dort, nicht in der Datei. Das Skript nimmt die Fassung, die heute gilt.
- **NBS:** CSV in Windows-1250 mit Titelzeile; der Link enthält eine Dokument-ID und wird jedes Mal von der Seite
  gelesen. Die Liste enthält auch tschechische Institute, die im slowakischen Zahlungsverkehr erreichbar sind.

**Ungarn, Slowenien – Besonderheiten der Quellen:**

- Auch hier wurde vorab nach moderneren Formaten gesucht: Die MNB bietet nur Excel (`.xlsx`) an („Table available only
  in hungarian (excel format)“), die Banka Slovenije nur eine Textdatei mit Semikolons (daneben eine PDF-Liste).
- **MNB:** Die `.xlsx` wird ohne Zusatzbibliothek gelesen (eine `.xlsx` ist ein ZIP mit XML-Dateien). Der Blattname
  (z. B. `SHT20261101`) nennt das Gültigkeitsdatum; neue Monatstabellen werden ab diesem Tag als Änderung protokolliert.
- **Banka Slovenije:** Windows-1250. Doppelte Zeilen in der Quelle (derzeit `19352`) werden nur einmal übernommen.

### Weboberfläche (GitHub Pages)

`web/` enthält eine statische Seite mit Umschalter Österreich/Deutschland, Suche (Bankleitzahl, BIC, Name,
Ort, LEI; in Deutschland auch Filial-BICs und Filialnamen), Filtern nach Bundesland und Sektor (Österreich),
Detailansicht mit Link zu GLEIF bzw. Filialliste und einer Übersicht aller Änderungen je Land.
Über `#land=DE&q=…` in der Adresse lässt sich eine Suche direkt verlinken.

Der Workflow `.github/workflows/bic-pages.yml` stellt Seite und Daten zusammen und veröffentlicht sie
auf GitHub Pages – nach jedem täglichen Update und bei jeder Änderung an Oberfläche, Daten oder Code auf `main`.
Bauen und Veröffentlichen laufen in getrennten Jobs.

**Einmalig einrichten:** Repository → Settings → Pages → „Build and deployment“ → Source: **GitHub Actions**.

Schlägt eine Veröffentlichung fehl (z. B. „No artifacts named github-pages“), den Workflow über
„Run workflow“ **neu starten**, nicht über „Re-run“. Ein Re-run findet sonst zwei gleichnamige Pakete und bricht ab.

Lokal ansehen:

```sh
python3 build_site.py /tmp/site
python3 -m http.server -d /tmp/site 8000   # dann http://localhost:8000
```

### Ausführung

Automatisch täglich über GitHub Actions (`.github/workflows/bic-update.yml`), manuell über
„Actions → BIC-Verzeichnis aktualisieren → Run workflow“ oder lokal:

```sh
python3 update.py                        # alle Länder herunterladen und vergleichen
python3 update.py DE                     # nur Deutschland
python3 update.py AT --input x.csv       # Österreich mit lokaler OeNB-Datei
python3 update.py DE --input a.xml b.xml --today 2026-12-07   # Deutschland: lokale Dateien, Stichtag testen
```

Liefert eine Quelle deutlich weniger Einträge als bisher (unter 80 %), wird dieses Land nicht übernommen, statt
massenhaft Banken als „entfernt“ zu melden. Mit `--force` wird der Stand trotzdem übernommen.
Die Länder laufen unabhängig voneinander: Fällt eine Quelle aus, werden die anderen trotzdem übernommen und
veröffentlicht, der Workflow wird aber als fehlgeschlagen markiert.

Daten: © Oesterreichische Nationalbank, es gelten deren [Nutzungsbedingungen](https://www.oenb.at/Service/Impressum-und-Haftung.html);
© Deutsche Bundesbank, die Bankleitzahlendatei wird dort „unverbindlich“ bereitgestellt, es gelten die
Hinweise im [Impressum](https://www.bundesbank.de/de/startseite/impressum).
© SIX Group AG (Bank Master), © Česká národní banka, © Národná banka Slovenska, © Magyar Nemzeti Bank,
© Banka Slovenije. Für diese Quellen wurden die
Nutzungsbedingungen noch nicht im Einzelnen geprüft.
