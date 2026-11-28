"""Zypern – Bankcodes und BICs der Central Bank of Cyprus (CBC).

- Angeboten wird eine Excel-Datei (.xlsx), deren Name Monat und Jahr enthält („…_updated_September_2026.xlsx“);
  der Link wird jedes Mal von der IBAN-Seite gelesen. Kein XML, JSON oder CSV. Gelesen ohne Zusatzbibliothek.
- Der Bankcode ist dreistellig (IBAN-Stellen 5–7). Die Datei enthält zwei Tabellen: Kreditinstitute (001–129)
  und E-Geld-Institute (9xx). Einige E-Geld-Institute haben zwei BICs (zweiter BIC in einer Folgezeile).
- Daneben bietet die CBC ein Register der Filialcodes im alten .xls-Format, das sich ohne Zusatzbibliothek
  nicht lesen lässt; es wird nicht verwendet.
- Bedingungen der CBC: freie Nutzung, genaue Wiedergabe, CBC als Quelle nennen, Änderungen ausdrücklich
  kennzeichnen. Die Originaldatei liegt unverändert bei.
"""

from __future__ import annotations

import html
import re
import urllib.parse

from kern import SCHLUESSEL, Stand, herunterladen, leer
from laender._xlsx import xlsx_lesen

CODE = "CY"
NAME = "Zypern"
BLZ_STELLEN = None
SEITE = "https://www.centralbank.cy/en/financial-market-infrastructures-payments/international-bank-account-number-iban"
QUELLE = {
    "name": "Central Bank of Cyprus – Bank identifiers used in IBAN and BICs",
    "kurz": "Central Bank of Cyprus",
    "url": SEITE,
    # „users may make free use of information obtained directly from the CBC's internet site … must be accurate,
    # and the CBC must be cited as the source … If the information is modified by the user, this must be stated“
    "bedingungen": "https://www.centralbank.cy/en/terms-of-use",
    "hinweis": "Source: Central Bank of Cyprus – Bank identifiers used in IBAN and BICs. Geändert: zwei Tabellen "
               "zusammengeführt, je Code eine Zeile, weitere BICs zusammengefasst; die Originaldatei der CBC liegt "
               "unverändert bei.",
}
ORIGINAL = "original-cbc.xlsx"
SPALTEN = ["Bankleitzahl", "BIC", "Weitere BICs", "Bankenname", "Art"]
_ARTEN = {"Credit Institution": "Kreditinstitut", "Electronic Money Institution": "E-Geld-Institut"}


def _xlsx_url() -> tuple[str, str]:
    seite = herunterladen(SEITE).decode("utf-8", "replace")
    links = re.findall(r'href="([^"]*FMIP/IBAN/[^"]*\.xlsx)"', seite)
    if not links:
        raise RuntimeError("kein Link zur BIC-Liste auf der IBAN-Seite der CBC gefunden – Seite geändert?")
    url = urllib.parse.urljoin(SEITE, html.unescape(links[0]))
    return url, urllib.parse.unquote(url.rsplit("/", 1)[-1])


def _text(wert: str) -> str:
    return re.sub(r"\s+", " ", (wert or "").replace("\xa0", " ")).strip()


def laden(args, alte_meta: dict) -> Stand:
    if args.input:
        roh, datei = args.input[0].read_bytes(), args.input[0].name
    else:
        url, datei = _xlsx_url()
        roh = herunterladen(url)
    _, zeilen = xlsx_lesen(roh)
    banken: dict[str, dict] = {}
    art, letzter = None, None
    for z in zeilen:
        z = [_text(c) for c in z] + ["", "", "", ""]
        if z[0] == "#":
            art = _ARTEN.get(z[1])
            if art is None:
                raise RuntimeError(f"unbekannte Tabelle in der CBC-Liste: {z[1]!r}")
            continue
        bic = z[3].replace(" ", "").upper()
        if art and re.fullmatch(r"\d{3}", z[2]):
            if z[2] in banken:
                raise RuntimeError(f"Bankcode {z[2]} mehrfach in der CBC-Liste")
            letzter = banken[z[2]] = {"Bankleitzahl": z[2], "BIC": bic, "Weitere BICs": "", "Bankenname": z[1], "Art": art}
        elif art and letzter and not z[0] and not z[2] and re.fullmatch(r"[A-Z0-9]{8}([A-Z0-9]{3})?", bic):
            letzter["Weitere BICs"] = " ".join(filter(None, [letzter["Weitere BICs"], bic]))
        else:
            letzter = None
    if not banken:
        raise RuntimeError("keine Bankcodes in der CBC-Liste gefunden – Format geändert?")
    for z in banken.values():
        if z["BIC"] and not re.fullmatch(r"[A-Z0-9]{8}([A-Z0-9]{3})?", z["BIC"]):
            raise RuntimeError(f"unerwarteter BIC in der CBC-Liste: {z['BIC']!r}")
    m = re.search(r"updated_([A-Za-z]+)_(\d{4})", datei)
    stand = f"{m.group(1)} {m.group(2)}" if m else ""
    print(f"[{CODE}] CBC-Liste {datei}: {len(banken)} Bankcodes, {sum(1 for z in banken.values() if z['BIC'])} mit BIC")
    return Stand(spalten=SPALTEN, banken=sorted(banken.values(), key=lambda z: z[SCHLUESSEL]),
                 datum=args.today.isoformat(), meta={"Quelle": SEITE, "Stand": stand}, dateien={ORIGINAL: roh})


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
        "weitere_bics": (z.get("Weitere BICs") or "").split(),
        "art": g("Art"),
    }


# ---------------------------------------------------------------- Webseite

WEB = {
    "suche_platzhalter": "Bankcode (3-stellig), BIC oder Name …",
    "suche": ["bankleitzahl", "bic", "name"],
    "suche_listen": ["weitere_bics"],
    "filter": [{"feld": "art", "alle": "Alle Arten"}],
    "spalte5": {"titel": "Art", "feld": "art"},
    "aenderung_name": "Bankenname",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Die Central Bank of Cyprus aktualisiert die Liste bei jeder Änderung. Täglicher Vergleich "
                           "mit dem Vortag. Eine Bank kann mehrere Codes haben (z. B. nach Übernahmen).",
    "details": [["Bankcode", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"],
                ["Weitere BICs", "weitere_bics", "liste"], ["Art", "art"]],
}


def stand_text(meta: dict) -> str:
    return f"CBC-Liste Stand {meta['Stand']}" if meta.get("Stand") else ""
