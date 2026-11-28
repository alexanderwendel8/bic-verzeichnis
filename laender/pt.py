"""Portugal – Bankcodes aus der MFI-Liste der Europäischen Zentralbank (EZB), BICs über GLEIF.

- Die amtliche Liste des Banco de Portugal („Participantes no SICOI e respetivo BIC“) ist für Programme
  nicht abrufbar: Die Website sperrt automatische Zugriffe (Browser-Prüfung).
- In der MFI-Liste der EZB enthält die Kennung (RIAD-Code) portugiesischer Kreditinstitute mit eigenem Code den
  vierstelligen Bankcode der IBAN (Stellen 5–8) ohne führende Nullen: „PT33“ = Banco Comercial Português, 0033.
  Kennungen mit vier Ziffern (z. B. „PT1280“) sind die lokalen Kassen des Crédito Agrícola; sie haben keinen
  eigenen IBAN-Code, sondern laufen über die Caixa Central („PT9000“), die den Code 0045 führt. Längere
  Kennungen (Steuernummer) gehören zu Filialen ohne eigenen Code und werden nicht übernommen.
- BICs kommen aus der GLEIF-Zuordnung (nur portugiesische BICs), über den LEI des Instituts, bei Filialen
  ausländischer Banken über den LEI der Mutter.
- Ergebnis ist **abgeleitet, nicht amtlich**: Zahlungs- und E-Geld-Institute mit eigenem Code fehlen, ebenso
  frühere Codes übernommener Banken.
- Bedingungen der EZB: freie Nutzung, genaue Wiedergabe, EZB als Quelle nennen, Änderungen kennzeichnen.
  Für die BICs gilt der SWIFT-Hinweis der GLEIF-Zuordnung.
"""

from __future__ import annotations

import re

from kern import SCHLUESSEL, Stand
from laender import _ezb, _gleif

CODE = "PT"
NAME = "Portugal"
BLZ_STELLEN = None
SEITE = _ezb.SEITE
QUELLE = {
    "name": "Europäische Zentralbank – Liste der Monetären Finanzinstitute (MFI); BIC über GLEIF",
    "kurz": "EZB",
    "url": SEITE,
    "bedingungen": _ezb.BEDINGUNGEN,
    "hinweis": "Source: European Central Bank – list of monetary financial institutions (MFI). Geändert: auf portugiesische "
               "Kreditinstitute mit eigenem Code gefiltert, Bankcode aus der EZB-Kennung (RIAD-Code) entnommen; BICs "
               "nicht von der EZB, sondern aus der BIC/LEI-Zuordnung von GLEIF ergänzt. Nicht amtlich und unvollständig – "
               "die amtliche Liste des Banco de Portugal ist nicht automatisch abrufbar.",
}
ORIGINAL_URL = SEITE
SPALTEN = _ezb.SPALTEN
# EZB-Kennungen, deren IBAN-Code nicht in der Kennung steht
_SONDERFAELLE = {"PT9000": "0045"}  # Caixa Central de Crédito Agrícola Mútuo


def bankcode(riad: str) -> str | None:
    if riad in _SONDERFAELLE:
        return _SONDERFAELLE[riad]
    m = re.fullmatch(r"PT(\d{1,3})", riad)
    return m.group(1).zfill(4) if m else None


def laden(args, alte_meta: dict) -> Stand:
    liste, info = _ezb.institute(CODE, mit_psri=False)
    nach_lei, tabelle, gleif_datei = _ezb.bics_nach_lei(CODE)
    banken = {}
    for i in liste:
        blz = bankcode(i["EZB-Kennung"])
        if not blz:
            continue
        if blz in banken:
            raise RuntimeError(f"Bankcode {blz} mehrfach in der MFI-Liste")
        bics = sorted(set(nach_lei.get(i["LEI"]) or nach_lei.get(i["Mutter-LEI"]) or []))
        haupt, weitere = _gleif.bic_wahl(bics)
        banken[blz] = {**{s: i.get(s, "") for s in SPALTEN}, "Bankleitzahl": blz, "BIC": haupt,
                       "Weitere BICs": " ".join(weitere)}
    if not banken:
        raise RuntimeError("keine portugiesischen Bankcodes in der MFI-Liste gefunden")
    zeilen = sorted(banken.values(), key=lambda z: z[SCHLUESSEL])
    print(f"[{CODE}] EZB {info['MFI-Datei']}: {info['MFI']} MFIs, {len(zeilen)} mit eigenem Bankcode, GLEIF "
          f"{gleif_datei}: {sum(1 for z in zeilen if z['BIC'])} mit BIC")
    meta = {"Quelle": SEITE, "GLEIF-Tabelle": tabelle}
    return Stand(spalten=SPALTEN, banken=zeilen, datum=args.today.isoformat(), meta=meta,
                 dateien={"HINWEIS-BIC.txt": _gleif.hinweis_datei(tabelle, QUELLE["hinweis"])})


# ---------------------------------------------------------------- API

def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    return _ezb.api_eintrag(CODE, z)


# ---------------------------------------------------------------- Webseite

WEB = _ezb.web(
    "Bankcode (4-stellig), BIC, Name oder Ort …",
    "Abgeleitet, nicht amtlich: Bankcode aus der EZB-Kennung der Kreditinstitute (MFI-Liste), BIC über GLEIF. "
    "Zahlungsinstitute und frühere Codes fehlen; die Kassen des Crédito Agrícola laufen über den Code 0045.")
WEB["filter"] = []


def stand_text(meta: dict) -> str:
    return "abgeleitet aus der MFI-Liste der EZB und GLEIF – nicht amtlich, unvollständig"


def zusatz_hinweis(meta: dict) -> str:
    return _gleif.swift_hinweis(meta.get("GLEIF-Tabelle"))
