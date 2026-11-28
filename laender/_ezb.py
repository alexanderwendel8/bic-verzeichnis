"""Institutslisten der Europäischen Zentralbank (EZB) und daraus abgeleitete Bankcodes – für Länder ohne
weitergebbare amtliche Liste der Bankcodes (Niederlande, Malta, Griechenland).

- MFI-Liste (täglich): Kreditinstitute und Zentralbank aller Länder des Euroraums mit EZB-Kennung (RIAD-Code),
  LEI, Adresse und – bei Filialen – Mutter. CSV in UTF-16, gezippt; der Dateiname wechselt täglich und wird von
  der Seite gelesen.
- PSRI-Liste (halbjährlich): auch Zahlungs- und E-Geld-Institute; XLSX in einem ZIP, verwendet wird die neueste.
- Beide Listen werden je Lauf nur einmal geladen, auch wenn mehrere Länder sie brauchen.
- Bedingungen der EZB: freie Nutzung, genaue Wiedergabe, EZB als Quelle nennen, Änderungen kennzeichnen.
"""

from __future__ import annotations

import csv
import gzip
import html
import io
import re
import time
import urllib.parse
import zipfile
from collections import defaultdict

from kern import SCHLUESSEL, herunterladen
from laender import _gleif
from laender._xlsx import xlsx_lesen

MFI_SEITE = "https://www.ecb.europa.eu/stats/financial_corporations/list_of_financial_institutions/html/daily_list-MID.en.html"
PSRI_URL = "https://www.ecb.europa.eu/stats/pdf/money/psri/ecb.psrid_overview.en.zip"
SEITE = "https://www.ecb.europa.eu/stats/financial_corporations/list_of_financial_institutions/html/index.en.html"
BEDINGUNGEN = "https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html"
SPALTEN = ["Bankleitzahl", "BIC", "Weitere BICs", "Bankenname", "Art", "LEI", "EZB-Kennung", "Straße", "PLZ", "Ort",
           "Muttergesellschaft", "EZB-Liste"]
MFI_ARTEN = {"Credit Institution": "Kreditinstitut", "Central Bank": "Zentralbank"}
PSRI_ARTEN = {"Credit institution": "Kreditinstitut", "Payment institution": "Zahlungsinstitut",
              "Electronic money institution": "E-Geld-Institut"}

_mfi_cache: tuple[list[dict], str] | None = None
_psri_cache: tuple[list[dict], str] | None = None


def holen(url: str) -> bytes:
    for versuch in range(4):
        try:
            return herunterladen(url, timeout=180)
        except Exception as e:
            if versuch == 3:
                raise
            print(f"[EZB] Download fehlgeschlagen ({e}) – neuer Versuch")
            time.sleep(5 * (versuch + 1))


def mfi(land: str) -> tuple[list[dict], str]:
    """-> (Kreditinstitute und Zentralbank eines Landes aus der täglichen MFI-Liste, Dateiname)."""
    global _mfi_cache
    if _mfi_cache is None:
        seite = holen(MFI_SEITE).decode("utf-8", "replace")
        links = re.findall(r'href="([^"]*/mfi_csv_\d{6}\.csv\.gz)"', seite)
        if not links:
            raise RuntimeError("kein Link zur MFI-Liste auf der EZB-Seite gefunden – Seite geändert?")
        url = urllib.parse.urljoin(MFI_SEITE, html.unescape(links[0]))
        zeilen = list(csv.DictReader(io.StringIO(gzip.decompress(holen(url)).decode("utf-16")), delimiter="\t"))
        if not zeilen or "LEI" not in zeilen[0] or "HEAD_LEI" not in zeilen[0]:
            raise RuntimeError("unerwartetes Format der MFI-Liste")
        _mfi_cache = (zeilen, url.rsplit("/", 1)[-1])
    zeilen, datei = _mfi_cache
    return [z for z in zeilen if z.get("COUNTRY_OF_REGISTRATION") == land and z.get("CATEGORY") in MFI_ARTEN], datei


def psri(land: str) -> tuple[list[dict], str]:
    """-> (Zahlungsdienstleister eines Landes aus der neuesten PSRI-Liste, Name der Liste)."""
    global _psri_cache
    if _psri_cache is None:
        z = zipfile.ZipFile(io.BytesIO(holen(PSRI_URL)))
        namen = [n for n in z.namelist() if re.search(r"PSRIs_\d{4}(_H[12])?\.xlsx$", n)]
        if not namen:
            raise RuntimeError("keine PSRI-Liste im ZIP der EZB gefunden")
        name = max(namen, key=lambda n: re.search(r"PSRIs_(\d{4})(?:_H([12]))?", n).groups(default="3"))
        _, zeilen = xlsx_lesen(z.read(name))
        kopf = zeilen[0]
        for s in ("Country of Residence", "ID", "LEI", "Name", "Payment Service Provider"):
            if s not in kopf:
                raise RuntimeError(f"Spalte {s!r} fehlt in der PSRI-Liste")
        _psri_cache = ([dict(zip(kopf, r + [""] * (len(kopf) - len(r)))) for r in zeilen[1:]],
                       re.search(r"PSRIs_[^/]+(?=\.xlsx)", name).group())
    eintraege, name = _psri_cache
    return [e for e in eintraege if e["Country of Residence"] == land], name


