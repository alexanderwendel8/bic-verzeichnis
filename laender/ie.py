"""Irland – abgeleitet aus Institutslisten der Europäischen Zentralbank (EZB) und der GLEIF-Zuordnung.

- Keine Behörde veröffentlicht die irischen Bankcodes oder die National Sort Codes (NSC); die Sort-Code-
  Datenbank des Bankenverbands BPFI ist „All rights reserved“, automatische Abfragen sind dort verboten.
- Der irische Bankcode (IBAN-Stellen 5–8) sind die ersten vier Buchstaben des BIC. Er wird wie in den
  Niederlanden abgeleitet (laender/_ezb.py): Institute aus der MFI- und PSRI-Liste der EZB → LEI → irische
  BICs aus der GLEIF-Zuordnung → Bankcode = BIC[0:4]. Die sechsstelligen Sort Codes (IBAN-Stellen 9–14)
  sind in keiner offenen Quelle enthalten und fehlen.
- Die MFI-Liste enthält auch die irischen Credit Unions; viele haben einen eigenen BIC (…IE21).
- Ergebnis ist **nicht amtlich und unvollständig**.
- Bedingungen der EZB: freie Nutzung, genaue Wiedergabe, EZB als Quelle nennen, Änderungen kennzeichnen.
  Für BICs und Bankcodes gilt der SWIFT-Hinweis der GLEIF-Zuordnung.
"""

from __future__ import annotations

from kern import Stand
from laender import _ezb, _gleif

CODE = "IE"
NAME = "Irland"
BLZ_STELLEN = None
SEITE = _ezb.SEITE
QUELLE = {
    "name": "Europäische Zentralbank – Listen der Finanzinstitute (MFI, PSRI); Bankcode und BIC abgeleitet über GLEIF",
    "kurz": "EZB",
    "url": SEITE,
    "bedingungen": _ezb.BEDINGUNGEN,
    "hinweis": "Source: European Central Bank – lists of monetary financial institutions (MFI) and payment statistics "
               "relevant institutions (PSRI). Geändert: auf irische Institute gefiltert; Bankcode und BIC nicht von der "
               "EZB, sondern abgeleitet aus der BIC/LEI-Zuordnung von GLEIF (Bankcode = erste vier Zeichen des BIC). "
               "Nicht amtlich und unvollständig, ohne Sort Codes.",
}
ORIGINAL_URL = SEITE
SPALTEN = _ezb.SPALTEN


def laden(args, alte_meta: dict) -> Stand:
    liste, info = _ezb.institute(CODE)
    nach_lei, tabelle, gleif_datei = _ezb.bics_nach_lei(CODE)
    banken = _ezb.codes_aus_bic(CODE, liste, nach_lei)
    print(f"[{CODE}] EZB {info['MFI-Datei']}: {info['MFI']} MFIs, {info['PSRI-Liste']}: {info['PSRI']} Zahlungsdienstleister; "
          f"GLEIF {gleif_datei}: {len(banken)} abgeleitete Bankcodes")
    meta = {"Quelle": SEITE, "PSRI-Liste": info["PSRI-Liste"], "GLEIF-Tabelle": tabelle}
    return Stand(spalten=SPALTEN, banken=banken, datum=args.today.isoformat(), meta=meta,
                 dateien={"HINWEIS-BIC.txt": _gleif.hinweis_datei(tabelle, QUELLE["hinweis"])})


# ---------------------------------------------------------------- API

def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    return _ezb.api_eintrag(CODE, z)


# ---------------------------------------------------------------- Webseite

WEB = _ezb.web(
    "Bankcode (4 Buchstaben), BIC, Name oder Ort …",
    "Abgeleitet, nicht amtlich: Bankcode = erste vier Zeichen des BIC (GLEIF) der Institute aus den Listen der EZB. "
    "Unvollständig und ohne Sort Codes.")


def stand_text(meta: dict) -> str:
    return "abgeleitet aus EZB-Listen und GLEIF – nicht amtlich, unvollständig"


def zusatz_hinweis(meta: dict) -> str:
    return _gleif.swift_hinweis(meta.get("GLEIF-Tabelle"))
