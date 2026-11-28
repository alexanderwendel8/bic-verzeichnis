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
- **Belgien:** der dreistellige Bank-Identifikationscode an den Stellen 5 bis 7 (`BE.. 310 …` → `310`, ING Belgium)
- **Spanien:** vierstellig an den Stellen 5 bis 8 (`ES.. 0049 …` → `0049`, Banco Santander)
- **Frankreich:** der fünfstellige Code banque (CIB) an den Stellen 5 bis 9 (`FR76 30004 …` → `30004`, BNP Paribas)
- **Polen:** die achtstellige Abrechnungsnummer (numer rozliczeniowy) an den Stellen 5 bis 12
  (`PL.. 1050 1445 …` → `10501445`, ING Bank Śląski Krakau)
- **Litauen:** fünfstellig an den Stellen 5 bis 9 (`LT.. 7300 0…` → `73000`, Swedbank)
- **Lettland:** vier Buchstaben an den Stellen 5 bis 8, gleich den ersten vier Zeichen des BIC (`LV.. HABA …` → `HABA`, Swedbank)
- **Estland:** zweistellig an den Stellen 5 und 6 (`EE.. 22…` → `22`, Swedbank)
- **Niederlande:** vier Buchstaben an den Stellen 5 bis 8, gleich den ersten vier Zeichen des BIC (`NL.. INGB …` → `INGB`, ING);
  hier **abgeleitet und unvollständig**, siehe unten
- **Italien:** der fünfstellige ABI-Code an den Stellen 6 bis 10, danach der CAB-Code der Filiale an den Stellen 11 bis 15
  (`IT.. X 03069 15417 …` → ABI `03069` Intesa Sanpaolo, CAB `15417` Filiale Pescara)

