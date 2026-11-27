"""Österreich – SEPA-Zahlungsverkehrs-Verzeichnis der Oesterreichischen Nationalbank (OeNB).

Die OeNB aktualisiert die CSV täglich. Sie ist Latin-1-kodiert, nutzt Semikolons und hat vor
der Kopfzeile einige Hinweiszeilen sowie die Zeile „SEPA-Verzeichnis-Abfrage vom TT.MM.JJJJ“.
Die Bankleitzahl ist eindeutig und in der IBAN fünfstellig (Stellen 5–9).
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import re

from kern import SCHLUESSEL, Stand, herunterladen, leer

CODE = "AT"
NAME = "Österreich"
BLZ_STELLEN = 5  # kürzere Bankleitzahlen zusätzlich fünfstellig abrufbar (100 -> 00100)
URL = "https://www.oenb.at/docroot/downloads_observ/sepa-zv-vz_gesamt.csv"
QUELLE = {
    "name": "Oesterreichische Nationalbank – SEPA-Zahlungsverkehrs-Verzeichnis",
    "kurz": "OeNB",
    "url": "https://www.oenb.at/Statistik/Klassifikationen/SEPA-Zahlungsverkehrs-Verzeichnis.html",
    "bedingungen": "https://www.oenb.at/Service/Impressum-und-Haftung.html",
    "hinweis": "Quelle: Oesterreichische Nationalbank (OeNB), SEPA-Zahlungsverkehrs-Verzeichnis.",
}
# frühere Adresse der Gesamtliste, wird beim Veröffentlichen weiter bedient
ALTE_CSV_ADRESSE = "data/sepa-zv-vz_gesamt.csv"


def laden(args, alte_meta: dict) -> Stand:
    roh = args.input[0].read_bytes() if args.input else herunterladen(URL)
    text = roh.decode("latin-1")
    zeilen = text.splitlines()

    stichtag = None
    for z in zeilen:
        m = re.search(r"Abfrage vom (\d{2})\.(\d{2})\.(\d{4})", z)
        if m:
            stichtag = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            break
    try:
        start = next(i for i, z in enumerate(zeilen) if z.startswith("Kennzeichen;"))
    except StopIteration:
        raise RuntimeError("Kopfzeile im OeNB-CSV nicht gefunden – Format geändert?")

    reader = csv.DictReader(io.StringIO("\n".join(zeilen[start:])), delimiter=";")
    spalten = [c.strip() for c in reader.fieldnames or []]
    if SCHLUESSEL not in spalten:
        raise RuntimeError(f"Spalte '{SCHLUESSEL}' fehlt im OeNB-CSV.")
    banken = []
    for r in reader:
        z = {c: (r.get(c) or "").strip() for c in spalten}
        if z[SCHLUESSEL]:
            banken.append(z)
    datum = (stichtag or args.today).isoformat()
    print(f"[{CODE}] OeNB-Verzeichnis vom {datum}: {len(banken)} Einträge")
    return Stand(spalten=spalten, banken=banken, datum=datum)


# ---------------------------------------------------------------- API

def _leer(wert):
    wert = leer(wert)
    return None if wert == "nullnull" else wert


def _datum(wert):
    wert = _leer(wert)
    m = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", wert or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else wert


def _homepage(wert):
    wert = _leer(wert)
    if wert and not re.match(r"https?://", wert):
        wert = "https://" + wert
    return wert


def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    g = z.get
    return {
        "land": CODE,
        "bankleitzahl": _leer(g("Bankleitzahl")),
        "bic": _leer(g("SWIFT-Code")),
        "name": _leer(g("Bankenname")),
        "status": None,
        "entfernt_am": None,
        "art": _leer(g("Kennzeichen")),
        "sektor": _leer(g("Sektor")),
        "institutsart": _leer(g("Institutsart")),
        "identnummer": _leer(g("Identnummer")),
        "firmenbuchnummer": _leer(g("Firmenbuchnummer")),
        "lei": _leer(g("LEI")),
        "gruendungsdatum": _datum(g("Gründungsdatum")),
        "adresse": {"strasse": _leer(g("Straße")), "plz": _leer(g("PLZ")), "ort": _leer(g("Ort")),
                    "bundesland": _leer(g("Bundesland"))},
        "postadresse": {"strasse": _leer(g("Postadresse / Straße")), "plz": _leer(g("Postadresse / PLZ")),
                        "ort": _leer(g("Postadresse / Ort")), "postfach": _leer(g("Postfach"))},
        "kontakt": {"telefon": _leer(g("Telefon")), "fax": _leer(g("Fax")), "email": _leer(g("E-Mail")),
                    "homepage": _homepage(g("Homepage"))},
    }


# ---------------------------------------------------------------- Webseite

WEB = {
    "suche_platzhalter": "Bankleitzahl, BIC, Bankname, Ort oder LEI …",
    "suche": ["bankleitzahl", "bic", "name", "adresse.plz", "adresse.ort", "lei", "adresse.bundesland", "sektor"],
    "filter": [{"feld": "adresse.bundesland", "alle": "Alle Bundesländer"}, {"feld": "sektor", "alle": "Alle Sektoren"}],
    "spalte5": {"titel": "Sektor", "feld": "sektor"},
    "aenderung_name": "Bankenname",
    "aenderung_bic": "SWIFT-Code",
    "hinweis_aenderungen": "Täglicher Vergleich mit dem Vortag. Banken, die aus dem OeNB-Verzeichnis "
                           "verschwinden, bleiben hier mit ihrem letzten Stand erhalten.",
    "details": [
        ["Bankleitzahl", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"], ["LEI", "lei", "lei"],
        ["Art", "art"], ["Sektor", "sektor"], ["Institutsart", "institutsart"],
        ["Identnummer", "identnummer"], ["Firmenbuchnummer", "firmenbuchnummer"],
        ["Adresse", "adresse", "adresse"], ["Postadresse", "postadresse", "adresse"],
        ["Bundesland", "adresse.bundesland"], ["Telefon", "kontakt.telefon"], ["Fax", "kontakt.fax"],
        ["E-Mail", "kontakt.email", "email"], ["Homepage", "kontakt.homepage", "url"],
        ["Gründungsdatum", "gruendungsdatum", "datum"],
    ],
}


def stand_text(meta: dict) -> str:
    return ""
