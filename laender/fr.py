"""Frankreich – REGAFI (Registre des agents financiers) der ACPR / Banque de France, BICs über GLEIF.

- REGAFI bietet eine offene Schnittstelle (Opendatasoft) mit Export als JSON, täglich aktualisiert.
  Verwendet wird der Datensatz „prd-banque-entites“, gefiltert auf Einträge mit CIB
  (code interbancaire, früher „code banque“): rund 840 Institute statt 26.000 Einträge, 0,7 MB statt 18 MB.
- Der CIB ist fünfstellig und steht in der IBAN an den Stellen 5–9. Ein Institut kann mehrere CIBs haben
  (z. B. nach Übernahmen); jeder CIB ist eine Zeile. Das Feld „cib“ ist eine JSON-Liste als Text
  ([{"code": "30004", "date": "…"}]).
- Die ACPR führt keine BICs. Sie kommen aus der BIC/LEI-Zuordnung von GLEIF, verknüpft über den LEI aus
  REGAFI (BICs aus Frankreich, Monaco und den Überseegebieten, bevorzugt französische). Fällt GLEIF aus,
  werden die BICs des letzten Stands weiterverwendet.
- Lücken und Fehler der GLEIF-Zuordnung (z. B. Société Générale, LCL) behebt eine kleine, von Hand gepflegte
  Liste (laender/fr_bic_korrekturen.csv, je Eintrag mit Beleg); diese BICs haben die Quelle „manuell“.
- REGAFI hat keine eigene Lizenz. Grundlage ist das französische Recht zur Weiterverwendung öffentlicher
  Informationen (CRPA L321-1 ff.) und die rechtlichen Hinweise der Banque de France: ACPR als Quelle und
  das Datum der letzten Aktualisierung nennen, Inhalt nicht verfälschen. Das Datum der letzten inhaltlichen
  Änderung wird deshalb in meta.json festgehalten („Stand“).
- REGAFI bricht Verbindungen gelegentlich ab; der Download wird bis zu viermal versucht.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

import kern
from kern import SCHLUESSEL, Stand, herunterladen, leer
from laender import _gleif

CODE = "FR"
NAME = "Frankreich"
BLZ_STELLEN = None
DATENSATZ = "https://www.regafi.fr/api/explore/v2.1/catalog/datasets/prd-banque-entites"
URL = DATENSATZ + "/exports/json?" + urllib.parse.urlencode({"where": 'cib != "[]"'})
SEITE = "https://www.regafi.fr/"
QUELLE = {
    "name": "ACPR / Banque de France – REGAFI, Registre des agents financiers (BIC: GLEIF)",
    "kurz": "ACPR",
    "url": SEITE,
    # Keine eigenen Bedingungen auf regafi.fr; Banque de France: Wiederverwendung erlaubt, Quelle Banque de France
    # oder ACPR und Datum der letzten Aktualisierung nennen, Daten nicht verfälschen (CRPA L321-1 ff.)
    "bedingungen": "https://www.banque-france.fr/fr/infos-legales",
    "hinweis": "Source : Autorité de contrôle prudentiel et de résolution (ACPR) – REGAFI (www.regafi.fr). Inhalt "
               "unverändert übernommen, nur umformatiert (auf Institute mit code interbancaire gefiltert, je Code "
               "eine Zeile); BICs nicht von der ACPR, sondern aus der BIC/LEI-Zuordnung von GLEIF ergänzt, einzelne von "
               "Hand mit Beleg (laender/fr_bic_korrekturen.csv).",
}
ORIGINAL_URL = URL
SPALTEN = ["Bankleitzahl", "BIC", "Weitere BICs", "BIC-Quelle", "Bankenname", "Handelsnamen", "Kürzel", "Kategorie", "Rechtsform",
           "Zulassung", "SIREN", "LEI", "Code seit", "Weitere Codes", "Straße", "PLZ", "Ort", "Land",
           "Muttergesellschaft", "Ereignisse", "REGAFI-ID"]
# BIC-Ländercodes im französischen IBAN-Raum (Frankreich, Monaco, Überseegebiete)
# Von Hand gepflegte BICs für Lücken und Fehler der GLEIF-Zuordnung, jeder Eintrag mit Beleg
KORREKTUREN = Path(__file__).with_name("fr_bic_korrekturen.csv")
_BIC_LAENDER = {"FR", "MC", "GP", "GF", "MQ", "RE", "YT", "PM", "BL", "MF", "NC", "PF", "WF"}


def _holen(url: str) -> bytes:
    for versuch in range(4):
        try:
            return herunterladen(url, timeout=180)
        except Exception as e:
            if versuch == 3:
                raise
            print(f"[{CODE}] Download fehlgeschlagen ({e}) – neuer Versuch")
            time.sleep(5 * (versuch + 1))


def _json_feld(wert):
    if isinstance(wert, str):
        try:
            return json.loads(wert)
        except ValueError:
            return wert
    return wert


def _gleif_bics() -> tuple[dict[str, list[str]], str]:
    paare, tabelle, name = _gleif.zuordnung()
    bics: dict[str, list[str]] = {}
    for bic, lei in paare:
        if bic[4:6] in _BIC_LAENDER:
            bics.setdefault(lei, []).append(bic)
    print(f"[{CODE}] GLEIF {name}: {sum(map(len, bics.values()))} BICs im französischen IBAN-Raum, {len(bics)} LEIs")
    return bics, tabelle


def laden(args, alte_meta: dict) -> Stand:
    roh = args.input[0].read_bytes() if args.input else _holen(URL)
    eintraege = json.loads(roh)
    if not isinstance(eintraege, list) or (eintraege and "cib" not in eintraege[0]):
        raise RuntimeError("unerwartetes REGAFI-Format")

    banken: dict[str, dict] = {}
    for r in eintraege:
        codes = [c for c in (_json_feld(r.get("cib")) or []) if isinstance(c, dict) and c.get("code")]
        handel = _json_feld(r.get("nom_commerciaux")) or {}
        for c in codes:
            blz = str(c["code"]).strip()
            if blz in banken:
                raise RuntimeError(f"CIB {blz} ist in REGAFI mehrfach vergeben")
            banken[blz] = {
                "Bankleitzahl": blz, "BIC": "", "Weitere BICs": "", "Bankenname": (r.get("denomination") or "").strip(),
                "Handelsnamen": " | ".join(handel) if isinstance(handel, dict) else str(handel),
                "Kürzel": r.get("sigle") or "", "Kategorie": " | ".join(r.get("categorie") or []),
                "Rechtsform": r.get("forme_juridique") or "", "Zulassung": r.get("nature_autorisation") or "",
                "SIREN": r.get("siren") or "", "LEI": r.get("lei") or "", "Code seit": c.get("date") or "",
                "Weitere Codes": " ".join(str(x["code"]) for x in codes if x is not c),
                "Straße": r.get("adresse") or "", "PLZ": r.get("code_postal") or "", "Ort": r.get("ville") or "",
                "Land": r.get("pays") or "", "Muttergesellschaft": r.get("denomination_entite_parente") or "",
                "Ereignisse": " | ".join(" ".join(e.split()) for e in (r.get("evenements") or [])),
                "REGAFI-ID": str(r.get("id_referentiel") or ""),
            }
    if not banken:
        raise RuntimeError("keine Institute mit CIB in REGAFI gefunden")

    # BICs über GLEIF (bei Ausfall: letzter Stand)
    alt = {z[SCHLUESSEL]: z for z in kern.csv_lesen(kern.daten_ordner(sys.modules[__name__]) / "bankleitzahlen.csv")[1]}
    try:
        nach_lei, tabelle = _gleif_bics()
    except Exception as e:
        print(f"[{CODE}] Warnung: GLEIF nicht erreichbar ({e}) – BICs des letzten Stands werden verwendet")
        nach_lei, tabelle = None, alte_meta.get("GLEIF-Tabelle", "")
    for blz, z in banken.items():
        if nach_lei is None:
            for s in ("BIC", "Weitere BICs", "BIC-Quelle"):
                z[s] = alt.get(blz, {}).get(s, "")
            continue
        bics = sorted(set(nach_lei.get(z["LEI"], []))) if z["LEI"] else []
        bics = [b for b in bics if b[4:6] == "FR"] or bics  # französische BICs bevorzugen
        haupt, weitere = _gleif.bic_wahl(bics)
        z["BIC"], z["Weitere BICs"], z["BIC-Quelle"] = haupt, " ".join(weitere), "GLEIF" if haupt else ""

    # Korrekturliste: ersetzt den GLEIF-BIC (der dann unter „Weitere BICs“ steht) oder füllt eine Lücke
    korrigiert = 0
    for k in _korrekturen():
        z = banken.get(k["Bankleitzahl"])
        if z is None:
            print(f"[{CODE}] Warnung: Korrektur für {k['Bankleitzahl']} ({k['Institut']}) – Code nicht mehr in REGAFI")
            continue
        if z["BIC"] != k["BIC"]:
            weitere = [b for b in [z["BIC"], *z["Weitere BICs"].split()] if b and b != k["BIC"]]
            z["BIC"], z["Weitere BICs"] = k["BIC"], " ".join(dict.fromkeys(weitere))
        z["BIC-Quelle"] = "manuell"
        korrigiert += 1

    neu = sorted(banken.values(), key=lambda z: z[SCHLUESSEL])
    heute = args.today.isoformat()
    # „Stand“ = letzte Änderung der REGAFI-Angaben (BICs zählen nicht dazu, sie kommen nicht von der ACPR)
    regafi = [s for s in SPALTEN if s not in ("BIC", "Weitere BICs", "BIC-Quelle")]
    vergleich = lambda zeilen: [{s: z.get(s, "") for s in regafi} for z in zeilen]
    geaendert = vergleich(neu) != vergleich(sorted(alt.values(), key=lambda z: z[SCHLUESSEL]))
    stand = heute if geaendert or not alte_meta.get("Stand") else alte_meta["Stand"]
    mit_bic = sum(1 for z in neu if z["BIC"])
    print(f"[{CODE}] REGAFI: {len(eintraege)} Institute mit {len(neu)} CIBs ({mit_bic} mit BIC, davon {korrigiert} "
          f"aus der Korrekturliste), Stand {stand}")
    meta = {"Quelle": URL, "Stand": stand, "GLEIF-Tabelle": tabelle}
    return Stand(spalten=SPALTEN, banken=neu, datum=heute, meta=meta,
                 dateien={"HINWEIS-BIC.txt": _gleif.hinweis_datei(tabelle, QUELLE["hinweis"]) + (
                     "\nAusnahme: BICs mit BIC-Quelle „manuell“ stammen nicht aus der GLEIF-Zuordnung, sondern aus einer "
                     "von Hand gepflegten Liste mit Beleg je Eintrag (laender/fr_bic_korrekturen.csv im Repository).\n"
                 ).encode("utf-8")})


def _korrekturen() -> list[dict]:
    if not KORREKTUREN.exists():
        return []
    with KORREKTUREN.open(encoding="utf-8", newline="") as f:
        zeilen = [{k: (v or "").strip() for k, v in z.items()} for z in csv.DictReader(f, delimiter=";")]
    for z in zeilen:
        if not re.fullmatch(r"\d{5}", z["Bankleitzahl"]) or not re.fullmatch(r"[A-Z0-9]{8}([A-Z0-9]{3})?", z["BIC"]):
            raise RuntimeError(f"ungültige Zeile in {KORREKTUREN.name}: {z}")
    return zeilen


# ---------------------------------------------------------------- API

def _liste(wert: str | None) -> list[str]:
    return [x.strip() for x in (wert or "").split("|") if x.strip()]


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
        "handelsnamen": _liste(z.get("Handelsnamen")),
        "kuerzel": g("Kürzel"),
        "kategorie": _liste(z.get("Kategorie")),
        "rechtsform": g("Rechtsform"),
        "zulassung": g("Zulassung"),
        "siren": g("SIREN"),
        "lei": g("LEI"),
        "code_seit": g("Code seit"),
        "weitere_codes": (z.get("Weitere Codes") or "").split(),
        "muttergesellschaft": g("Muttergesellschaft"),
        "ereignisse": _liste(z.get("Ereignisse")),
        "regafi_id": g("REGAFI-ID"),
        "adresse": {"strasse": g("Straße"), "plz": g("PLZ"), "ort": g("Ort"), "land": g("Land")},
        "stand": meta.get("Stand"),
    }


# ---------------------------------------------------------------- Webseite

WEB = {
    "suche_platzhalter": "Code banque (5-stellig), BIC, Bankname, Ort, SIREN oder LEI …",
    "suche": ["bankleitzahl", "bic", "name", "kuerzel", "adresse.plz", "adresse.ort", "siren", "lei"],
    "suche_listen": ["weitere_bics", "handelsnamen"],
    "filter": [{"feld": "rechtsform", "alle": "Alle Rechtsformen"}],
    "spalte5": {"titel": "Kategorie", "feld": "kategorie"},
    "aenderung_name": "Bankenname",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Täglicher Vergleich mit dem Vortag (REGAFI der ACPR). Hat ein Institut mehrere Codes, "
                           "ist jeder Code ein eigener Eintrag.",
    "details": [
        ["Code banque (CIB)", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"], ["BIC-Quelle", "bic_quelle"],
        ["Weitere BICs", "weitere_bics", "liste"], ["LEI", "lei", "lei"], ["Code vergeben am", "code_seit", "datum"],
        ["Weitere Codes", "weitere_codes", "liste"], ["Kategorie", "kategorie", "liste"], ["Rechtsform", "rechtsform"],
        ["Zulassung", "zulassung"], ["SIREN", "siren"], ["Handelsnamen", "handelsnamen", "liste"],
        ["Kürzel", "kuerzel"], ["Muttergesellschaft", "muttergesellschaft"], ["Sitz", "adresse", "adresse"],
        ["Land", "adresse.land"], ["Ereignisse", "ereignisse", "liste"], ["Stand REGAFI", "stand", "datum"],
    ],
}


def stand_text(meta: dict) -> str:
    return "BICs über GLEIF ergänzt"


def quellen_hinweis(meta: dict) -> str:
    """Quellenangabe mit Datum der letzten Aktualisierung (Bedingung der Banque de France / CRPA)."""
    if not meta.get("Stand"):
        return QUELLE["hinweis"]
    stand = "/".join(reversed(meta["Stand"].split("-")))
    return QUELLE["hinweis"].replace("REGAFI (www.regafi.fr).", f"REGAFI (www.regafi.fr), données mises à jour le {stand}.")


def zusatz_hinweis(meta: dict) -> str:
    return _gleif.swift_hinweis(meta.get("GLEIF-Tabelle"))