Dieses Projekt sammelt die BICs und Bankleitzahlen aller Banken in Österreich und seinen Nachbarländern
Deutschland, Schweiz, Liechtenstein, Italien, Tschechien, Slowakei, Ungarn und Slowenien sowie weiterer EU-Länder
(Belgien, Spanien, Frankreich, Polen, Litauen, Lettland, Estland, Niederlande) an einem Ort und hält sie aktuell.

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
  - Belgien: die [Liste der Bank-Identifikationscodes](https://www.nbb.be/en/payments-and-securities/bank-identification-codes)
    der Belgischen Nationalbank (NBB), aktualisiert, sobald sich etwas ändert
  - Spanien: das [Registro de Entidades](https://app.bde.es/rbe_spa/) des Banco de España, täglich aktualisiert,
    samt früherer Codes mit Abmeldegrund und Nachfolger. Auch der Banco de España führt keine BICs; sie kommen
    wie in Italien aus der BIC/LEI-Zuordnung von GLEIF.
  - Frankreich: das Register [REGAFI](https://www.regafi.fr/) der ACPR (Banque de France), täglich aktualisiert;
    BICs ebenfalls über GLEIF
  - Polen: das [EWIB](https://ewib.nbp.pl/) der Polnischen Nationalbank (NBP) mit allen Abrechnungsnummern
    (Zentralen und Filialen), neu übernommen ab dem Tag jeder Veröffentlichung
  - Litauen: die [Liste der Finanzinstitutscodes](https://www.lb.lt/en/iban-and-financial-institution-codes) der
    Lietuvos bankas
  - Lettland: die [BIC-Liste](https://www.bank.lv/darbibas-jomas/maksajumu-sistemas-uzdevumi/bic-noteiksana-pec-iban)
    der Latvijas Banka
  - Estland: die Listen der IBAN-Bankcodes der [Finanzaufsicht Finantsinspektsioon](https://www.fi.ee/et/pangandus-ja-krediit/krediidivaldkonna-tegevuslubade-taotlemine/krediidiasutuse-rahvusvahelise-kontonumbri-tunnuskood),
    die die Codes vergibt; BICs über GLEIF
  - Niederlande: **abgeleitet, nicht amtlich** – Kreditinstitute und Zahlungsdienstleister aus den Listen der
    [Europäischen Zentralbank](https://www.ecb.europa.eu/stats/financial_corporations/list_of_financial_institutions/html/index.en.html),
    deren niederländische BICs von GLEIF und daraus der Bankcode. Die amtliche Liste der Betaalvereniging Nederland
    darf nicht weitergegeben werden.
  - Italien: die Register der [Banca d'Italia](https://www.bancaditalia.it/servizi-cittadino/servizi/albi-elenchi/index.html)
    (Institute, Filialen mit CAB-Code, Fusionen). Die Banca d'Italia führt keine BICs; sie werden über die
    [BIC/LEI-Zuordnung von GLEIF](https://www.gleif.org/en/lei-data/lei-mapping/download-bic-to-lei-relationship-files) ergänzt.
- **Es vergleicht sie mit dem letzten Stand** und hält fest, welche Banken neu dazugekommen sind, sich geändert
  haben oder weggefallen sind, z. B. durch eine Fusion.
- Weggefallene Banken **bleiben nachvollziehbar**. Die offiziellen Listen zeigen nur den aktuellen Stand, hier
  bleibt der letzte Stand jeder Bank erhalten – in Deutschland, der Schweiz und Liechtenstein samt
  Nachfolge-Bankleitzahl, wenn es eine gibt.

## So nutzt du es

👉 **[alexanderwendel8.github.io/bic-verzeichnis](https://alexanderwendel8.github.io/bic-verzeichnis/)**

- **Land wählen:** oben das Land umschalten (AT, DE, CH, LI, IT, CZ, SK, HU, SI, BE, ES, FR, PL, LV, LT, EE, NL).
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

Ein Projekt von Alexander Wendel. Die Daten stammen von OeNB, Deutscher Bundesbank, SIX, Banca d'Italia (BICs: GLEIF), ČNB, NBS, MNB,
Banka Slovenije, NBB, Banco de España (BICs: GLEIF), ACPR (BICs: GLEIF), NBP, Latvijas Banka, Lietuvos bankas, Finantsinspektsioon (BICs: GLEIF) und EZB (NL, abgeleitet über GLEIF) und werden ohne Gewähr weitergegeben.

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

- **Land:** `AT`, `DE`, `CH`, `LI`, `IT`, `CZ`, `SK`, `HU`, `SI`, `BE`, `ES`, `FR`, `PL`, `LV`, `LT`, `EE` oder `NL`, Kleinbuchstaben gehen auch.
- **Bankleitzahl Österreich:** wie in der IBAN fünfstellig (`00100`) oder ohne führende Nullen (`100`).
- **Bankleitzahl Deutschland:** immer achtstellig (`10010010`).
- **Bankleitzahl Schweiz/Liechtenstein:** die IID, fünfstellig (`00100`) oder ohne führende Nullen (`100`).
- **Bankleitzahl Tschechien:** vierstellig (`0800`). **Slowakei:** vierstellig (`0200`) oder ohne führende Nullen (`200`).
- **Bankleitzahl Ungarn:** der achtstellige Filialcode (`11738008`). **Slowenien:** fünfstellig (`01000`).
- **Bankleitzahl Belgien:** der dreistellige Bank-Identifikationscode (`310`). **Spanien:** vierstellig (`0049`).
- **Bankleitzahl Frankreich:** der Code banque, fünfstellig (`30004`). **Polen:** die Abrechnungsnummer, achtstellig (`10501445`).
- **Bankleitzahl Litauen:** fünfstellig (`73000`). **Lettland:** vier Buchstaben (`HABA`, auch `haba`).
- **Bankleitzahl Estland:** zweistellig (`22`). **Niederlande:** vier Buchstaben (`INGB`, auch `ingb`).
- **Bankleitzahl Italien:** der ABI-Code, fünfstellig (`03069`) oder ohne führende Nullen (`3069`). Die CAB-Codes
  stehen in `filialen`.
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
- **Belgien:** jeder dreistellige Code ist ein Eintrag; eine Bank hat oft mehrere Codes mit demselben BIC. Dazu `namen`
  (`nl`, `fr`, `de`, `en`, nicht immer alle vorhanden; `name` ist der erste vorhandene) und `version` der Liste.
  Keine Adressen. Freie und nicht verfügbare Codes sind nicht enthalten.
- **Spanien:** `art` (z. B. Banco, Cooperativa de crédito, Entidad de pago, Sucursal …), `art_code`, `nif`, `lei`,
  `muttergesellschaft`, `eingetragen_seit`, `adresse` mit `provinz`, `herkunftsland`, `kontakt`. Wie in Italien stammt
  der `bic` **von GLEIF** (`bic_quelle`: `GLEIF`), verknüpft über den LEI aus dem Register. Banken und Genossenschaftsbanken
  haben fast alle einen BIC, Zweigstellen ausländischer Banken (z. B. ING, `1465`) meist nicht, weil das Register für
  sie keinen LEI führt – dann ist `bic` `null`. Neben Banken stehen im Register auch Zahlungs- und E-Geld-Institute,
  Repräsentanzen, Wechselstuben, Bewertungsgesellschaften u. a. Frühere Codes abgemeldeter Institute (rund 1.800, seit
  1948) liefern `status: entfernt` mit Abmeldedatum, `abmeldegrund` und `nachfolge_bankleitzahl`, wenn es einen gibt.
- **Frankreich:** `kategorie` (Liste, z. B. Établissement de Crédit, Société de financement), `rechtsform`, `zulassung`,
  `siren`, `lei`, `code_seit`, `weitere_codes` (weitere CIBs desselben Instituts; jeder CIB ist ein eigener Eintrag),
  `handelsnamen`, `kuerzel`, `muttergesellschaft`, `ereignisse` (z. B. Übernahmen), `adresse`, `stand` (letzte
  inhaltliche Änderung). Der `bic` stammt **von GLEIF** (`bic_quelle`: `GLEIF`), verknüpft über den LEI; für rund
  zwei Drittel der Codes gibt es einen. GLEIF ist nicht vollständig; wichtige Lücken und Fehler (z. B. Société Générale,
  LCL, Crédit Mutuel) behebt eine kleine, von Hand gepflegte Liste – diese BICs haben `bic_quelle`: `manuell`, ein
  abweichender GLEIF-BIC steht dann in `weitere_bics`.
- **Polen:** jede Abrechnungsnummer (Zentrale, Filiale, interne Einheit) ist ein Eintrag; `name` ist das Institut,
  dazu `bezeichnung` der Nummer, `einheit`, `art_der_einheit`, `institutsnummer`, `institutsart`, `untertyp`, `lei`,
  `nip`, `adresse` mit `woiwodschaft`, `kontakt`, `vergeben_am` und `version` (EWIB-Veröffentlichung). Neben `bic`
  stehen in `bics` die BICs für SEPA, SORBNET 3 und TARGET 2, soweit die NBP sie nennt.
- **Litauen:** `filiale`, `registernummer`, `adresse`, `gueltig_ab` der verwendeten Liste. Mehrere Codes können
  denselben BIC haben (Filialen, frühere Codes). **Lettland:** nur Bankcode, BIC, Name, `iban_struktur` und
  `gueltig_ab` (Datum der letzten Aktualisierung der Liste).
- **Estland:** `art` (Kreditinstitut, Filiale, Zahlungs- oder E-Geld-Institut), `weitere_codes` (Luminor hat `96` und
  `17`), `lei`. Der `bic` stammt **von GLEIF** (`bic_quelle`: `GLEIF`), verknüpft über den Namen; für drei Filialen
  ausländischer Banken aus einer kleinen, von Hand gepflegten Liste (`bic_quelle`: `manuell`). **Nur für nicht
  kommerzielle Zwecke:** eine kommerzielle Weiterverwendung der estnischen Codes braucht eine Erlaubnis der
  Finantsinspektsioon (siehe [Quellen und Lizenzen](#quellen-und-lizenzen)).
- **Niederlande:** `abgeleitet: true` – Bankcode und BIC stammen nicht aus einer amtlichen Liste, sondern aus GLEIF
  (Bankcode = erste vier Zeichen des BIC). Dazu `art`, `lei`, `ezb_kennung`, `ezb_liste` (MFI oder PSRI),
  `muttergesellschaft` (bei Filialen) und `adresse`. **Unvollständig:** rund 90 Codes, die amtliche Liste hat rund
  100; es fehlen Codes, für die GLEIF keinen BIC kennt (z. B. ASN `ASNB`, Knab), und einzelne abgeleitete Codes
  werden nicht für niederländische IBANs vergeben.
- **Italien:** `register` (Bank, Zahlungsinstitut, E-Geld-Institut), `rechtsform`, `steuernummer`, `registernummer`,
  `eingetragen_seit`, `filialen` (mit `cab`, Adresse, `eroeffnet`). Der `bic` stammt **nicht von der Banca d'Italia,
  sondern von GLEIF** (`bic_quelle`: `GLEIF`); weitere BICs desselben Instituts stehen in `weitere_bics`. Für etwa jedes
  siebte Institut findet GLEIF keinen BIC – dann ist `bic` `null`. Frühere ABI-Codes aus Übernahmen und Fusionen
  (rund 1.700, seit 1970) liefern `status: entfernt` mit Datum und `nachfolge_bankleitzahl` (heute aktiver Nachfolger).
- **Unbekannte Bankleitzahl oder unbekanntes Land:** Antwort mit HTTP-Status **404**.
- **Weggefallene Banken** liefern weiter ihren letzten Stand, mit `"status": "entfernt"` und dem Datum in `entfernt_am`.
- Leere Felder sind `null`, Datumsangaben im Format `JJJJ-MM-TT`.
- Die API darf aus jedem Browser und jeder Webseite abgefragt werden (CORS ist offen).
- Aktualisiert wird täglich zusammen mit der Webseite.
- **Quellenangaben sind Pflicht:** Wer Daten aus der API verwendet, muss die Quellenangaben des jeweiligen Landes
  sichtbar darstellen – siehe [Quellen und Lizenzen](#quellen-und-lizenzen).

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
| `laender/at.py`, `de.py`, `ch.py`, `li.py`, `it.py`, `cz.py`, `sk.py`, `hu.py`, `si.py`, `be.py`, `es.py`, `fr.py`, `pl.py`, `lv.py`, `lt.py`, `ee.py`, `nl.py` | je Land: Download, Umwandlung, API-Felder, Einstellungen der Webseite |
| `laender/_six.py` | gemeinsame SIX-Quelle für die Schweiz und Liechtenstein |
| `laender/_xlsx.py` | liest Excel-Dateien (`.xlsx`) ohne Zusatzbibliothek (Ungarn, Belgien, Spanien) |
| `laender/_gleif.py` | BICs aus der BIC/LEI-Zuordnung von GLEIF samt SWIFT-Hinweis (Italien, Spanien, Frankreich, Estland, Niederlande), je Lauf nur einmal geladen, und Korrekturlisten |
| `kern.py` | gemeinsamer Teil: Vergleich, Änderungsprotokoll, Ablage, API-Einträge |
| `update.py` | lädt alle (oder ausgewählte) Länder und protokolliert Änderungen |
| `build_site.py` | stellt Webseite, `laender.json` und API für GitHub Pages zusammen (API nicht im Repo abgelegt) |
| `web/` | Weboberfläche (statisch, ohne Build-Schritt; Länder kommen aus `laender.json`) |
| `data/<land>/bankleitzahlen.csv` | aktueller Stand, eine Zeile je Bankleitzahl |
| `data/<land>/filialen.csv` | weitere Orte je Bankleitzahl (Deutschland: Zusatzeinträge, Italien: Filialen mit CAB) |
| `data/<land>/meta.json` | Angaben zur verwendeten Quelldatei (z. B. Gültigkeit in DE, CZ und HU, Version in BE, frühere Codes in ES, Stand in FR, Veröffentlichung in PL, verwendete Datei in LT und LV, Stand der Listen in EE, PSRI-Liste in NL, Überführungen in CH/LI, Fusionen in IT) |
| `changes/<land>/JJJJ-MM-TT.csv` | Änderungen eines Tages (nur an Tagen mit Änderungen) |
| `changes/<land>/index.json` | Liste der Tage mit Änderungen |

`<land>` ist der Ländercode in Kleinbuchstaben (`at`, `de`, `ch`, `li`, `it`, `cz`, `sk`, `hu`, `si`, `be`, `es`, `fr`, `pl`, `lv`, `lt`, `ee`, `nl`). Die frühere Adresse der österreichischen
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

**Belgien – Besonderheiten der Quelle:**

- Die NBB bietet die Liste nur als Excel (`.xlsx`) und PDF an, kein XML, JSON oder CSV. Verwendet wird die vollständige
  Liste (`full_list_current.xlsx`, je Code eine Zeile); die erste Zeile nennt die Version (z. B. „Version 01/09/2026“),
  neue Versionen werden unter diesem Tag protokolliert.
- Die Liste enthält alle Codes 000–999; freie („VRIJ“/„LIBRE“) und nicht verfügbare Codes werden weggelassen.
- BICs stehen in der Datei mit Leerzeichen („GEBA BE BB“) und werden ohne Leerzeichen abgelegt; Platzhalter wie
  „N/A“ oder „NYA“ gelten als „kein BIC“.

**Spanien – Besonderheiten der Quelle:**

- Der Banco de España bietet das Register nur als Excel (`Registro_Entidades.xlsx`, täglich neu) und als Webanwendung
  ohne offene Schnittstelle an; kein XML, JSON oder CSV. Die Statistiklisten (MFI/PSRI, CSV) enthalten weniger Institute
  und keine Abmeldungen und werden deshalb nicht verwendet.
- Übernommen werden Einträge mit vierstelligem `CÓDIGO BE` ohne Abmeldedatum. Abgemeldete Codes, die heute nicht
  vergeben sind, stehen mit Name, Datum, Grund und Nachfolger in `data/es/meta.json`; Ketten von Nachfolgern werden
  bis zum heute aktiven Code verfolgt.
- BICs: GLEIF-Zuordnung BIC → LEI (nur BICs mit Ländercode `ES`), verknüpft über den LEI aus dem Register; ohne LEI
  ersatzweise über die Steuernummer (NIF = `registeredAs` bei GLEIF). Ist GLEIF nicht erreichbar, bleiben die BICs
  des letzten Stands erhalten.
- Die Originaldatei (rund 1,7 MB) ändert sich täglich, schon wegen des Datums in der ersten Zeile. Damit das Repository
  nicht jeden Tag um 1,7 MB wächst, wird sie nicht abgelegt, sondern beim Banco de España verlinkt.

**Frankreich – Besonderheiten der Quelle:**

- REGAFI bietet eine offene Schnittstelle mit Export als **JSON** (daneben CSV, XLSX u. a.), täglich aktualisiert.
  Abgefragt wird nur der Teil mit code interbancaire (`where=cib != "[]"`): rund 840 Institute und 0,7 MB statt
  26.000 Einträgen und 18 MB. Das Feld `cib` ist eine JSON-Liste als Text und wird ein zweites Mal gelesen.
- REGAFI bricht Verbindungen gelegentlich ab; der Download wird bis zu viermal versucht.
- BICs: GLEIF-Zuordnung BIC → LEI, nur BICs aus Frankreich, Monaco und den Überseegebieten, französische bevorzugt.
- **Korrekturliste** `laender/fr_bic_korrekturen.csv` (Bankleitzahl, BIC, Institut, Beleg, Geprüft am): füllt Lücken
  von GLEIF oder ersetzt einen falschen Haupt-BIC. Derzeit 19 Einträge (16 Lücken, 3 Korrekturen), geprüft anhand der
  öffentlichen Erreichbarkeitslisten von EBA CLEARING (STEP2, RT1) und teils Wikidata. Die Einträge wurden einzeln von
  Hand übernommen, die Listen selbst werden weder automatisch ausgewertet noch weitergegeben. Steht ein Code nicht mehr
  in REGAFI, warnt das Skript. Neue Einträge nur mit Beleg (z. B. Angabe der Bank auf ihrer Website oder ihrem RIB).
- Die Quellenangabe muss das Datum der letzten Aktualisierung nennen. Gespeichert wird das Datum der letzten
  inhaltlichen Änderung (`Stand` in `data/fr/meta.json`), damit nicht jeden Tag ein Commit entsteht.
- Die Originaldaten werden nicht abgelegt, sondern als Abfrage bei REGAFI verlinkt.

**Polen – Besonderheiten der Quelle:**

- Die NBP bietet EWIB als **XML** (`plewiba.xml`, rund 11 MB), als Textdatei in CP852 und als Abfrage-Schnittstelle an;
  verwendet wird das XML. Es ist nach Institut → Einheit → Abrechnungsnummer gegliedert; je Nummer eine Zeile.
- Nummer und Datum der Veröffentlichung (z. B. „Pub.wer.533“, 2026-11-27) stehen nur auf der Download-Seite und
  werden dort gelesen. Eine neue Veröffentlichung wird unter ihrem Datum protokolliert.
- Öffnungszeiten und Dienstleistungen der Einheiten werden nicht übernommen. Die Originaldatei wird bei der NBP
  verlinkt statt abgelegt.

**Litauen, Lettland – Besonderheiten der Quellen:**

- Beide Notenbanken bieten kein XML oder JSON an. **Lietuvos bankas:** CSV (Windows-1257), XLSX und PDF, verwendet
  wird die englische CSV. Der Dateiname enthält das Datum (`FIK_KODAI_20261118-en.csv`), und die Übersichtsseite ist
  für Programme gesperrt (Browser-Prüfung). Das Skript probiert deshalb die Dateinamen der letzten 21 Tage durch
  (nur kurze Anfragen ohne Download) und nimmt die neueste Datei; die zuletzt gefundene steht in `data/lt/meta.json`.
- **Latvijas Banka:** nur eine Excel-Datei im alten `.xls`-Format, die sich ohne Zusatzbibliothek nicht lesen lässt.
  Gelesen wird dieselbe Tabelle von der Webseite (HTML); die `.xls`-Datei wird verlinkt. Der Server lehnt den
  Standard-User-Agent von Python ab und bricht Verbindungen gelegentlich ab (bis zu vier Versuche).

**Estland – Besonderheiten der Quelle:**

- Die zweistelligen Codes vergibt seit 2017 die Finanzaufsicht Finantsinspektsioon. Ihre amtliche Liste steht auf zwei
  Seiten (Kreditinstitute; Zahlungs- und E-Geld-Institute) nur als HTML-Tabelle, jeweils mit „Viimati muudetud“
  (zuletzt geändert). Die ältere Liste des Bankenverbands Pangaliit ist nicht mehr aktuell und wird nur zur Kontrolle
  herangezogen.
- BICs führt die Finantsinspektsioon nicht. Sie kommen aus der GLEIF-Zuordnung (nur estnische BICs), verknüpft über den
  Namen (rechtlicher und weitere Namen bei GLEIF, ohne Rechtsformzusätze). Filialen ausländischer Institute führt GLEIF
  unter dem LEI der Mutter; für sie gibt es `laender/ee_bic_korrekturen.csv` (derzeit Citadele `12`, OP `51`, Banqup `72`).

**Niederlande – abgeleitet aus EZB-Listen und GLEIF:**

- Die vollständige Liste der niederländischen Bankcodes führt die Betaalvereniging Nederland. Ihre Bedingungen verbieten
  die Weitergabe ohne schriftliche Erlaubnis; De Nederlandsche Bank und die EZB veröffentlichen keine Bankcodes oder BICs.
- Da der Bankcode den ersten vier Zeichen des BIC entspricht, wird er abgeleitet:
  1. Institute aus der täglichen **MFI-Liste** der EZB (Kreditinstitute und Zentralbank, CSV in UTF-16, gezippt; der
     Dateiname wechselt täglich und wird von der Seite gelesen) und der halbjährlichen **PSRI-Liste** (Zahlungs- und
     E-Geld-Institute, XLSX in einem ZIP; verwendet wird die neueste),
  2. deren niederländische BICs aus der GLEIF-Zuordnung über den LEI, bei Filialen ausländischer Banken auch über den
     LEI der Mutter,
  3. Bankcode = BIC[0:4]; Haupt-BIC je Code wie in Italien (voll verbunden, bevorzugt `…XXX`).
- In der API steht `abgeleitet: true`, auf der Webseite ein deutlicher Hinweis.

**Italien – Besonderheiten der Quelle:**

- Die Banca d'Italia bietet in ihrem Download-Bereich („Area download“ der Register) täglich aktualisierte Dateien als
  **XML** (gezippt) an – verwendet werden „Lista intermediari“, „Lista succursali banche“ und „Lista fusioni,
  incorporazioni …“. Die Dateinamen sind nicht fest veröffentlicht; das Skript holt jedes Mal die Produktliste der
  Webanwendung. Der Abruf ist ohne Anmeldung möglich; die Anwendung leitet dabei automatisch über
  `auth.bancaditalia.it` und schickt für anonyme Besucher selbst `username=OBLIXANONYMOUS` mit.
- Die Dateien enthalten auch frühere Fassungen jedes Eintrags; verwendet wird nur die heute gültige
  (`DATA_I_VAL`/`DATA_F_VAL`). Übernommen werden Banken, Zahlungs- und E-Geld-Institute mit ABI-Code.
- Die Filialliste ist entpackt rund 200 MB groß und wird beim Lesen gestreamt.
- BICs: GLEIF-Zuordnung BIC → LEI, dann LEI-Datensätze (`registeredAs` = italienische Steuernummer) → Institut.
  Als Haupt-BIC gilt ein voll verbundener BIC, bevorzugt der des Hauptsitzes (`…XXX`). Ist GLEIF nicht erreichbar,
  bleiben die BICs des letzten Stands erhalten.
- Ein Lauf dauert etwa eine Minute (rund 10 MB Download plus GLEIF).

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

---

## Quellen und Lizenzen

Die Daten stammen von den unten genannten Notenbanken und Stellen. Sie erlauben die Weitergabe, verlangen aber
**Quellenangaben** und teils einen Hinweis auf Änderungen. Auf der Webseite stehen die Angaben des gewählten Landes in
der Fußzeile, direkt neben dem CSV-Download.

**Bei Verwendung der API oder der CSV-Dateien sind die Quellenangaben sichtbar darzustellen** – mit dem Wortlaut aus
der Tabelle für jedes Land, dessen Daten verwendet werden, und einem Link zu den Nutzungsbedingungen, z. B. in der
Fußzeile, im Impressum oder direkt bei den angezeigten Daten. Für BICs aus Italien, Spanien, Frankreich, Estland und den Niederlanden (dort auch für die Bankcodes) ist zusätzlich der SWIFT-Hinweis
(unten) Pflicht. Die Quellen übernehmen keine Haftung für Richtigkeit und Vollständigkeit; dasselbe gilt für dieses
Verzeichnis.

| Land | Quelle | Pflichtangabe (Wortlaut) | Bedingungen |
|---|---|---|---|
| AT | Oesterreichische Nationalbank (CC BY 4.0) | Quelle: Oesterreichische Nationalbank (OeNB), SEPA-Zahlungsverkehrs-Verzeichnis, Lizenz CC BY 4.0. Geändert: Hinweiszeilen entfernt, in UTF-8 umgewandelt. | [Impressum & Haftung, Abschnitt 2.2](https://www.oenb.at/Service/Impressum-und-Haftung.html), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.de) |
| DE | Deutsche Bundesbank | Quelle: Deutsche Bundesbank | [Nutzungsbedingungen, Abschnitt 4](https://www.bundesbank.de/de/startseite/benutzerhinweise/nutzungsbedingungen-fuer-den-allgemeinen-gebrauch-der-website-763554): speichern, weitergeben und vervielfältigen frei, „Die Informationen dürfen nicht verändert oder verfälscht werden.“ |
| CH, LI | SIX Interbank Clearing | Quelle: SIX Interbank Clearing, Bank Master. BICs sind Eigentum von S.W.I.F.T. SCRL. | [Record Description](https://www.six-group.com/dam/download/banking-services/interbank-clearing/bc-bank-master/bankmaster-v3.0-record-description-en.pdf): „Information in the Download Bank Master may be used freely.“ |
| IT | Banca d'Italia (Open Data, CC BY 4.0) | Fonte: Banca d'Italia – Albi ed elenchi di vigilanza, Lizenz CC BY 4.0. Geändert: gefiltert, umformatiert, BICs von GLEIF ergänzt. | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.de), Datensätze auf [dati.gov.it](https://www.dati.gov.it) |
| IT, ES, FR, EE, NL (BICs) | SWIFT / GLEIF, BIC/LEI-Zuordnung | SWIFT-Hinweis, siehe unten | [License Agreement](https://www.gleif.org/lei-data/lei-mapping/download-bic-to-lei-relationship-files/2017-12-21_annex-2_bic-to-lei-mapping-table-license-agreement_final.pdf) |
| CZ | Česká národní banka | Source: the CNB (Zdroj: ČNB). | [Terms and conditions](https://www.cnb.cz/en/privacy-statement-and-disclaimer/disclaimer-copyright/) |
| SK | Národná banka Slovenska | Zdroj: Národná banka Slovenska. | [Disclaimer](https://nbs.sk/disclaimer-sk/) |
| HU | Magyar Nemzeti Bank | Forrás: Magyar Nemzeti Bank. | [Disclaimer](https://www.mnb.hu/en/the-central-bank/practical-issues/disclaimer) |
| SI | Banka Slovenije | Vir: Banka Slovenije. Geändert: umformatiert, Spalten umbenannt. | [Disclaimer and Copyright](https://bsi.si/en/disclaimer-and-copyright) |
| BE | Nationale Bank van België / Banque Nationale de Belgique | Source: National Bank of Belgium (NBB). | [Copyright and use information](https://www.nbb.be/en/disclaimer-and-legal-information/copyright-and-use-information): „may be distributed or reproduced, provided the integrity and accuracy thereof are maintained and the NBB is acknowledged as the source“ |
| FR | ACPR / Banque de France, REGAFI | Source : ACPR – REGAFI, données mises à jour le [Datum]. Geändert: gefiltert, umformatiert, BICs von GLEIF ergänzt. | REGAFI selbst nennt keine Lizenz. Grundlage: französisches Recht zur Weiterverwendung öffentlicher Informationen ([CRPA L321-1 ff.](https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000031366350/LEGISCTA000031367685/)) und die [rechtlichen Hinweise der Banque de France](https://www.banque-france.fr/fr/infos-legales): „faire clairement apparaître comme source la Banque de France ou l'Autorité de contrôle prudentiel et de résolution ainsi que la date de la dernière mise à jour“, Daten nicht verfälschen |
| PL | Narodowy Bank Polski, EWIB | Źródło: Narodowy Bank Polski – EWIB, ewib.nbp.pl (stan na [Datum], Pub.wer.[Nummer]); dane przetworzone. | Die NBP nennt für EWIB keine Nutzungsbedingungen. Grundlage: polnisches Gesetz über offene Daten und die Weiterverwendung öffentlicher Informationen ([Dz.U. 2021 poz. 1641](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20210001641)): Quelle, Stand und Verarbeitung angeben |
| LT | Lietuvos bankas | Šaltinis: Lietuvos bankas. | [Informacijos naudojimo sąlygos](https://www.lb.lt/lt/informacijos-naudojimo-salygos): „prašome kaip šaltinį nurodyti Lietuvos banką“ (bitte die Lietuvos bankas als Quelle nennen) |
| LV | Latvijas Banka | Avots: Latvijas Banka. | Keine eigenen Bedingungen für die BIC-Liste. Angewandt werden die [Bedingungen für statistische Informationen](https://www.bank.lv/statistika/informacija-statistikas-lietotajiem/datu-izmantosana): Latvijas Banka als Quelle nennen, Daten nicht verfälschen |
| EE | Finantsinspektsioon | Allikas: Finantsinspektsioon. Geändert: zwei Listen zusammengeführt, BICs von GLEIF ergänzt. | [Veebilehe info ja kasutustingimused](https://www.fi.ee/et/veebilehe-info-ja-kasutustingimused): Verbreiten nur mit vorheriger Erlaubnis; erlaubt ist die Nutzung „ajakirjanduses ja mittetulunduslikel eesmärkidel, kui märgitakse ära informatsiooni allikas“ (in der Presse und für nicht kommerzielle Zwecke mit Quellenangabe), Änderungen kenntlich machen. **Kommerzielle Weiterverwendung der estnischen Codes nur mit Erlaubnis der Finantsinspektsioon.** |
| NL | Europäische Zentralbank (MFI- und PSRI-Liste) | Source: European Central Bank. Geändert: gefiltert; Bankcode und BIC abgeleitet über GLEIF, nicht amtlich. | [Disclaimer](https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html): „users of this website may make free use of the information obtained directly from it … it must appear accurately and the ECB must be cited as the source“; Änderungen ausdrücklich kennzeichnen |
| ES | Banco de España | Fuente: Banco de España. Geändert: gefiltert, umformatiert, BICs von GLEIF ergänzt. | [Aviso legal](https://www.bde.es/wbe/es/pie/aviso-legal/): Wiedergabe erlaubt, wenn sie „fielmente, sin manipular ni alterar los contenidos“ erfolgt und der Banco de España als Quelle genannt wird |

**SWIFT-Hinweis für die italienischen, spanischen, französischen, estnischen und niederländischen BICs** (Pflicht für jede Kopie, auch in Teilen; `[Monat Jahr]` = Stand der
verwendeten Zuordnungstabelle, auf der Webseite und in `data/it/`, `data/es/`, `data/fr/`, `data/ee/` und `data/nl/HINWEIS-BIC.txt` jeweils eingesetzt):

> SWIFT © and database rights [Monat Jahr]. All rights reserved. This Mapping Table has been developed by SWIFT. Any use
> of the Mapping Table, in whole or in part, is subject to the BIC/LEI Mapping Table License Agreement as published with
> the Mapping Table available on GLEIF's website. The Mapping Table is updated monthly. For the latest BIC information and
> updates, always refer to www.swift.com/bic .

Die LEI-Daten von GLEIF (für die Zuordnung über die Steuernummer in Italien und Spanien, über den LEI in Spanien und Frankreich) stehen unter
[CC0](https://www.gleif.org/en/meta/lei-data-terms-of-use).

**Unveränderte Originale:** Deutsche Bundesbank, ČNB, NBS und MNB erlauben die Weitergabe nur ohne inhaltliche
Änderung, die NBB verlangt, dass Vollständigkeit und Richtigkeit erhalten bleiben. Das Verzeichnis ändert die Angaben nicht, formatiert bzw. strukturiert sie aber um (Spaltennamen, „ja“/„nein“
statt „A“ oder „x“, Adressen in Felder aufgeteilt, in Deutschland Zusatzeinträge als Filialen und ohne
Änderungskennzeichen). Deshalb liegen die Originaldateien unverändert bei: `data/de/original-bundesbank.xml` (die jeweils
gültige Bankleitzahlendatei), `data/cz/original-cnb.csv`, `data/sk/original-nbs.csv`, `data/hu/original-mnb.xlsx`,
`data/be/original-nbb.xlsx`,
`data/lt/original-lb.csv` – auf
der Webseite als „Originaldatei“ verlinkt. Auch der Banco de España verlangt eine Wiedergabe ohne Änderung des
Inhalts; seine täglich neue Originaldatei wird auf der Webseite direkt beim Banco de España verlinkt, ebenso die
Originaldaten von REGAFI (Frankreich), EWIB (Polen) und die `.xls`-Datei der Latvijas Banka.

**Logos** der Notenbanken werden nicht verwendet; deren Nutzung ist bei allen Quellen genehmigungspflichtig.

**Frankreich und Polen** haben keine ausdrücklichen Nutzungsbedingungen für diese Daten; die Weitergabe stützt sich auf
die gesetzlichen Regeln zur Weiterverwendung öffentlicher Informationen. Eine schriftliche Bestätigung von ACPR bzw.
NBP liegt nicht vor.

Stand der Prüfung der Nutzungsbedingungen: 27.11.2026. Das ist keine Rechtsberatung.
