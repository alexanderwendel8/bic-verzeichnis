"""Malta – abgeleitet aus Institutslisten der Europäischen Zentralbank (EZB) und der GLEIF-Zuordnung.

- Die Central Bank of Malta und die Aufsicht MFSA sperren automatische Abrufe ihrer Websites; eine abrufbare
  amtliche Liste der Bankcodes gibt es nicht.
- Der maltesische Bankcode (IBAN-Stellen 5–8) sind die ersten vier Buchstaben des BIC. Er wird wie in den
  Niederlanden abgeleitet (laender/_ezb.py): Institute aus der MFI- und PSRI-Liste der EZB → LEI →
  maltesische BICs aus der GLEIF-Zuordnung → Bankcode = BIC[0:4]. Die fünfstelligen Sort Codes (IBAN-Stellen
  9–13) sind in keiner offenen Quelle enthalten und fehlen.
- Ergebnis ist **nicht amtlich und unvollständig**. Viele maltesische BICs tragen noch alte Namen (z. B. nach
  Umbenennungen); der Name kommt deshalb aus der EZB-Liste, nicht aus dem BIC.
- Bedingungen der EZB: freie Nutzung, genaue Wiedergabe, EZB als Quelle nennen, Änderungen kennzeichnen.
  Für BICs und Bankcodes gilt der SWIFT-Hinweis der GLEIF-Zuordnung.
"""

from __future__ import annotations

from kern import Stand
from laender import _ezb, _gleif

CODE = "MT"
NAME = "Malta"
BLZ_STELLEN = None
SEITE = _ezb.SEITE
QUELLE = {
    "name": "Europäische Zentralbank – Listen der Finanzinstitute (MFI, PSRI); Bankcode und BIC abgeleitet über GLEIF",
    "kurz": "EZB",
    "url": SEITE,
    "bedingungen": _ezb.BEDINGUNGEN,
    "hinweis": "Source: European Central Bank – lists of monetary financial institutions (MFI) and payment statistics "
               "relevant institutions (PSRI). Geändert: auf maltesische Institute gefiltert; Bankcode und BIC nicht "
               "von der EZB, sondern abgeleitet aus der BIC/LEI-Zuordnung von GLEIF (Bankcode = erste vier Zeichen "
               "des BIC). Nicht amtlich und unvollständig, ohne Sort Codes.",
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
