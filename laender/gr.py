"""Griechenland – Bankcodes aus der MFI-Liste der Europäischen Zentralbank (EZB), BICs über GLEIF.

- Die Bank of Greece sperrt automatische Abrufe ihrer Website; die Filialcodes (HEBIC) führt der Bankenverband
  als PDF ohne BICs und ohne Lizenz. Beides wird nicht verwendet.
- In der MFI-Liste der EZB enthält die Kennung (RIAD-Code) griechischer Kreditinstitute den dreistelligen
  Bankcode der IBAN (Stellen 5–7): „GR014N“ = Alpha Bank, Bankcode 014. Übernommen werden Kreditinstitute und
  die Bank of Greece, deren Kennung diesem Muster folgt.
- BICs kommen aus der GLEIF-Zuordnung (nur griechische BICs), über den LEI des Instituts, bei Filialen
  ausländischer Banken über den LEI der Mutter. Für einen Teil der Institute gibt es keinen BIC.
- Ergebnis ist **abgeleitet, nicht amtlich**: Zahlungs- und E-Geld-Institute mit eigenem Bankcode fehlen,
  ebenso frühere Codes übernommener Banken; Filialcodes (IBAN-Stellen 8–11) sind nicht enthalten.
- Bedingungen der EZB: freie Nutzung, genaue Wiedergabe, EZB als Quelle nennen, Änderungen kennzeichnen.
  Für die BICs gilt der SWIFT-Hinweis der GLEIF-Zuordnung.
"""

from __future__ import annotations

import re

from kern import SCHLUESSEL, Stand
from laender import _ezb, _gleif

CODE = "GR"
NAME = "Griechenland"
BLZ_STELLEN = None
SEITE = _ezb.SEITE
QUELLE = {
    "name": "Europäische Zentralbank – Liste der Monetären Finanzinstitute (MFI); BIC über GLEIF",
    "kurz": "EZB",
    "url": SEITE,
    "bedingungen": _ezb.BEDINGUNGEN,
    "hinweis": "Source: European Central Bank – list of monetary financial institutions (MFI). Geändert: auf griechische "
               "Kreditinstitute gefiltert, Bankcode aus der EZB-Kennung (RIAD-Code) entnommen; BICs nicht von der EZB, "
               "sondern aus der BIC/LEI-Zuordnung von GLEIF ergänzt. Nicht amtlich und unvollständig.",
}
ORIGINAL_URL = SEITE
SPALTEN = _ezb.SPALTEN
_RIAD = re.compile(r"GR(\d{3})N?")


def laden(args, alte_meta: dict) -> Stand:
    liste, info = _ezb.institute(CODE, mit_psri=False)
    nach_lei, tabelle, gleif_datei = _ezb.bics_nach_lei(CODE)
    banken = {}
    for i in liste:
        m = _RIAD.fullmatch(i["EZB-Kennung"])
        if not m:
            continue
        blz = m.group(1)
        if blz in banken:
            raise RuntimeError(f"Bankcode {blz} mehrfach in der MFI-Liste")
        bics = sorted(set(nach_lei.get(i["LEI"]) or nach_lei.get(i["Mutter-LEI"]) or []))
        haupt, weitere = _gleif.bic_wahl(bics)
        banken[blz] = {**{s: i.get(s, "") for s in SPALTEN}, "Bankleitzahl": blz, "BIC": haupt,
                       "Weitere BICs": " ".join(weitere)}
    if not banken:
        raise RuntimeError("keine griechischen Bankcodes in der MFI-Liste gefunden")
    zeilen = sorted(banken.values(), key=lambda z: z[SCHLUESSEL])
    print(f"[{CODE}] EZB {info['MFI-Datei']}: {len(zeilen)} Bankcodes, GLEIF {gleif_datei}: "
          f"{sum(1 for z in zeilen if z['BIC'])} mit BIC")
    meta = {"Quelle": SEITE, "GLEIF-Tabelle": tabelle}
    return Stand(spalten=SPALTEN, banken=zeilen, datum=args.today.isoformat(), meta=meta,
                 dateien={"HINWEIS-BIC.txt": _gleif.hinweis_datei(tabelle, QUELLE["hinweis"])})


# ---------------------------------------------------------------- API

def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    return _ezb.api_eintrag(CODE, z)


# ---------------------------------------------------------------- Webseite

WEB = _ezb.web(
    "Bankcode (3-stellig), BIC, Name oder Ort …",
    "Abgeleitet, nicht amtlich: Bankcode aus der EZB-Kennung der Kreditinstitute (MFI-Liste), BIC über GLEIF. "
    "Zahlungsinstitute, frühere Codes und Filialcodes fehlen.")
WEB["filter"] = []


def stand_text(meta: dict) -> str:
    return "abgeleitet aus der MFI-Liste der EZB und GLEIF – nicht amtlich, unvollständig"


def zusatz_hinweis(meta: dict) -> str:
    return _gleif.swift_hinweis(meta.get("GLEIF-Tabelle"))