def institute(land: str, mit_psri: bool = True) -> tuple[list[dict], dict]:
    """-> (Institute eines Landes: MFI zuerst, dann PSRI für die übrigen; Angaben zu den Listen)."""
    m, mfi_datei = mfi(land)
    liste = []
    for z in m:
        liste.append({"LEI": z["LEI"], "Mutter-LEI": z.get("HEAD_LEI", ""), "Bankenname": z["NAME"],
                      "Art": MFI_ARTEN[z["CATEGORY"]], "EZB-Kennung": z["RIAD_CODE"], "Straße": z.get("ADDRESS", ""),
                      "PLZ": z.get("POSTAL", ""), "Ort": z.get("CITY", ""), "Muttergesellschaft": z.get("HEAD_NAME", ""),
                      "EZB-Liste": "MFI"})
    info = {"MFI-Datei": mfi_datei, "MFI": len(m)}
    if mit_psri:
        p, psri_name = psri(land)
        bekannt = {i["LEI"] for i in liste if i["LEI"]}
        for z in p:
            if not z["LEI"] or z["LEI"] in bekannt:
                continue
            art = next((v for k, v in PSRI_ARTEN.items() if z["Payment Service Provider"].startswith(k)), "Zahlungsdienstleister")
            liste.append({"LEI": z["LEI"], "Mutter-LEI": "", "Bankenname": z["Name"], "Art": art, "EZB-Kennung": z["ID"],
                          "Straße": z.get("Address", ""), "PLZ": z.get("Postal Code", ""), "Ort": z.get("City", ""),
                          "Muttergesellschaft": "", "EZB-Liste": f"PSRI {psri_name[6:].replace('_', ' ')}"})
            bekannt.add(z["LEI"])
        info.update({"PSRI-Liste": psri_name, "PSRI": len(p)})
    return liste, info


def bics_nach_lei(land: str) -> tuple[dict[str, list[str]], str, str]:
    """-> ({LEI: [BICs mit Ländercode land]}, Stand der GLEIF-Tabelle JJJJ-MM, Dateiname)."""
    paare, tabelle, datei = _gleif.zuordnung()
    nach_lei: dict[str, list[str]] = defaultdict(list)
    for bic, lei in paare:
        if bic[4:6] == land:
            nach_lei[lei].append(bic)
    return nach_lei, tabelle, datei


def codes_aus_bic(land: str, liste: list[dict], nach_lei: dict[str, list[str]],
                  spalten: list[str] | None = None) -> list[dict]:
    """Bankcode = erste vier Zeichen des BIC (eigene BICs, sonst die der Mutter) -> Zeilen nach spalten."""
    spalten = spalten or SPALTEN
    codes: dict[str, dict] = {}
    for i in liste:
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
                           **{k: i[k] for k in spalten if k in i}}
    if not codes:
        raise RuntimeError(f"keine Bankcodes für {land} abgeleitet")
    return [{s: z.get(s, "") for s in spalten} for z in sorted(codes.values(), key=lambda z: z[SCHLUESSEL])]


def api_eintrag(code: str, z: dict) -> dict:
    """Gemeinsame API-Felder der abgeleiteten Länder."""
    g = lambda s: (z.get(s) or "").strip() or None
    return {
        "land": code,
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


def web(platzhalter: str, hinweis: str, bankcode: str = "Bankcode (abgeleitet)") -> dict:
    return {
        "suche_platzhalter": platzhalter,
        "suche": ["bankleitzahl", "bic", "name", "adresse.ort", "lei", "muttergesellschaft"],
        "suche_listen": ["weitere_bics"],
        "filter": [{"feld": "art", "alle": "Alle Arten"}],
        "spalte5": {"titel": "Art", "feld": "art"},
        "aenderung_name": "Bankenname",
        "aenderung_bic": "BIC",
        "hinweis_aenderungen": hinweis,
        "details": [
            [bankcode, "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"], ["BIC-Quelle", "bic_quelle"],
            ["Weitere BICs", "weitere_bics", "liste"], ["Art", "art"], ["LEI", "lei", "lei"],
            ["EZB-Kennung", "ezb_kennung"], ["EZB-Liste", "ezb_liste"], ["Muttergesellschaft", "muttergesellschaft"],
            ["Adresse", "adresse", "adresse"],
        ],
    }
