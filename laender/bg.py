"""Bulgarien – abgeleitet aus der MFI-Liste der EZB und den Teilnehmerlisten der Българска народна банка (BNB).

- Die BNB veröffentlicht keine Liste der Bankcodes mit BIC. Der bulgarische Bankcode (IBAN-Stellen 5–8) sind die
  ersten vier Buchstaben des BIC; dahinter folgt der vierstellige Filialcode (BAE, Stellen 9–12).
- Banken: aus der MFI-Liste der EZB (laender/_ezb.py), BICs über den LEI aus der GLEIF-Zuordnung (bei Filialen
  ausländischer Banken über die Mutter). Die EZB-Kennung bulgarischer Banken enthält Bankcode und Filialcode
  der Zentrale („BGSTSA9300“ = DSK Bank, Bankcode STSA, BAE 9300); der Filialcode wird als „BAE (Zentrale)“
  übernommen.
- Zahlungs- und E-Geld-Institute: aus den Teilnehmerlisten der BNB für TARGET (T2) und TIPS (XLSX) mit
  Handelsregisternummer (ЕИК); über die ЕИК („registeredAs“ bei GLEIF) zum LEI und damit zum BIC.
- Der Server der BNB ist langsam; bis zu vier Versuche mit langer Wartezeit. Ist er nicht erreichbar, werden
  nur die Banken aus der EZB-Liste übernommen.
- Ergebnis ist **abgeleitet, nicht amtlich**; Filialcodes außer dem der Zentrale fehlen.
- Bedingungen: EZB – freie Nutzung mit Quellenangabe, Änderungen kennzeichnen; BNB – Weitergabe erlaubt, wenn
  die Quelle genannt und der Inhalt nicht verändert wird. Für BICs und Bankcodes gilt der SWIFT-Hinweis.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse

from kern import Stand, herunterladen, leer
from laender import _ezb, _gleif
from laender._xlsx import xlsx_lesen

CODE = "BG"
NAME = "Bulgarien"
BLZ_STELLEN = None
SEITE = _ezb.SEITE
BNB_LISTEN = {
    "T2": "https://www.bnb.bg/bnbweb/groups/public/documents/bnb_download/ps_target_list_users_bg.xlsx",
    "TIPS": "https://www.bnb.bg/bnbweb/groups/public/documents/bnb_download/ps_tips_list_users_bg.xlsx",
}
QUELLE = {
    "name": "Europäische Zentralbank (MFI-Liste) und Българска народна банка (Teilnehmer TARGET/TIPS); "
            "Bankcode und BIC abgeleitet über GLEIF",
    "kurz": "EZB / BNB",
    "url": SEITE,
    # EZB: Disclaimer; BNB (https://www.bnb.bg/AboutUs/PressOffice/PORightsUsing/index.htm): „разрешение … да
    # разпространявате и възпроизвеждате данни при условие, че посочите източника и не променяте или изопачавате“
    "bedingungen": _ezb.BEDINGUNGEN,
    "hinweis": "Source: European Central Bank – list of monetary financial institutions (MFI); Източник: Българска "
               "народна банка – участници в TARGET-BNB и TIPS. Geändert: gefiltert und zusammengeführt; Bankcode und "
               "BIC nicht von EZB oder BNB, sondern abgeleitet aus der BIC/LEI-Zuordnung von GLEIF (Bankcode = erste "
               "vier Zeichen des BIC). Nicht amtlich und unvollständig.",
}
ORIGINAL_URL = SEITE
SPALTEN = _ezb.SPALTEN + ["BAE (Zentrale)", "ЕИК", "BNB-Liste"]


def _bnb_holen(url: str) -> bytes:
    for versuch in range(4):
        try:
            return herunterladen(url, timeout=240)
        except Exception as e:
            if versuch == 3:
                raise
            print(f"[{CODE}] BNB: Download fehlgeschlagen ({e}) – neuer Versuch")
            time.sleep(10 * (versuch + 1))


def _bnb_teilnehmer() -> list[dict]:
    """-> [{ЕИК, Name, Liste}] aus den Teilnehmerlisten der BNB (ohne Nebensysteme)."""
    teilnehmer: dict[str, dict] = {}
    for liste, url in BNB_LISTEN.items():
        _, zeilen = xlsx_lesen(_bnb_holen(url))
        kopf = next((i for i, z in enumerate(zeilen) if "ЕИК" in [c.strip() for c in z]), None)
        if kopf is None:
            raise RuntimeError(f"Kopfzeile in der BNB-Liste {liste} nicht gefunden")
        k = [c.strip() for c in zeilen[kopf]]
        p_eik, p_tr = k.index("ЕИК"), k.index("Транслитерация")
        for z in zeilen[kopf + 1:]:
            eik = z[p_eik].strip() if p_eik < len(z) else ""
            name = z[p_tr].strip() if p_tr < len(z) else ""
            if re.fullmatch(r"\d{9}(\d{4})?", eik) and name not in ("BORICA", "BISERA"):
                t = teilnehmer.setdefault(eik, {"ЕИК": eik, "Name": name, "Listen": []})
                t["Listen"].append(liste)
    return list(teilnehmer.values())


def _lei_nach_eik(eiks: list[str]) -> dict[str, str]:
    leis = {}
    for i in range(0, len(eiks), 50):
        q = urllib.parse.urlencode({"filter[entity.registeredAs]": ",".join(eiks[i:i + 50]),
                                    "filter[entity.legalAddress.country]": "BG", "page[size]": 100})
        for d in json.loads(_gleif.holen(f"{_gleif.LEI_API}?{q}"))["data"]:
            e = d["attributes"]["entity"]
            if e.get("status") == "ACTIVE" and e.get("registeredAs"):
                leis[e["registeredAs"].strip()] = d["id"]
    return leis


def laden(args, alte_meta: dict) -> Stand:
    liste, info = _ezb.institute(CODE, mit_psri=False)
    for i in liste:
        m = re.fullmatch(r"BG[A-Z]{4}(\d{4})", i["EZB-Kennung"])
        i["BAE (Zentrale)"] = m.group(1) if m else ""
    nach_lei, tabelle, gleif_datei = _ezb.bics_nach_lei(CODE)

    bnb = 0
    try:
        teilnehmer = _bnb_teilnehmer()
        leis = _lei_nach_eik([t["ЕИК"] for t in teilnehmer])
        bekannt = {i["LEI"] for i in liste if i["LEI"]}
        for t in teilnehmer:
            lei = leis.get(t["ЕИК"])
            if not lei or lei in bekannt:
                continue
            liste.append({"LEI": lei, "Mutter-LEI": "", "Bankenname": t["Name"], "Art": "Zahlungs- oder E-Geld-Institut",
                          "EZB-Kennung": "", "ЕИК": t["ЕИК"], "BNB-Liste": ", ".join(t["Listen"])})
            bekannt.add(lei)
            bnb += 1
    except Exception as e:
        print(f"[{CODE}] Warnung: Teilnehmerlisten der BNB nicht verfügbar ({e}) – nur Banken aus der EZB-Liste")

    banken = _ezb.codes_aus_bic(CODE, liste, nach_lei, SPALTEN)
    print(f"[{CODE}] EZB {info['MFI-Datei']}: {info['MFI']} MFIs, BNB: {bnb} weitere Zahlungsdienstleister; "
          f"GLEIF {gleif_datei}: {len(banken)} abgeleitete Bankcodes")
    meta = {"Quelle": SEITE, "BNB-Listen": BNB_LISTEN, "GLEIF-Tabelle": tabelle}
    return Stand(spalten=SPALTEN, banken=banken, datum=args.today.isoformat(), meta=meta,
                 dateien={"HINWEIS-BIC.txt": _gleif.hinweis_datei(tabelle, QUELLE["hinweis"])})


# ---------------------------------------------------------------- API

def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    e = _ezb.api_eintrag(CODE, z)
    e.update({"bae_zentrale": leer(z.get("BAE (Zentrale)")), "eik": leer(z.get("ЕИК")), "bnb_liste": leer(z.get("BNB-Liste"))})
    return e


# ---------------------------------------------------------------- Webseite

WEB = _ezb.web(
    "Bankcode (4 Buchstaben), BIC, Name oder Ort …",
    "Abgeleitet, nicht amtlich: Bankcode = erste vier Zeichen des BIC (GLEIF) der Banken aus der MFI-Liste der EZB "
    "und der Zahlungsdienstleister aus den Teilnehmerlisten der BNB. Filialcodes (BAE) nur für die Zentrale.")
WEB["details"] = WEB["details"][:2] + [["BAE (Zentrale)", "bae_zentrale"]] + WEB["details"][2:] + \
    [["ЕИК (Registernummer)", "eik"], ["BNB-Liste", "bnb_liste"]]


def stand_text(meta: dict) -> str:
    return "abgeleitet aus EZB, BNB und GLEIF – nicht amtlich, unvollständig"


def zusatz_hinweis(meta: dict) -> str:
    return _gleif.swift_hinweis(meta.get("GLEIF-Tabelle"))
