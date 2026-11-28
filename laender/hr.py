"""Kroatien – Vodeći brojevi pružatelja platnih usluga der Kroatischen Nationalbank (HNB).

- Angeboten wird nur eine Excel-Datei (.xlsx) mit fester Adresse; dieselbe Tabelle steht als HTML auf der Seite.
  Kein XML, JSON oder CSV. Gelesen ohne Zusatzbibliothek (laender/_xlsx.py).
- Die Bankleitzahl (vodeći broj, VBB) ist siebenstellig und steht in der IBAN an den Stellen 5–11; die letzte
  Stelle ist eine Prüfziffer.
- BICs stehen mit Leerzeichen in der Datei („HAAB HR 22“) und werden ohne Leerzeichen abgelegt.
- Die HNB aktualisiert die Liste sofort bei jeder Änderung; ein Datum steht nicht in der Datei, sondern nur auf
  der Seite („Ažurirano: 27.3.2025“).
- Bedingungen der HNB: Kopieren erlaubt, wenn die HNB als Quelle genannt wird; der Inhalt darf nicht verändert
  werden. Die Originaldatei liegt deshalb unverändert bei.
"""

from __future__ import annotations

import re

from kern import SCHLUESSEL, Stand, herunterladen, leer
from laender._xlsx import xlsx_lesen

CODE = "HR"
NAME = "Kroatien"
BLZ_STELLEN = None
URL = "https://www.hnb.hr/documents/d/guest/h-vodeci-brojevi-pruzatelja-platnih-usluga"
SEITE = "https://www.hnb.hr/temeljne-funkcije/platni-promet/vodeci-brojevi-pruzatelja-platnih-usluga"
QUELLE = {
    "name": "Hrvatska narodna banka – Vodeći brojevi pružatelja platnih usluga",
    "kurz": "HNB",
    "url": SEITE,
    # „The Croatian National Bank permits copying material from its web site under the condition that the CNB is
    # stated as the source. … It is not permitted to amend the contents of the material.“
    "bedingungen": "https://www.hnb.hr/en/terms-of-use",
    "hinweis": "Izvor: Hrvatska narodna banka – Vodeći brojevi pružatelja platnih usluga. Inhalt unverändert übernommen, "
               "nur umformatiert (BIC ohne Leerzeichen); die Originaldatei der HNB liegt unverändert bei.",
}
ORIGINAL = "original-hnb.xlsx"
SPALTEN = ["Bankleitzahl", "BIC", "Bankenname"]


def _sitz(name: str) -> tuple[str | None, str | None]:
    """„ADDIKO BANK d.d. Zagreb“ -> (Rechtsform „d.d.“, Sitz „Zagreb“); die HNB nennt beides im Namen."""
    m = re.search(r"\b(d\.d\.|d\.o\.o\.|AG)(?:\s+(.+))?$", name)
    if not m:
        return None, None
    return m.group(1), (m.group(2) or "").strip() or None


def _text(wert: str) -> str:
    return re.sub(r"\s+", " ", (wert or "").replace("\xa0", " ")).strip()


def laden(args, alte_meta: dict) -> Stand:
    roh = args.input[0].read_bytes() if args.input else herunterladen(URL)
    _, zeilen = xlsx_lesen(roh)
    try:
        k = next(i for i, z in enumerate(zeilen) if any(_text(c) == "Vodeći broj" for c in z))
    except StopIteration:
        raise RuntimeError("Kopfzeile in der HNB-Liste nicht gefunden – Format geändert?")
    kopf = [_text(c) for c in zeilen[k]]
    p_name = next(i for i, c in enumerate(kopf) if c.startswith("Naziv"))
    p_blz = kopf.index("Vodeći broj")
    p_bic = next(i for i, c in enumerate(kopf) if c.startswith("SWIFT"))

    banken = {}
    for z in zeilen[k + 1:]:
        w = lambda i: _text(z[i]) if i < len(z) else ""
        blz = w(p_blz)
        if not blz:
            continue
        if not re.fullmatch(r"\d{7}", blz):
            raise RuntimeError(f"unerwarteter vodeći broj in der HNB-Liste: {blz!r}")
        if blz in banken:
            raise RuntimeError(f"vodeći broj {blz} mehrfach in der HNB-Liste")
        bic = w(p_bic).replace(" ", "").upper()
        if bic and not re.fullmatch(r"[A-Z0-9]{8}([A-Z0-9]{3})?", bic):
            raise RuntimeError(f"unerwarteter BIC in der HNB-Liste: {bic!r}")
        banken[blz] = {"Bankleitzahl": blz, "BIC": bic, "Bankenname": w(p_name)}
    if not banken:
        raise RuntimeError("keine Einträge in der HNB-Liste")
    print(f"[{CODE}] HNB-Liste: {len(banken)} Codes, {sum(1 for z in banken.values() if z['BIC'])} mit BIC")
    return Stand(spalten=SPALTEN, banken=sorted(banken.values(), key=lambda z: z[SCHLUESSEL]),
                 datum=args.today.isoformat(), meta={"Quelle": URL}, dateien={ORIGINAL: roh})


# ---------------------------------------------------------------- API

def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    g = lambda s: leer(z.get(s))
    rechtsform, sitz = _sitz(z.get("Bankenname") or "")
    return {
        "land": CODE,
        "bankleitzahl": g("Bankleitzahl"),
        "bic": g("BIC"),
        "name": g("Bankenname"),
        "status": None,
        "entfernt_am": None,
        "rechtsform": rechtsform,
        "adresse": {"ort": sitz},
    }


# ---------------------------------------------------------------- Webseite

WEB = {
    "suche_platzhalter": "Vodeći broj (7-stellig), BIC oder Name …",
    "suche": ["bankleitzahl", "bic", "name", "adresse.ort"],
    "filter": [],
    "spalte5": {"titel": "Rechtsform", "feld": "rechtsform"},
    "aenderung_name": "Bankenname",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Die HNB aktualisiert die Liste sofort bei jeder Änderung. Täglicher Vergleich mit dem Vortag.",
    "details": [["Vodeći broj (Bankleitzahl)", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"],
                ["Rechtsform", "rechtsform"], ["Sitz", "adresse.ort"]],
}


def stand_text(meta: dict) -> str:
    return ""
