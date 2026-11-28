"""Niederlande – abgeleitet aus Institutslisten der Europäischen Zentralbank (EZB) und der GLEIF-Zuordnung.

- Die vollständige Liste der niederländischen IBAN-Bankcodes (BIC-lijst-NL) führt die Betaalvereniging
  Nederland; ihre Bedingungen verbieten die Weitergabe ohne schriftliche Erlaubnis. Sie wird nicht verwendet.
- Der niederländische Bankcode (IBAN-Stellen 5–8) sind die ersten vier Buchstaben des BIC. Er lässt sich daher
  ableiten: Institute aus den EZB-Listen → LEI → niederländische BICs aus der BIC/LEI-Zuordnung von GLEIF →
  Bankcode = BIC[0:4]. Bei Filialen ausländischer Institute werden auch die niederländischen BICs der
  Mutter (HEAD_LEI) berücksichtigt.
- EZB-Listen: die tägliche Liste der Monetären Finanzinstitute (MFI, Kreditinstitute und Zentralbank) und die
  halbjährliche Liste der für die Zahlungsverkehrsstatistik relevanten Institute (PSRI, auch Zahlungs- und
  E-Geld-Institute). Beide nennen keine BICs.
- Ergebnis ist **nicht amtlich und unvollständig**: Es fehlen Codes, für die GLEIF keinen BIC kennt (z. B. ASN,
  Knab), und nicht jeder abgeleitete Code wird tatsächlich für niederländische IBANs vergeben.
- Bedingungen der EZB: freie Nutzung, Angaben genau wiedergeben, EZB als Quelle nennen, Änderungen ausdrücklich
  kennzeichnen. Für die BICs (und damit die Bankcodes) gilt der SWIFT-Hinweis der GLEIF-Zuordnung.
"""

from __future__ import annotations

from kern import Stand
from laender import _ezb, _gleif

CODE = "NL"
NAME = "Niederlande"
BLZ_STELLEN = None
SEITE = _ezb.SEITE
QUELLE = {
    "name": "Europäische Zentralbank – Listen der Finanzinstitute (MFI, PSRI); Bankcode und BIC abgeleitet über GLEIF",
    "kurz": "EZB",
    "url": SEITE,
    # „users of this website may make free use of the information obtained directly from it … it must appear
    # accurately and the ECB must be cited as the source … If the information is modified … this must be stated“
    "bedingungen": _ezb.BEDINGUNGEN,
    "hinweis": "Source: European Central Bank – lists of monetary financial institutions (MFI) and payment statistics "
               "relevant institutions (PSRI). Geändert: auf niederländische Institute gefiltert; Bankcode und BIC nicht "
               "von der EZB, sondern abgeleitet aus der BIC/LEI-Zuordnung von GLEIF (Bankcode = erste vier Zeichen "
               "des BIC). Nicht amtlich und unvollständig – die amtliche Liste der Betaalvereniging Nederland darf "
               "nicht weitergegeben werden.",
}
ORIGINAL_URL = SEITE
SPALTEN = _ezb.SPALTEN


def laden(args, alte_meta: dict) -> Stand:
    liste, info = _ezb.institute(CODE)
    nach_lei, tabelle, gleif_datei = _ezb.bics_nach_lei(CODE)
    banken = _ezb.codes_aus_bic(CODE, liste, nach_lei)
    print(f"[{CODE}] EZB {info['MFI-Datei']}: {info['MFI']} MFIs, {info['PSRI-Liste']}: {info['PSRI']} Zahlungsdienstleister; "
          f"GLEIF {gleif_datei}: {len(banken)} abgeleitete Bankcodes")
    # Keine täglich wechselnden Angaben in meta.json (MFI-Datei), sonst entstünde jeden Tag ein Commit.
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
    "Unvollständig – nicht jede Bank ist enthalten, und nicht jeder Code wird für niederländische IBANs verwendet.")


def stand_text(meta: dict) -> str:
    return "abgeleitet aus EZB-Listen und GLEIF – nicht amtlich, unvollständig"


def zusatz_hinweis(meta: dict) -> str:
    return _gleif.swift_hinweis(meta.get("GLEIF-Tabelle"))
