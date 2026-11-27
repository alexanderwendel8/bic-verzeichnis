"""Belgien – Liste der Bank-Identifikationscodes der Belgischen Nationalbank (NBB).

- Angeboten werden nur Excel (.xlsx) und PDF, kein XML, JSON oder CSV. Gelesen wird die
  vollständige Liste (je Code eine Zeile) ohne Zusatzbibliothek (laender/_xlsx.py).
- Der Bank-Identifikationscode ist dreistellig und steht in der IBAN an den Stellen 5–7.
  Die Liste enthält alle Codes 000–999; freie („VRIJ“/„LIBRE“) und nicht verfügbare
  („Onbeschikbaar“) Codes werden weggelassen.
- Eine Bank hat oft viele Codes mit demselben BIC. BICs stehen in der Datei mit Leerzeichen
  („GEBA BE BB“) und werden ohne Leerzeichen abgelegt; Platzhalter wie „N/A“ oder „NYA“ = kein BIC.
- Namen gibt es auf Niederländisch, Französisch, Deutsch und Englisch (nicht immer alle).
- Die erste Zeile nennt die Version („Version 01/09/2026“); die NBB aktualisiert die Liste,
  sobald sich etwas ändert. Adressen enthält die Liste nicht.
"""

from __future__ import annotations

import datetime as dt
import re

from kern import SCHLUESSEL, Stand, herunterladen, leer
from laender._xlsx import xlsx_lesen

CODE = "BE"
NAME = "Belgien"
BLZ_STELLEN = None
URL = "https://www.nbb.be/doc/be/be/protocol/full_list_current.xlsx"
SEITE = "https://www.nbb.be/en/payments-and-securities/bank-identification-codes"
QUELLE = {
    "name": "Nationale Bank van België / Banque Nationale de Belgique – Bank-Identifikationscodes",
    "kurz": "NBB",
    "url": SEITE,
    # Bedingungen: „may be distributed or reproduced, provided the integrity and accuracy thereof are maintained
    # and the NBB is acknowledged as the source“
    "bedingungen": "https://www.nbb.be/en/disclaimer-and-legal-information/copyright-and-use-information",
    "hinweis": "Source: National Bank of Belgium (NBB) – Bank identification codes. Inhalt unverändert übernommen, "
               "nur umformatiert (freie Codes weggelassen, BIC ohne Leerzeichen); die Originaldatei der NBB liegt "
               "unverändert bei.",
}
ORIGINAL = "original-nbb.xlsx"
SPALTEN = ["Bankleitzahl", "BIC", "Name (NL)", "Name (FR)", "Name (DE)", "Name (EN)"]
_KOPF = {"T_Identification_Number": "Bankleitzahl", "Biccode": "BIC", "T_Institutions_Dutch": "Name (NL)",
         "T_Institutions_French": "Name (FR)", "T_Institutions_German": "Name (DE)",
         "T_Institutions_English": "Name (EN)"}
_FREI = {"VRIJ", "LIBRE", "ONBESCHIKBAAR", "INDISPONIBLE"}
_KEIN_BIC = {"N/A", "NA", "NAV", "NYA", "-", ""}


def _bic(wert: str) -> str:
    wert = re.sub(r"\s+", "", wert or "").upper()
    return "" if wert in _KEIN_BIC else wert


def laden(args, alte_meta: dict) -> Stand:
    roh = args.input[0].read_bytes() if args.input else herunterladen(URL)
    blatt, zeilen = xlsx_lesen(roh)
    try:
        k = next(i for i, z in enumerate(zeilen) if "T_Identification_Number" in z)
    except StopIteration:
        raise RuntimeError("Kopfzeile in der NBB-Liste nicht gefunden – Format geändert?")
    kopf = zeilen[k]
    fehlend = [s for s in _KOPF if s not in kopf]
    if fehlend:
        raise RuntimeError(f"Spalten fehlen in der NBB-Liste: {fehlend}")
    pos = {ziel: kopf.index(quelle) for quelle, ziel in _KOPF.items()}

    ab = None
    for z in zeilen[:k]:
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", " ".join(z))
        if m:
            ab = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
            break

    banken, frei = [], 0
    for z in zeilen[k + 1:]:
        wert = lambda s: z[pos[s]].strip() if pos[s] < len(z) else ""
        blz = wert("Bankleitzahl")
        if not re.fullmatch(r"\d{3}", blz):
            continue
        namen = [wert(s) for s in SPALTEN[2:]]
        if not any(namen) or {n.upper() for n in namen if n} & _FREI:
            frei += 1
            continue
        e = {s: wert(s) for s in SPALTEN}
        e["BIC"] = _bic(wert("BIC"))
        banken.append(e)
    banken.sort(key=lambda z: z[SCHLUESSEL])
    ab = ab or args.today.isoformat()
    print(f"[{CODE}] NBB-Liste Version {ab}: {len(banken)} vergebene Codes, {frei} frei/nicht verfügbar")
    meta = {"Version": ab, "Quelle": URL}
    datum = ab if alte_meta.get("Version") != ab else args.today.isoformat()
    return Stand(spalten=SPALTEN, banken=banken, datum=datum, meta=meta, dateien={ORIGINAL: roh})


# ---------------------------------------------------------------- API

def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    g = lambda s: leer(z.get(s))
    namen = {"nl": g("Name (NL)"), "fr": g("Name (FR)"), "de": g("Name (DE)"), "en": g("Name (EN)")}
    return {
        "land": CODE,
        "bankleitzahl": g("Bankleitzahl"),
        "bic": g("BIC"),
        "name": next((n for n in namen.values() if n), None),
        "status": None,
        "entfernt_am": None,
        "namen": namen,
        "version": meta.get("Version"),
    }


# ---------------------------------------------------------------- Webseite

WEB = {
    "suche_platzhalter": "Bank-Identifikationscode (3-stellig), BIC oder Bankname …",
    "suche": ["bankleitzahl", "bic", "name", "namen.nl", "namen.fr", "namen.de", "namen.en"],
    "filter": [],
    "spalte5": {"titel": "Name (FR)", "feld": "namen.fr"},
    "aenderung_name": "Name (NL)",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Die NBB aktualisiert die Liste, sobald sich etwas ändert. Änderungen stehen unter dem Tag "
                           "der neuen Version. Eine Bank hat oft mehrere dreistellige Codes mit demselben BIC.",
    "details": [
        ["Bank-Identifikationscode", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"],
        ["Name (Niederländisch)", "namen.nl"], ["Name (Französisch)", "namen.fr"],
        ["Name (Deutsch)", "namen.de"], ["Name (Englisch)", "namen.en"],
        ["Version der Liste", "version", "datum"],
    ],
}


def stand_text(meta: dict) -> str:
    if not meta.get("Version"):
        return ""
    return f"NBB-Liste Version {'.'.join(reversed(meta['Version'].split('-')))}"
