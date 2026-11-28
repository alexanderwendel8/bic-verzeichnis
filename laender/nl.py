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

import csv
import gzip
import html
import io
import re
import sys
import time
import urllib.parse
import zipfile
from collections import defaultdict

import kern
from kern import SCHLUESSEL, Stand, herunterladen, leer
from laender import _gleif
from laender._xlsx import xlsx_lesen

CODE = "NL"
NAME = "Niederlande"
BLZ_STELLEN = None
MFI_SEITE = "https://www.ecb.europa.eu/stats/financial_corporations/list_of_financial_institutions/html/daily_list-MID.en.html"
PSRI_URL = "https://www.ecb.europa.eu/stats/pdf/money/psri/ecb.psrid_overview.en.zip"
SEITE = "https://www.ecb.europa.eu/stats/financial_corporations/list_of_financial_institutions/html/index.en.html"
QUELLE = {
    "name": "Europäische Zentralbank – Listen der Finanzinstitute (MFI, PSRI); Bankcode und BIC abgeleitet über GLEIF",
    "kurz": "EZB",
    "url": SEITE,
    # „users of this website may make free use of the information obtained directly from it … it must appear
    # accurately and the ECB must be cited as the source … If the information is modified … this must be stated“
    "bedingungen": "https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html",
    "hinweis": "Source: European Central Bank – lists of monetary financial institutions (MFI) and payment statistics "
               "relevant institutions (PSRI). Geändert: auf niederländische Institute gefiltert; Bankcode und BIC nicht "
               "von der EZB, sondern abgeleitet aus der BIC/LEI-Zuordnung von GLEIF (Bankcode = erste vier Zeichen "
               "des BIC). Nicht amtlich und unvollständig – die amtliche Liste der Betaalvereniging Nederland darf "
               "nicht weitergegeben werden.",
}
ORIGINAL_URL = SEITE
SPALTEN = ["Bankleitzahl", "BIC", "Weitere BICs", "Bankenname", "Art", "LEI", "EZB-Kennung", "Straße", "PLZ", "Ort",
           "Muttergesellschaft", "EZB-Liste"]
_PSRI_ARTEN = {"Credit institution": "Kreditinstitut", "Payment institution": "Zahlungsinstitut",
               "Electronic money institution": "E-Geld-Institut"}
_MFI_ARTEN = {"Credit Institution": "Kreditinstitut", "Central Bank": "Zentralbank"}


def _holen(url: str) -> bytes:
    for versuch in range(4):
        try:
            return herunterladen(url, timeout=180)
        except Exception as e:
            if versuch == 3:
                raise
            print(f"[{CODE}] Download fehlgeschlagen ({e}) – neuer Versuch")
            time.sleep(5 * (versuch + 1))


def _mfi() -> tuple[list[dict], str]:
    """-> (niederländische Kreditinstitute und Zentralbank aus der täglichen MFI-Liste, Dateiname)."""
    seite = _holen(MFI_SEITE).decode("utf-8", "replace")
    links = re.findall(r'href="([^"]*/mfi_csv_\d{6}\.csv\.gz)"', seite)
    if not links:
        raise RuntimeError("kein Link zur MFI-Liste auf der EZB-Seite gefunden – Seite geändert?")
    url = urllib.parse.urljoin(MFI_SEITE, html.unescape(links[0]))
    text = gzip.decompress(_holen(url)).decode("utf-16")
    zeilen = list(csv.DictReader(io.StringIO(text), delimiter="\t"))
    if not zeilen or "LEI" not in zeilen[0] or "HEAD_LEI" not in zeilen[0]:
        raise RuntimeError("unerwartetes Format der MFI-Liste")
    return [z for z in zeilen if z.get("COUNTRY_OF_REGISTRATION") == "NL" and z.get("CATEGORY") in _MFI_ARTEN], url


def _psri() -> tuple[list[dict], str]:
    """-> (niederländische Zahlungsdienstleister aus der neuesten PSRI-Liste, Name der Liste)."""
    z = zipfile.ZipFile(io.BytesIO(_holen(PSRI_URL)))
    namen = [n for n in z.namelist() if re.search(r"PSRIs_\d{4}(_H[12])?\.xlsx$", n)]
    if not namen:
        raise RuntimeError("keine PSRI-Liste im ZIP der EZB gefunden")
    name = max(namen, key=lambda n: re.search(r"PSRIs_(\d{4})(?:_H([12]))?", n).groups(default="3"))
    _, zeilen = xlsx_lesen(z.read(name))
    kopf = zeilen[0]
    for s in ("Country of Residence", "ID", "LEI", "Name", "Payment Service Provider"):
        if s not in kopf:
            raise RuntimeError(f"Spalte {s!r} fehlt in der PSRI-Liste")
    eintraege = [dict(zip(kopf, r + [""] * (len(kopf) - len(r)))) for r in zeilen[1:]]
    return [e for e in eintraege if e["Country of Residence"] == "NL"], re.search(r"PSRIs_[^/]+(?=\.xlsx)", name).group()


