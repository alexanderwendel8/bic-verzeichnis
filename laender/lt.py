"""Litauen – Finansų įstaigų kodai (FIK) der Litauischen Zentralbank (Lietuvos bankas).

- Angeboten werden CSV, XLSX und PDF (je litauisch und englisch), kein XML oder JSON. Verwendet wird die
  englische CSV: Windows-1257, Semikolons, eine Zeile je Code, leere Zusatzspalten am Ende.
- Der Code (National ID) ist fünfstellig und steht in der IBAN an den Stellen 5–9. Mehrere Codes können
  denselben BIC haben (z. B. frühere Codes übernommener Banken).
- Der Dateiname enthält das Datum („FIK_KODAI_20261105-en.csv“). Die Übersichtsseite der Lietuvos bankas
  ist für Programme gesperrt (Browser-Prüfung), die Dateien selbst nicht. Das Skript probiert deshalb die
  Dateinamen der letzten Tage durch (nur HEAD-Anfragen) und nimmt die neueste Datei; gefunden wird eine
  neue Liste also innerhalb von SUCHTAGE Tagen nach ihrem Datum. Die zuletzt gefundene Datei steht in
  meta.json.
- Bedingungen der Lietuvos bankas: bei Nutzung der Informationen die Lietuvos bankas als Quelle nennen.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import re
import urllib.error
import urllib.request

from kern import SCHLUESSEL, Stand, herunterladen, leer

CODE = "LT"
NAME = "Litauen"
BLZ_STELLEN = None
SEITE = "https://www.lb.lt/en/iban-and-financial-institution-codes"
DATEI = "https://www.lb.lt/uploads/documents/files/FIK_KODAI_{datum}-en.csv"
ERSTE_DATEI = "20261105"  # Ausgangspunkt, falls noch kein Stand vorhanden ist
SUCHTAGE = 21
QUELLE = {
    "name": "Lietuvos bankas – Finansų įstaigų kodai (Financial institution codes)",
    "kurz": "Lietuvos bankas",
    "url": SEITE,
    # Informacijos naudojimo sąlygos: „prašome kaip šaltinį nurodyti Lietuvos banką“
    "bedingungen": "https://www.lb.lt/lt/informacijos-naudojimo-salygos",
    "hinweis": "Šaltinis: Lietuvos bankas – Finansų įstaigų kodai (Source: Bank of Lithuania – Financial institution "
               "codes). Inhalt unverändert übernommen, nur umformatiert; die Originaldatei liegt unverändert bei.",
}
ORIGINAL = "original-lb.csv"
SPALTEN = ["Bankleitzahl", "BIC", "Bankenname", "Filiale", "Registernummer", "Straße", "PLZ", "Ort", "Lage", "Land"]
_KOPF = {"National ID": "Bankleitzahl", "BIC Code": "BIC", "Financial Institution Name": "Bankenname",
         "Branch Name": "Filiale", "Legal Entity Code": "Registernummer", "Branch Address": "Straße",
         "Zip Code": "PLZ", "City": "Ort", "Location": "Lage", "Country": "Land"}


def _gibt_es(url: str) -> bool:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "bic-verzeichnis-update"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status == 200
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        raise


def _neueste_datei(heute: dt.date, bekannt: str | None) -> str:
    """-> JJJJMMTT der neuesten Datei: die letzten SUCHTAGE Tage rückwärts, sonst die zuletzt bekannte."""
    bekannt = bekannt or ERSTE_DATEI
    for i in range(SUCHTAGE + 1):
        tag = (heute - dt.timedelta(days=i)).strftime("%Y%m%d")
        if tag <= bekannt:
            break
        if _gibt_es(DATEI.format(datum=tag)):
            return tag
    return bekannt


def _text(wert: str) -> str:
    return re.sub(r"\s+", " ", (wert or "").replace("\xa0", " ")).strip()


def laden(args, alte_meta: dict) -> Stand:
    if args.input:
        roh = args.input[0].read_bytes()
        m = re.search(r"(\d{8})", args.input[0].name)
        datei = m.group(1) if m else args.today.strftime("%Y%m%d")
    else:
        datei = _neueste_datei(args.today, alte_meta.get("Datei"))
        roh = herunterladen(DATEI.format(datum=datei))
    zeilen = list(csv.reader(io.StringIO(roh.decode("cp1257")), delimiter=";"))
    try:
        k = next(i for i, z in enumerate(zeilen) if z and z[0].strip() == "National ID")
    except StopIteration:
        raise RuntimeError("Kopfzeile in der FIK-Liste nicht gefunden – Format geändert?")
    kopf = [c.strip() for c in zeilen[k]]
    fehlend = [s for s in _KOPF if s not in kopf]
    if fehlend:
        raise RuntimeError(f"Spalten fehlen in der FIK-Liste: {fehlend}")
    pos = {ziel: kopf.index(quelle) for quelle, ziel in _KOPF.items()}

    banken = {}
    for z in zeilen[k + 1:]:
        e = {s: _text(z[i]) if i < len(z) else "" for s, i in pos.items()}
        if not e["Bankleitzahl"]:
            continue
        if not re.fullmatch(r"\d{5}", e["Bankleitzahl"]):
            raise RuntimeError(f"unerwarteter Code in der FIK-Liste: {e['Bankleitzahl']!r}")
        if e["Bankleitzahl"] in banken:
            raise RuntimeError(f"Code {e['Bankleitzahl']} mehrfach in der FIK-Liste")
        e["BIC"] = e["BIC"].replace(" ", "").upper()
        banken[e["Bankleitzahl"]] = e
    ab = f"{datei[:4]}-{datei[4:6]}-{datei[6:]}"
    print(f"[{CODE}] FIK-Liste vom {ab}: {len(banken)} Codes, {sum(1 for z in banken.values() if z['BIC'])} mit BIC")
    meta = {"Datei": datei, "ValidFrom": ab, "Quelle": DATEI.format(datum=datei)}
    datum = ab if alte_meta.get("Datei") != datei else args.today.isoformat()
    return Stand(spalten=SPALTEN, banken=sorted(banken.values(), key=lambda z: z[SCHLUESSEL]), datum=datum,
                 meta=meta, dateien={ORIGINAL: roh})


# ---------------------------------------------------------------- API

def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    g = lambda s: leer(z.get(s))
    return {
        "land": CODE,
        "bankleitzahl": g("Bankleitzahl"),
        "bic": g("BIC"),
        "name": g("Bankenname"),
        "status": None,
        "entfernt_am": None,
        "filiale": g("Filiale"),
        "registernummer": g("Registernummer"),
        "adresse": {"strasse": g("Straße"), "plz": g("PLZ"), "ort": g("Ort"), "lage": g("Lage"), "land": g("Land")},
        "gueltig_ab": meta.get("ValidFrom"),
    }


# ---------------------------------------------------------------- Webseite

WEB = {
    "suche_platzhalter": "Code (5-stellig), BIC, Name oder Ort …",
    "suche": ["bankleitzahl", "bic", "name", "filiale", "adresse.ort", "adresse.plz", "registernummer"],
    "filter": [],
    "spalte5": {"titel": "Filiale", "feld": "filiale"},
    "aenderung_name": "Bankenname",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Die Lietuvos bankas veröffentlicht die Liste neu, sobald sich etwas ändert. Änderungen "
                           "stehen unter dem Datum der neuen Liste. Mehrere Codes können denselben BIC haben.",
    "details": [
        ["Code (Bankleitzahl)", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"], ["Filiale", "filiale"],
        ["Registernummer", "registernummer"], ["Adresse", "adresse", "adresse"], ["Land", "adresse.land"],
        ["Liste gültig ab", "gueltig_ab", "datum"],
    ],
}


def stand_text(meta: dict) -> str:
    if not meta.get("ValidFrom"):
        return ""
    return f"FIK-Liste vom {'.'.join(reversed(meta['ValidFrom'].split('-')))}"
