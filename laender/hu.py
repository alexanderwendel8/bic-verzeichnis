"""Ungarn – Rövid irányítókód-tábla (Short Routing Table) der Ungarischen Nationalbank (MNB).

- Angeboten wird nur eine Excel-Datei (.xlsx), kein XML, JSON oder CSV. Eine .xlsx besteht intern
  aus XML; sie wird hier ohne Zusatzbibliothek mit zipfile und ElementTree gelesen.
- Jede Zeile ist ein achtstelliger Filialcode (pénzforgalmi irányítókód): 3 Stellen Bankcode,
  4 Stellen Filiale, 1 Prüfziffer. Genau diese 8 Stellen stehen in der IBAN an den Stellen 5–12,
  daher dienen sie hier als Bankleitzahl.
- Der Blattname (z. B. „SHT20261101“) nennt das Gültigkeitsdatum. Die MNB aktualisiert die Tabelle
  am ersten Arbeitstag jedes Monats.
- VIBER (Großzahlungssystem): „S“ = Filiale darf senden, „R“ = darf empfangen.
"""

from __future__ import annotations

import datetime as dt
import io
import re
import zipfile
import xml.etree.ElementTree as ET

from kern import SCHLUESSEL, Stand, herunterladen, leer

CODE = "HU"
NAME = "Ungarn"
BLZ_STELLEN = None
URL = "https://www.mnb.hu/letoltes/sht.xlsx"
SEITE = "https://www.mnb.hu/en/payments/mnb-as-payment-authority/routing-table"
QUELLE = {
    "name": "Magyar Nemzeti Bank – Rövid irányítókód-tábla",
    "kurz": "MNB",
    "url": SEITE,
    "bedingungen": SEITE,
}
SPALTEN = ["Bankleitzahl", "BIC", "Bankenname", "Adresse", "Bankcode", "VIBER senden", "VIBER empfangen"]
_KOPF = {"Branch office code": "Bankleitzahl", "BIC code": "BIC", "Name of the branch office": "Bankenname",
         "Address of the branch office": "Adresse", "Branch office may send VIBER items": "VIBER senden",
         "Branch office may receive VIBER items": "VIBER empfangen"}
_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _xlsx_lesen(roh: bytes) -> tuple[str, list[list[str]]]:
    """-> (Name des ersten Blatts, Zeilen als Listen von Zellwerten)."""
    z = zipfile.ZipFile(io.BytesIO(roh))
    texte = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(_NS + "si"):
            texte.append("".join(t.text or "" for t in si.iter(_NS + "t")))
    blatt = ET.fromstring(z.read("xl/workbook.xml")).find(_NS + "sheets")[0].get("name", "")
    zeilen = []
    for r in ET.fromstring(z.read("xl/worksheets/sheet1.xml")).iter(_NS + "row"):
        zeile: dict[int, str] = {}
        for c in r.findall(_NS + "c"):
            spalte = re.match(r"[A-Z]+", c.get("r", "A")).group()
            idx = 0
            for ch in spalte:
                idx = idx * 26 + ord(ch) - 64
            typ, v = c.get("t"), c.find(_NS + "v")
            if typ == "inlineStr":
                wert = "".join(t.text or "" for t in c.iter(_NS + "t"))
            elif v is None:
                wert = ""
            else:
                wert = texte[int(v.text)] if typ == "s" else (v.text or "")
            zeile[idx - 1] = wert.strip()
        if zeile:
            zeilen.append([zeile.get(i, "") for i in range(max(zeile) + 1)])
    return blatt, zeilen


def laden(args, alte_meta: dict) -> Stand:
    roh = args.input[0].read_bytes() if args.input else herunterladen(URL)
    blatt, zeilen = _xlsx_lesen(roh)
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
    return Stand(spalten=SPALTEN, banken=banken, datum=datum, meta=meta)


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
