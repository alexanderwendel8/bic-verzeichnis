"""Slowenien – Seznam identifikacijskih oznak ponudnikov plačilnih storitev der Banka Slovenije.

- Angeboten wird nur eine Textdatei mit Semikolons (Windows-1250), kein XML oder JSON.
- Die nationale Kennung ist fünfstellig und steht in der IBAN an den Stellen 5–9; die ersten zwei
  Stellen bezeichnen das Institut, die übrigen drei seine Einheit (daher viele Einträge je Bank).
- Die Banka Slovenije aktualisiert die Liste laufend (spätestens am nächsten Arbeitstag nach
  einer Meldung). Doppelte Zeilen in der Quelle werden nur einmal übernommen.
"""

from __future__ import annotations

import csv
import io

from kern import SCHLUESSEL, Stand, herunterladen, leer

CODE = "SI"
NAME = "Slowenien"
BLZ_STELLEN = None
URL = "https://www.bsi.si/sl/d/seznam-identifikacijskih-oznak-pps"
QUELLE = {
    "name": "Banka Slovenije – Seznam identifikacijskih oznak PPS",
    "kurz": "Banka Slovenije",
    "url": URL,
    "bedingungen": URL,
}
SPALTEN = ["Bankleitzahl", "BIC", "Bankenname", "Straße", "PLZ", "Ort"]
_KOPF = {"NACIONALNA IDENTIFIKACIJSKA OZNAKA": "Bankleitzahl", "BIC11": "BIC", "NAZIV": "Bankenname",
         "NASLOV": "Straße", "POŠTNA ŠTEVILKA": "PLZ", "KRAJ": "Ort"}


def laden(args, alte_meta: dict) -> Stand:
    roh = args.input[0].read_bytes() if args.input else herunterladen(URL)
    reader = csv.DictReader(io.StringIO(roh.decode("cp1250")), delimiter=";")
    fehlend = [k for k in _KOPF if k not in (reader.fieldnames or [])]
    if fehlend:
        raise RuntimeError(f"Spalten fehlen in der Liste der Banka Slovenije: {fehlend}")
    banken: dict[str, dict] = {}
    doppelt = 0
    for r in reader:
        z = {ziel: (r.get(quelle) or "").strip() for quelle, ziel in _KOPF.items()}
        if not z[SCHLUESSEL]:
            continue
        if z[SCHLUESSEL] in banken:
            doppelt += 1
            continue
        banken[z[SCHLUESSEL]] = z
    print(f"[{CODE}] Banka Slovenije: {len(banken)} Kennungen" + (f" ({doppelt} doppelte Zeilen übersprungen)" if doppelt else ""))
    return Stand(spalten=SPALTEN, banken=sorted(banken.values(), key=lambda z: z[SCHLUESSEL]),
                 datum=args.today.isoformat())


def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    return {
        "land": CODE,
        "bankleitzahl": leer(z.get("Bankleitzahl")),
        "bic": leer(z.get("BIC")),
        "name": leer(z.get("Bankenname")),
        "status": None,
        "entfernt_am": None,
        "institut": (z.get("Bankleitzahl") or "")[:2] or None,
        "adresse": {"strasse": leer(z.get("Straße")), "plz": leer(z.get("PLZ")), "ort": leer(z.get("Ort"))},
    }


WEB = {
    "suche_platzhalter": "Kennung (5-stellig), BIC, Bankname oder Ort …",
    "suche": ["bankleitzahl", "bic", "name", "adresse.plz", "adresse.ort", "adresse.strasse"],
    "filter": [{"feld": "name", "alle": "Alle Institute"}],
    "spalte5": {"titel": "Institut", "feld": "institut"},
    "aenderung_name": "Bankenname",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Täglicher Vergleich mit dem Vortag. Kennungen, die aus der Liste der Banka Slovenije "
                           "verschwinden, bleiben hier mit ihrem letzten Stand erhalten.",
    "details": [
        ["Kennung (Bankleitzahl)", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"],
        ["Institut (Stellen 1–2)", "institut"], ["Adresse", "adresse", "adresse"],
    ],
}


def stand_text(meta: dict) -> str:
    return ""