def laden(args, alte_meta: dict) -> Stand:
    mfi, mfi_url = _mfi()
    psri, psri_name = _psri()
    paare, tabelle, gleif_datei = _gleif.zuordnung()
    nach_lei: dict[str, list[str]] = defaultdict(list)
    for bic, lei in paare:
        if bic[4:6] == "NL":
            nach_lei[lei].append(bic)

    # Institute: MFI zuerst (mit Mutter bei Filialen), dann PSRI für die übrigen
    institute = []
    for z in mfi:
        institute.append({"LEI": z["LEI"], "Mutter-LEI": z.get("HEAD_LEI", ""), "Bankenname": z["NAME"],
                          "Art": _MFI_ARTEN[z["CATEGORY"]], "EZB-Kennung": z["RIAD_CODE"], "Straße": z.get("ADDRESS", ""),
                          "PLZ": z.get("POSTAL", ""), "Ort": z.get("CITY", ""), "Muttergesellschaft": z.get("HEAD_NAME", ""),
                          "EZB-Liste": "MFI"})
    bekannt = {i["LEI"] for i in institute if i["LEI"]}
    for z in psri:
        if not z["LEI"] or z["LEI"] in bekannt:
            continue
        art = next((v for k, v in _PSRI_ARTEN.items() if z["Payment Service Provider"].startswith(k)), "Zahlungsdienstleister")
        institute.append({"LEI": z["LEI"], "Mutter-LEI": "", "Bankenname": z["Name"], "Art": art, "EZB-Kennung": z["ID"],
                          "Straße": z.get("Address", ""), "PLZ": z.get("Postal Code", ""), "Ort": z.get("City", ""),
                          "Muttergesellschaft": "", "EZB-Liste": f"PSRI {psri_name[6:].replace('_', ' ')}"})
        bekannt.add(z["LEI"])

    # Bankcodes ableiten: eigene NL-BICs, sonst die der Mutter
    codes: dict[str, dict] = {}
    for i in institute:
        bics = nach_lei.get(i["LEI"]) or nach_lei.get(i["Mutter-LEI"]) or []
        for code in sorted({b[:4] for b in bics}):
            eigene = sorted({b for b in bics if b.startswith(code)})
            if code in codes:  # mehrere Institute mit demselben Code (z. B. zwei Filialen derselben Gruppe)
                c = codes[code]
                c["Bankenname"] = " / ".join(dict.fromkeys([*c["Bankenname"].split(" / "), i["Bankenname"]]))
                c["Weitere BICs"] = " ".join(sorted(set(c["Weitere BICs"].split()) | set(eigene) - {c["BIC"]}))
                continue
            haupt, weitere = _gleif.bic_wahl(eigene)
            codes[code] = {"Bankleitzahl": code, "BIC": haupt, "Weitere BICs": " ".join(weitere),
                           **{k: i[k] for k in SPALTEN if k in i}}
    if not codes:
        raise RuntimeError("keine niederländischen Bankcodes abgeleitet")
    banken = [{s: z.get(s, "") for s in SPALTEN} for z in sorted(codes.values(), key=lambda z: z[SCHLUESSEL])]
    print(f"[{CODE}] EZB {mfi_url.rsplit('/', 1)[-1]}: {len(mfi)} MFIs, {psri_name}: {len(psri)} Zahlungsdienstleister; "
          f"GLEIF {gleif_datei}: {len(banken)} abgeleitete Bankcodes")
    # Keine täglich wechselnden Angaben in meta.json (MFI-Datei), sonst entstünde jeden Tag ein Commit.
    meta = {"Quelle": SEITE, "PSRI-Liste": psri_name, "GLEIF-Tabelle": tabelle}
    return Stand(spalten=SPALTEN, banken=banken, datum=args.today.isoformat(), meta=meta,
                 dateien={"HINWEIS-BIC.txt": _gleif.hinweis_datei(tabelle, QUELLE["hinweis"])})


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
        "abgeleitet": True,
        "bic_quelle": "GLEIF" if g("BIC") else None,
        "weitere_bics": (z.get("Weitere BICs") or "").split(),
        "art": g("Art"),
        "lei": g("LEI"),
        "ezb_kennung": g("EZB-Kennung"),
        "ezb_liste": g("EZB-Liste"),
        "muttergesellschaft": g("Muttergesellschaft"),
        "adresse": {"strasse": g("Straße"), "plz": g("PLZ"), "ort": g("Ort")},
    }


# ---------------------------------------------------------------- Webseite

WEB = {
    "suche_platzhalter": "Bankcode (4 Buchstaben), BIC, Name oder Ort …",
    "suche": ["bankleitzahl", "bic", "name", "adresse.ort", "lei", "muttergesellschaft"],
    "suche_listen": ["weitere_bics"],
    "filter": [{"feld": "art", "alle": "Alle Arten"}],
    "spalte5": {"titel": "Art", "feld": "art"},
    "aenderung_name": "Bankenname",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Abgeleitet, nicht amtlich: Bankcode = erste vier Zeichen des BIC (GLEIF) der Institute aus "
                           "den Listen der EZB. Unvollständig – nicht jede Bank ist enthalten, und nicht jeder Code wird "
                           "für niederländische IBANs verwendet.",
    "details": [
        ["Bankcode (abgeleitet)", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"], ["BIC-Quelle", "bic_quelle"],
        ["Weitere BICs", "weitere_bics", "liste"], ["Art", "art"], ["LEI", "lei", "lei"],
        ["EZB-Kennung", "ezb_kennung"], ["EZB-Liste", "ezb_liste"], ["Muttergesellschaft", "muttergesellschaft"],
        ["Adresse", "adresse", "adresse"],
    ],
}


def stand_text(meta: dict) -> str:
    return "abgeleitet aus EZB-Listen und GLEIF – nicht amtlich, unvollständig"


def zusatz_hinweis(meta: dict) -> str:
    return _gleif.swift_hinweis(meta.get("GLEIF-Tabelle"))
