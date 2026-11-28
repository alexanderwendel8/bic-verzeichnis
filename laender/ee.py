"""Estland – Tunnuskoodid (IBAN-Bankcodes) der Finanzaufsicht Finantsinspektsioon, BICs über GLEIF.

- Die zweistelligen Codes (IBAN-Stellen 5–6) vergibt seit 2017 die Finantsinspektsioon; die amtliche Liste
  steht auf zwei Seiten ihrer Website (Kreditinstitute; Zahlungs- und E-Geld-Institute), nur als HTML-Tabelle.
  Jede Seite nennt das Datum der letzten Änderung („Viimati muudetud 25.08.2025“). Ein Institut kann
  mehrere Codes haben (Luminor: 96 und 17); jeder Code ist ein Eintrag.
- BICs führt die Finantsinspektsioon nicht. Sie kommen aus der BIC/LEI-Zuordnung von GLEIF (estnische BICs),
  verknüpft über den Namen des Instituts (GLEIF: rechtlicher Name und weitere Namen). Filialen ausländischer
  Institute führt GLEIF unter dem LEI der Mutter; für sie gibt es eine kleine, von Hand gepflegte Liste
  (laender/ee_bic_korrekturen.csv, je Eintrag mit Beleg).
- Bedingungen der Finantsinspektsioon: Vervielfältigen und Verbreiten nur mit vorheriger Erlaubnis; erlaubt
  ist die Nutzung in der Presse und für nicht kommerzielle Zwecke mit Quellenangabe, Änderungen sind
  kenntlich zu machen. Das Verzeichnis ist nicht kommerziell; die Quellenangabe weist darauf hin, dass eine
  kommerzielle Weiterverwendung der estnischen Codes eine Erlaubnis der Finantsinspektsioon braucht.
"""

from __future__ import annotations

import html
import json
import re
import sys
import unicodedata
import urllib.parse
from pathlib import Path

import kern
from kern import SCHLUESSEL, Stand, herunterladen, leer
from laender import _gleif

CODE = "EE"
NAME = "Estland"
BLZ_STELLEN = None
SEITEN = {
    "Kreditinstitute": "https://www.fi.ee/et/pangandus-ja-krediit/krediidivaldkonna-tegevuslubade-taotlemine/"
                       "krediidiasutuse-rahvusvahelise-kontonumbri-tunnuskood",
    "Zahlungsinstitute": "https://www.fi.ee/et/makse-ja-e-raha-teenused/makseteenuse-valdkonna-tegevuslubade-taotlemine/"
                         "makse-ja-e-raha-asutuse-rahvusvahelise-kontonumbri-tunnuskood",
}
QUELLE = {
    "name": "Finantsinspektsioon – Rahvusvahelise kontonumbri tunnuskoodid (BIC: GLEIF)",
    "kurz": "Finantsinspektsioon",
    "url": SEITEN["Kreditinstitute"],
    # „Veebilehel esitatud informatsiooni kasutamine on lubatud ajakirjanduses ja mittetulunduslikel eesmärkidel,
    # kui märgitakse ära informatsiooni allikas. Kui kasutaja muudab informatsiooni, tuleb see selgesõnaliselt ära märkida.“
    "bedingungen": "https://www.fi.ee/et/veebilehe-info-ja-kasutustingimused",
    "hinweis": "Allikas: Finantsinspektsioon – krediidiasutuste ning makse- ja e-raha asutuste rahvusvahelise "
               "kontonumbri tunnuskoodid (www.fi.ee). Nicht kommerzielle Nutzung; eine kommerzielle Weiterverwendung "
               "der estnischen Codes braucht eine Erlaubnis der Finantsinspektsioon. Geändert: zwei Listen "
               "zusammengeführt, je Code eine Zeile; BICs nicht von der Finantsinspektsioon, sondern aus der "
               "BIC/LEI-Zuordnung von GLEIF und von Hand mit Beleg (laender/ee_bic_korrekturen.csv) ergänzt.",
}
KORREKTUREN = Path(__file__).with_name("ee_bic_korrekturen.csv")
SPALTEN = ["Bankleitzahl", "BIC", "Weitere BICs", "BIC-Quelle", "Bankenname", "Art", "Weitere Codes", "LEI"]
_ARTEN = {"Krediidiasutus": "Kreditinstitut", "Välisriigi krediidiasutuse filiaal": "Filiale eines ausländischen Kreditinstituts",
          "Makseasutus/e-raha asutus": "Zahlungs- oder E-Geld-Institut",
          "Välisriigi makseasutuse filiaal": "Filiale eines ausländischen Zahlungsinstituts"}


