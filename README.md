# BIC-Verzeichnis Österreich

Für eine Überweisung braucht man die Kontonummer (IBAN) und oft auch den **BIC**. Das ist eine Art
„Adresse“ der Bank, z. B. `GIBAATWWXXX` für die Erste Bank. In Österreich hat jede Bank außerdem eine
fünfstellige **Bankleitzahl** (BLZ). Sie steckt in der IBAN an den Stellen 5 bis 9.

Dieses Projekt sammelt die BICs und Bankleitzahlen aller Banken in Österreich an einem Ort und hält sie
aktuell.

## Was es macht

- **Jeden Morgen** lädt es die offizielle Liste der [Oesterreichischen Nationalbank](https://www.oenb.at/Statistik/Klassifikationen/SEPA-Zahlungsverkehrs-Verzeichnis.html) (OeNB) herunter.
- **Es vergleicht sie mit dem Vortag** und hält fest, welche Banken neu dazugekommen sind, sich geändert
  haben oder weggefallen sind, z. B. durch eine Fusion.
- Weggefallene Banken **bleiben nachvollziehbar**. Die OeNB-Liste zeigt nur den heutigen Stand, hier
  bleibt der letzte Stand jeder Bank erhalten.

## So nutzt du es

👉 **[alexanderwendel8.github.io/bic-verzeichnis](https://alexanderwendel8.github.io/bic-verzeichnis/)**

- **Suchen:** Bankleitzahl, BIC, Banknamen oder Ort eintippen, die Treffer erscheinen sofort.
  Ein Klick auf eine Bank zeigt alle Details, BLZ und BIC lassen sich mit einem Klick kopieren.
- **Änderungen ansehen:** Der Reiter „Änderungen“ zeigt Tag für Tag, was sich getan hat.
- **Herunterladen:** Über „CSV herunterladen“ bekommst du die ganze Liste als Datei. Sie öffnet sich
  direkt in Excel.

Ein Projekt von Alexander Wendel. Die Daten stammen von der OeNB und werden ohne Gewähr weitergegeben.

---

## Für Entwickler

### Aufbau

| Pfad | Inhalt |
|---|---|
| `update_bic.py` | Skript: Download, Vergleich, Ablage (nur Python-Standardbibliothek) |
| `data/sepa-zv-vz_gesamt.csv` | Aktueller Stand des Verzeichnisses |
| `changes/JJJJ-MM-TT.csv` | Änderungen eines Tages (nur an Tagen mit Änderungen) |
| `changes/index.json` | Liste der Tage mit Änderungen (für die Weboberfläche) |
| `web/` | Weboberfläche (statisch, ohne Build-Schritt) |

Ältere Gesamtstände sind über die Git-Historie von `data/sepa-zv-vz_gesamt.csv` abrufbar.

### Format

Alle Dateien: Semikolon als Trennzeichen, UTF-8 mit BOM (öffnet sich in Excel mit korrekten Umlauten).

Die Änderungsdateien haben zwei zusätzliche Spalten vorne:

- `Änderung`: `neu`, `geändert` oder `entfernt`
- `Geänderte Felder`: bei `geändert` z. B. `SWIFT-Code: ALT -> NEU | Ort: ALT -> NEU`

Danach folgt der Eintrag (bei `entfernt` der letzte bekannte Stand). Schlüssel für den Vergleich ist die Bankleitzahl.

### Weboberfläche (GitHub Pages)

`web/` enthält eine statische Seite mit Suche (Bankleitzahl, BIC, Name, Ort, LEI), Filtern nach
Bundesland und Sektor, Detailansicht mit Link zu GLEIF und einer Übersicht aller Änderungen.

Der Workflow `.github/workflows/bic-pages.yml` stellt Seite und Daten zusammen und veröffentlicht sie
auf GitHub Pages – nach jedem täglichen Update und bei jeder Änderung an `web/`, `data/` oder `changes/` auf `main`.

**Einmalig einrichten:** Repository → Settings → Pages → „Build and deployment“ → Source: **GitHub Actions**.

Schlägt eine Veröffentlichung fehl (z. B. „No artifacts named github-pages“), den Workflow über
„Run workflow“ **neu starten**, nicht über „Re-run“. Ein Re-run findet sonst zwei gleichnamige Pakete und bricht ab.

Lokal ansehen:

```sh
mkdir -p /tmp/site && cp web/* /tmp/site/ && cp -r data changes /tmp/site/
python3 -m http.server -d /tmp/site 8000   # dann http://localhost:8000
```

### Ausführung

Automatisch täglich über GitHub Actions (`.github/workflows/bic-update.yml`), manuell über
„Actions → BIC-Verzeichnis aktualisieren → Run workflow“ oder lokal:

```sh
python3 update_bic.py              # herunterladen und vergleichen
python3 update_bic.py --input x.csv  # lokale OeNB-Datei verwenden
```

Liefert die OeNB deutlich weniger Einträge als bisher (unter 80 %), bricht das Skript ab, statt
massenhaft Banken als „entfernt“ zu melden. Mit `--force` wird der Stand trotzdem übernommen.

Daten: © Oesterreichische Nationalbank, es gelten deren [Nutzungsbedingungen](https://www.oenb.at/Service/Impressum-und-Haftung.html).
