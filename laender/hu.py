"""Ungarn – Rövid irányítókód-tábla (Short Routing Table) der Ungarischen Nationalbank (MNB).

- Angeboten wird nur eine Excel-Datei (.xlsx), kein XML, JSON oder CSV. Eine .xlsx besteht intern
  aus XML; sie wird ohne Zusatzbibliothek gelesen (laender/_xlsx.py).
- Jede Zeile ist ein achtstelliger Filialcode (pénzforgalmi irányítókód): 3 Stellen Bankcode,
  4 Stellen Filiale, 1 Prüfziffer. Genau diese 8 Stellen stehen in der IBAN an den Stellen 5–12,
  daher dienen sie hier als Bankleitzahl.
- Der Blattname (z. B. „SHT20261101“) nennt das Gültigkeitsdatum. Die MNB aktualisiert die Tabelle
  am ersten Arbeitstag jedes Monats.
- VIBER (Großzahlungssystem): „S“ = Filiale darf senden, „R“ = darf empfangen.
"""

from __future__ import annotations

import datetime as dt
import re

from kern import SCHLUESSEL, Stand, herunterladen, leer
from laender._xlsx import xlsx_lesen

CODE = "HU"
NAME = "Ungarn"
BLZ_STELLEN = None
URL = "https://www.mnb.hu/letoltes/sht.xlsx"
SEITE = "https://www.mnb.hu/en/payments/mnb-as-payment-authority/routing-table"
QUELLE = {
    "name": "Magyar Nemzeti Bank – Rövid irányítókód-tábla",
    "kurz": "MNB",
    "url": SEITE,
    "bedingungen": "https://www.mnb.hu/en/the-central-bank/practical-issues/disclaimer",
    # Bedingungen: „may be freely distributed, without changing the content, subject to specifying the source“
    "hinweis": "Forrás: Magyar Nemzeti Bank – Rövid irányítókód-tábla. Inhalt unverändert übernommen, nur umformatiert "
               "(Adresse in PLZ, Ort und Straße aufgeteilt); die Originaldatei der MNB liegt unverändert bei.",
}
ORIGINAL = "original-mnb.xlsx"
SPALTEN = ["Bankleitzahl", "BIC", "Bankenname", "Adresse", "Bankcode", "VIBER senden", "VIBER empfangen"]
_KOPF = {"Branch office code": "Bankleitzahl", "BIC code": "BIC", "Name of the branch office": "Bankenname",
         "Address of the branch office": "Adresse", "Branch office may send VIBER items": "VIBER senden",
         "Branch office may receive VIBER items": "VIBER empfangen"}
def laden(args, alte_meta: dict) -> Stand:
    roh = args.input[0].read_bytes() if args.input else herunterladen(URL)
    blatt, zeilen = xlsx_lesen(roh)
    if not zeilen:
        raise RuntimeError("MNB-Tabelle ist leer")
    kopf = zeilen[0]
    fehlend = [k for k in _KOPF if k not in kopf]
    if fehlend:
        raise RuntimeError(f"Spalten fehlen in der MNB-Tabelle: {fehlend}")
    pos = {ziel: kopf.index(quelle) for quelle, ziel in _KOPF.items()}
    banken = []
    for z in zeilen[1:]:
        wert = lambda k: z[pos[k]] if pos[k] < len(z) else ""
        blz = wert("Bankleitzahl")
        if not blz:
            continue
        banken.append({
            "Bankleitzahl": blz, "BIC": wert("BIC"), "Bankenname": wert("Bankenname"), "Adresse": wert("Adresse"),
            "Bankcode": blz[:3],
            "VIBER senden": "ja" if wert("VIBER senden").upper() == "S" else "nein",
            "VIBER empfangen": "ja" if wert("VIBER empfangen").upper() == "R" else "nein",
        })
    banken.sort(key=lambda z: z[SCHLUESSEL])
    m = re.search(r"(\d{4})(\d{2})(\d{2})", blatt)
    ab = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat() if m else args.today.isoformat()
    print(f"[{CODE}] MNB-Tabelle {blatt}: {len(banken)} Filialcodes, {len({z['Bankcode'] for z in banken})} Bankcodes")
    meta = {"Blatt": blatt, "ValidFrom": ab, "Quelle": URL}
    datum = ab if alte_meta.get("ValidFrom") != ab else args.today.isoformat()
    return Stand(spalten=SPALTEN, banken=banken, datum=datum, meta=meta, dateien={ORIGINAL: roh})


def _adresse(text: str | None) -> dict:
    """„1139 Budapest, Váci út 71.“ -> PLZ, Ort, Straße."""
    text = (text or "").strip()
    m = re.match(r"^(\d{4})\s+([^,]+?)\s*,\s*(.+)$", text)
    if m:
        return {"strasse": m.group(3), "plz": m.group(1), "ort": m.group(2)}
    return {"strasse": leer(text), "plz": None, "ort": None}


def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    return {
        "land": CODE,
        "bankleitzahl": leer(z.get("Bankleitzahl")),
        "bic": leer(z.get("BIC")),
        "name": leer(z.get("Bankenname")),
        "status": None,
        "entfernt_am": None,
        "bankcode": leer(z.get("Bankcode")),
        "adresse": _adresse(z.get("Adresse")),
        "viber_senden": z.get("VIBER senden") == "ja",
        "viber_empfangen": z.get("VIBER empfangen") == "ja",
        "gueltig_ab": meta.get("ValidFrom"),
    }


WEB = {
    "suche_platzhalter": "Filialcode (8-stellig), BIC, Name oder Ort …",
    "suche": ["bankleitzahl", "bic", "name", "adresse.plz", "adresse.ort", "adresse.strasse"],
    "filter": [],
    "spalte5": {"titel": "Bankcode", "feld": "bankcode"},
    "aenderung_name": "Bankenname",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Die MNB veröffentlicht die Tabelle am ersten Arbeitstag jedes Monats. Änderungen stehen "
                           "unter dem Tag, ab dem sie gelten. Jede Zeile ist eine Filiale mit eigenem achtstelligem Code.",
    "details": [
        ["Filialcode (Bankleitzahl)", "bankleitzahl", "kopieren"], ["Bankcode", "bankcode"],
        ["BIC", "bic", "kopieren"], ["Adresse", "adresse", "adresse"],
        ["VIBER senden", "viber_senden", "ja:ja – darf Großzahlungen über VIBER senden"],
        ["VIBER empfangen", "viber_empfangen", "ja:ja – darf Großzahlungen über VIBER empfangen"],
    ],
}


def stand_text(meta: dict) -> str:
    if not meta.get("ValidFrom"):
        return ""
    return f"MNB-Tabelle gültig ab {'.'.join(reversed(meta['ValidFrom'].split('-')))}"
