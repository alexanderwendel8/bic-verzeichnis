# BIC-Verzeichnis Österreich & Deutschland

Für eine Überweisung braucht man die Kontonummer (IBAN) und oft auch den **BIC**. Das ist eine Art
„Adresse“ der Bank, z. B. `GIBAATWWXXX` für die Erste Bank. Jede Bank hat außerdem eine
**Bankleitzahl** (BLZ), die in der IBAN steckt:

- **Österreich:** fünfstellig, an den Stellen 5 bis 9 der IBAN (`AT61 2011 1…` → `20111`)
- **Deutschland:** achtstellig, an den Stellen 5 bis 12 der IBAN (`DE89 1001 0010 …` → `10010010`)

Dieses Projekt sammelt die BICs und Bankleitzahlen aller Banken in Österreich und Deutschland an einem
Ort und hält sie aktuell.

## Was es macht

- **Jeden Morgen** lädt es die offiziellen Listen herunter:
  - Österreich: das Verzeichnis der [Oesterreichischen Nationalbank](https://www.oenb.at/Statistik/Klassifikationen/SEPA-Zahlungsverkehrs-Verzeichnis.html) (OeNB), täglich aktualisiert
  - Deutschland: die [Bankleitzahlendatei der Deutschen Bundesbank](https://www.bundesbank.de/de/aufgaben/unbarer-zahlungsverkehr/serviceangebot/bankleitzahlen/download-bankleitzahlen-602592),
    die viermal im Jahr erscheint (März, Juni, September, Dezember). Die neue Datei wird automatisch
    genau an dem Tag übernommen, ab dem sie gilt.
- **Es vergleicht sie mit dem letzten Stand** und hält fest, welche Banken neu dazugekommen sind, sich geändert
  haben oder weggefallen sind, z. B. durch eine Fusion.
- Weggefallene Banken **bleiben nachvollziehbar**. Die offiziellen Listen zeigen nur den aktuellen Stand, hier
  bleibt der letzte Stand jeder Bank erhalten – in Deutschland samt Nachfolge-Bankleitzahl, wenn die Bank eine angegeben hat.

## So nutzt du es

👉 **[alexanderwendel8.github.io/bic-verzeichnis](https://alexanderwendel8.github.io/bic-verzeichnis/)**

- **Land wählen:** oben zwischen Österreich und Deutschland umschalten.
- **Suchen:** Bankleitzahl, BIC, Banknamen oder Ort eintippen, die Treffer erscheinen sofort.
  Ein Klick auf eine Bank zeigt alle Details, BLZ und BIC lassen sich mit einem Klick kopieren.
  In Deutschland findet die Suche auch Filial-BICs und frühere Banknamen und zeigt, zu welcher
  Bankleitzahl sie gehören.
- **Änderungen ansehen:** Der Reiter „Änderungen“ zeigt Tag für Tag, was sich getan hat.
- **Herunterladen:** Über „CSV herunterladen“ bekommst du die ganze Liste des gewählten Landes als
  Datei. Sie öffnet sich direkt in Excel.
- **Per API abfragen:** Für Programme gibt es eine einfache Schnittstelle, siehe [API](#api).

Ein Projekt von Alexander Wendel. Die Daten stammen von der OeNB und der Deutschen Bundesbank und
werden ohne Gewähr weitergegeben.

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
| `/api/v1/index.json` | Übersicht: unterstützte Länder und Anzahl der Banken |

- **Land:** `AT` (Österreich) oder `DE` (Deutschland), Kleinbuchstaben gehen auch.
- **Bankleitzahl Österreich:** wie in der IBAN fünfstellig (`00100`) oder ohne führende Nullen (`100`).
- **Bankleitzahl Deutschland:** immer achtstellig (`10010010`).
- **Felder je Land unterschiedlich:** Die Bundesbank liefert keine Straße, keine Kontaktdaten und keinen LEI,
  dafür Kurzbezeichnung, Prüfziffermethode, angekündigte Löschung, Nachfolge-Bankleitzahl und Filialen.
- **Deutschland – welcher BIC gilt:** Für Zahlungen gilt `bic`. Die BICs in `filialen` dienen nur der Zuordnung.
- **Deutschland – Gültigkeit:** `gueltig_ab` und `gueltig_bis` geben an, welche Bundesbank-Datei verwendet wurde.
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

| Pfad | Inhalt |
|---|---|
| `update_bic.py` | Österreich: Download, Vergleich, Ablage (nur Python-Standardbibliothek) |
| `data/sepa-zv-vz_gesamt.csv` | Österreich: aktueller Stand des OeNB-Verzeichnisses |
| `changes/JJJJ-MM-TT.csv` | Österreich: Änderungen eines Tages (nur an Tagen mit Änderungen) |
| `changes/index.json` | Österreich: Liste der Tage mit Änderungen (für die Weboberfläche) |
| `update_bic_de.py` | Deutschland: Download der Bundesbank-XML, Auswahl der gültigen Datei, Vergleich, Ablage |
| `data/de/bankleitzahlen.csv` | Deutschland: eine Zeile je Bankleitzahl (Haupteintrag, Merkmal „1“) |
| `data/de/filialen.csv` | Deutschland: weitere Orte je Bankleitzahl (Zusatzeinträge, Merkmal „2“) |
| `data/de/meta.json` | Deutschland: verwendete Bundesbank-Datei (`FileRef`, `ValidFrom`, `ValidTill`) |
| `changes/de/JJJJ-MM-TT.csv`, `changes/de/index.json` | Deutschland: Änderungen, datiert auf den Gültigkeitstag |
| `web/` | Weboberfläche (statisch, ohne Build-Schritt) |
| `build_api.py` | Erzeugt beim Veröffentlichen die JSON-Dateien der API (nicht im Repo abgelegt) |

Ältere Gesamtstände sind über die Git-Historie der Dateien in `data/` abrufbar.

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

### Weboberfläche (GitHub Pages)

`web/` enthält eine statische Seite mit Umschalter Österreich/Deutschland, Suche (Bankleitzahl, BIC, Name,
Ort, LEI; in Deutschland auch Filial-BICs und Filialnamen), Filtern nach Bundesland und Sektor (Österreich),
Detailansicht mit Link zu GLEIF bzw. Filialliste und einer Übersicht aller Änderungen je Land.
Über `#land=DE&q=…` in der Adresse lässt sich eine Suche direkt verlinken.

Der Workflow `.github/workflows/bic-pages.yml` stellt Seite und Daten zusammen und veröffentlicht sie
auf GitHub Pages – nach jedem täglichen Update und bei jeder Änderung an `web/`, `data/` oder `changes/` auf `main`.

**Einmalig einrichten:** Repository → Settings → Pages → „Build and deployment“ → Source: **GitHub Actions**.

Schlägt eine Veröffentlichung fehl (z. B. „No artifacts named github-pages“), den Workflow über
„Run workflow“ **neu starten**, nicht über „Re-run“. Ein Re-run findet sonst zwei gleichnamige Pakete und bricht ab.

Lokal ansehen:

```sh
mkdir -p /tmp/site && cp web/* /tmp/site/ && cp -r data changes /tmp/site/ && python3 build_api.py /tmp/site/api
python3 -m http.server -d /tmp/site 8000   # dann http://localhost:8000
```

### Ausführung

Automatisch täglich über GitHub Actions (`.github/workflows/bic-update.yml`), manuell über
„Actions → BIC-Verzeichnis aktualisieren → Run workflow“ oder lokal:

```sh
python3 update_bic.py                    # Österreich: herunterladen und vergleichen
python3 update_bic.py --input x.csv      # Österreich: lokale OeNB-Datei verwenden
python3 update_bic_de.py                 # Deutschland: herunterladen und vergleichen
python3 update_bic_de.py --input a.xml b.xml --today 2026-12-07   # Deutschland: lokale Dateien, Stichtag testen
```

Liefert eine Quelle deutlich weniger Einträge als bisher (unter 80 %), bricht das jeweilige Skript ab, statt
massenhaft Banken als „entfernt“ zu melden. Mit `--force` wird der Stand trotzdem übernommen.
Beide Länder laufen im Workflow unabhängig voneinander: Fällt eine Quelle aus, wird die andere trotzdem
übernommen und veröffentlicht, der Workflow wird aber als fehlgeschlagen markiert.

Daten: © Oesterreichische Nationalbank, es gelten deren [Nutzungsbedingungen](https://www.oenb.at/Service/Impressum-und-Haftung.html);
© Deutsche Bundesbank, die Bankleitzahlendatei wird dort „unverbindlich“ bereitgestellt, es gelten die
Hinweise im [Impressum](https://www.bundesbank.de/de/startseite/impressum).