def _zelle(wert: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", wert)).replace("\xa0", " ")).strip()


def tabellen_lesen(seite: str) -> tuple[list[dict], str | None]:
    """-> ([{Name, Codes, Art}], Datum der letzten Änderung JJJJ-MM-TT)."""
    eintraege = []
    for tabelle in re.findall(r"(?s)<table.*?</table>", seite):
        zeilen = [[_zelle(c) for c in re.findall(r"(?s)<t[dh][^>]*>(.*?)</t[dh]>", tr)]
                  for tr in re.findall(r"(?s)<tr.*?</tr>", tabelle)]
        if not zeilen or len(zeilen[0]) < 2 or zeilen[0][1] != "Tunnuskood":
            continue
        art = _ARTEN.get(zeilen[0][0])
        if art is None:
            raise RuntimeError(f"unbekannte Tabelle bei der Finantsinspektsioon: {zeilen[0][0]!r}")
        for z in zeilen[1:]:
            if len(z) < 2 or not z[0]:
                continue
            codes = re.findall(r"\d+", z[1])
            if not codes or any(len(c) != 2 for c in codes):
                raise RuntimeError(f"unerwarteter Code bei der Finantsinspektsioon: {z}")
            eintraege.append({"Name": z[0], "Codes": codes, "Art": art})
    m = re.search(r"Viimati muudetud\s*(?:<[^>]+>\s*)*(\d{2})\.(\d{2})\.(\d{4})", seite)
    return eintraege, f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def _norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().upper()
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(r"\b(AS|AKTSIASELTS|SA|PLC|AB|OYJ|EESTI|FILIAAL)\b", " ", s)
    return " ".join(s.split())


def _gleif_bics() -> tuple[dict[str, tuple[str, list[str]]], str]:
    """({normierter Name: (LEI, [estnische BICs])}, Stand der Tabelle JJJJ-MM)."""
    paare, tabelle, datei = _gleif.zuordnung()
    nach_lei: dict[str, list[str]] = {}
    for bic, lei in paare:
        if bic[4:6] == "EE":
            nach_lei.setdefault(lei, []).append(bic)
    leis, namen = sorted(nach_lei), {}
    for i in range(0, len(leis), 100):
        q = urllib.parse.urlencode({"filter[lei]": ",".join(leis[i:i + 100]), "page[size]": 100})
        for d in json.loads(_gleif.holen(f"{_gleif.LEI_API}?{q}"))["data"]:
            e = d["attributes"]["entity"]
            if e.get("status") != "ACTIVE":
                continue
            for n in [e["legalName"]["name"]] + [x.get("name", "") for x in e.get("otherNames") or []]:
                namen.setdefault(_norm(n), (d["id"], nach_lei[d["id"]]))
    print(f"[{CODE}] GLEIF {datei}: {sum(map(len, nach_lei.values()))} estnische BICs, {len(nach_lei)} LEIs")
    return namen, tabelle


def laden(args, alte_meta: dict) -> Stand:
    if args.input:
        seiten = {art: p.read_bytes().decode("utf-8", "replace") for art, p in zip(SEITEN, args.input)}
    else:
        seiten = {art: herunterladen(url).decode("utf-8", "replace") for art, url in SEITEN.items()}
    banken: dict[str, dict] = {}
    staende = {}
    for art, seite in seiten.items():
        eintraege, stand = tabellen_lesen(seite)
        if not eintraege:
            raise RuntimeError(f"keine Codes auf der Seite der Finantsinspektsioon ({art}) – Seite geändert?")
        staende[art] = stand
        for e in eintraege:
            for c in e["Codes"]:
                if c in banken:
                    raise RuntimeError(f"Code {c} bei der Finantsinspektsioon mehrfach vergeben")
                banken[c] = {"Bankleitzahl": c, "BIC": "", "Weitere BICs": "", "BIC-Quelle": "", "Bankenname": e["Name"],
                             "Art": e["Art"], "Weitere Codes": " ".join(x for x in e["Codes"] if x != c), "LEI": ""}

    # BICs über GLEIF (bei Ausfall: letzter Stand)
    alt = {z[SCHLUESSEL]: z for z in kern.csv_lesen(kern.daten_ordner(sys.modules[__name__]) / "bankleitzahlen.csv")[1]}
    try:
        nach_name, tabelle = _gleif_bics()
    except Exception as e:
        print(f"[{CODE}] Warnung: GLEIF nicht erreichbar ({e}) – BICs des letzten Stands werden verwendet")
        nach_name, tabelle = None, alte_meta.get("GLEIF-Tabelle", "")
    for blz, z in banken.items():
        if nach_name is None:
            for s in ("BIC", "Weitere BICs", "BIC-Quelle", "LEI"):
                z[s] = alt.get(blz, {}).get(s, "")
            continue
        lei, bics = nach_name.get(_norm(z["Bankenname"]), ("", []))
        haupt, weitere = _gleif.bic_wahl(sorted(set(bics)))
        z.update({"BIC": haupt, "Weitere BICs": " ".join(weitere), "BIC-Quelle": "GLEIF" if haupt else "", "LEI": lei})
    korrigiert = _gleif.korrekturen_anwenden(CODE, KORREKTUREN, r"\d{2}", banken, "der Liste der Finantsinspektsioon")

    neu = sorted(banken.values(), key=lambda z: z[SCHLUESSEL])
    ab = max((s for s in staende.values() if s), default=None)
    print(f"[{CODE}] Finantsinspektsioon (Stand {', '.join(f'{k} {v}' for k, v in staende.items())}): {len(neu)} Codes, "
          f"{sum(1 for z in neu if z['BIC'])} mit BIC, davon {korrigiert} aus der Korrekturliste")
    meta = {"Quelle": SEITEN, "Stand": staende, "GLEIF-Tabelle": tabelle}
    neu_stand = ab and alte_meta.get("Stand") != staende and ab <= args.today.isoformat()
    return Stand(spalten=SPALTEN, banken=neu, datum=ab if neu_stand else args.today.isoformat(), meta=meta,
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
        "bic_quelle": g("BIC-Quelle") or ("GLEIF" if g("BIC") else None),
        "weitere_bics": (z.get("Weitere BICs") or "").split(),
        "art": g("Art"),
        "weitere_codes": (z.get("Weitere Codes") or "").split(),
        "lei": g("LEI"),
    }


# ---------------------------------------------------------------- Webseite

WEB = {
    "suche_platzhalter": "Bankcode (2-stellig), BIC oder Name …",
    "suche": ["bankleitzahl", "bic", "name", "lei"],
    "suche_listen": ["weitere_bics"],
    "filter": [{"feld": "art", "alle": "Alle Arten"}],
    "spalte5": {"titel": "Art", "feld": "art"},
    "aenderung_name": "Bankenname",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Täglicher Vergleich mit dem Vortag (Listen der Finantsinspektsioon). Ein Institut kann "
                           "mehrere Codes haben; jeder Code ist ein eigener Eintrag.",
    "details": [
        ["Bankcode", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"], ["BIC-Quelle", "bic_quelle"],
        ["Weitere BICs", "weitere_bics", "liste"], ["Weitere Codes", "weitere_codes", "liste"], ["Art", "art"],
        ["LEI", "lei", "lei"],
    ],
}


def stand_text(meta: dict) -> str:
    return "BICs über GLEIF ergänzt"


def zusatz_hinweis(meta: dict) -> str:
    return _gleif.swift_hinweis(meta.get("GLEIF-Tabelle"))
