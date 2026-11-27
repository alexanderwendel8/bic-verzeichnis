"""Spanien – Registro de Entidades des Banco de España (BdE), BICs über GLEIF.

- Der BdE bietet das Register nur als Excel (.xlsx) an (daneben eine Webanwendung ohne offene
  Schnittstelle), kein XML, JSON oder CSV. Verwendet wird „Registro_Entidades.xlsx“: Kreditinstitute,
  Zahlungs- und E-Geld-Institute und weitere beaufsichtigte Stellen, täglich aktualisiert. Die erste
  Zeile nennt den Stand („FECHA: 26/11/2026“). Gelesen ohne Zusatzbibliothek (laender/_xlsx.py).
- Die Bankleitzahl (código de entidad) ist vierstellig und steht in der IBAN an den Stellen 5–8.
  Übernommen werden Einträge mit vierstelligem „CÓDIGO BE“ ohne Abmeldedatum (FECHA BAJA).
- Das Register enthält auch frühere Einträge mit Abmeldedatum, Grund und Nachfolger (SUCESORAS).
  Codes werden teils wiederverwendet; abgemeldete Codes, die heute nicht vergeben sind, stehen in
  meta.json und sind in der API mit Status „entfernt“ und Nachfolger abrufbar.
- Der BdE führt keine BICs. Sie kommen aus der BIC/LEI-Zuordnung von GLEIF, verknüpft über den LEI
  aus dem Register (nur spanische BICs). Zweigstellen ausländischer Banken haben meist keinen LEI;
  für sie wird ersatzweise die spanische Steuernummer (NIF) mit GLEIF „registeredAs“ verglichen.
  Fällt GLEIF aus, werden die BICs des letzten Stands weiterverwendet.
- Die Originaldatei ändert sich täglich (Stand in der ersten Zeile) und ist rund 1,7 MB groß; sie wird
  deshalb nicht abgelegt, sondern beim BdE verlinkt.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
import urllib.parse
from collections import defaultdict

import kern
from kern import SCHLUESSEL, Stand, herunterladen, leer
from laender import _gleif
from laender._xlsx import xlsx_lesen

CODE = "ES"
NAME = "Spanien"
BLZ_STELLEN = None
URL = "https://www.bde.es/f/webbe/SGE/regis/ficheros/es/Registro_Entidades.xlsx"
SEITE = "https://app.bde.es/rbe_spa/"
QUELLE = {
    "name": "Banco de España – Registro de Entidades (BIC: GLEIF)",
    "kurz": "Banco de España",
    "url": SEITE,
    # Aviso legal: Wiedergabe erlaubt, „fielmente, sin manipular ni alterar los contenidos“, Quelle Banco de España
    "bedingungen": "https://www.bde.es/wbe/es/pie/aviso-legal/",
    "hinweis": "Fuente: Banco de España – Registro de Entidades. Inhalt unverändert übernommen, nur umformatiert "
               "(auf heute eingetragene Institute mit vierstelligem Code gefiltert, Datumsangaben als JJJJ-MM-TT); "
               "die Originaldatei steht beim Banco de España. BICs nicht vom Banco de España, sondern aus der "
               "BIC/LEI-Zuordnung von GLEIF ergänzt.",
}
ORIGINAL_URL = URL
SPALTEN = ["Bankleitzahl", "BIC", "Weitere BICs", "Bankenname", "Art", "Art-Code", "NIF", "LEI", "Muttergesellschaft",
           "Eingetragen seit", "Straße", "PLZ", "Ort", "Provinz", "Land", "Telefon", "Homepage", "Herkunftsland"]
_KOPF = ["CÓDIGO BE", "NOMBRE", "DOCUMENTO IDENTIFICATIVO", "NOMBRE ENTIDAD MATRIZ", "CODIGO TIPO ENTIDAD",
         "TIPO ENTIDAD", "CÓDIGO LEI", "FECHA ALTA", "DIRECCIÓN", "POBLACIÓN", "CÓDIGO POSTAL", "PROVINCIA",
         "PAÍS (ISO2)", "TELÉFONO", "PÁGINA WEB", "PAÍS DE ORIGEN (ISO2)", "FECHA BAJA", "MOTIVO BAJA", "SUCESORAS"]


def _datum(wert: str) -> str:
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", (wert or "").strip())
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else (wert or "").strip()


def _gleif_bics(eigene_leis: set[str]) -> tuple[dict[str, list[str]], dict[str, list[str]], str]:
    """({LEI: [spanische BICs]}, {NIF: [spanische BICs]}, Stand der Tabelle JJJJ-MM).

    Die NIF-Zuordnung (GLEIF „registeredAs“) hilft bei Zweigstellen ausländischer Banken, die im Register
    keinen LEI haben, bei GLEIF aber als eigene Zweigstelle mit spanischer NIF geführt werden."""
    paare, tabelle, name = _gleif.zuordnung()
    nach_lei = defaultdict(list)
    for bic, lei in paare:
        if bic[4:6] == "ES":
            nach_lei[lei].append(bic)
    rest = sorted(set(nach_lei) - eigene_leis)
    nach_nif = defaultdict(list)
    for i in range(0, len(rest), 100):
        q = urllib.parse.urlencode({"filter[lei]": ",".join(rest[i:i + 100]), "page[size]": 100})
        for d in json.loads(_gleif.holen(f"{_gleif.LEI_API}?{q}"))["data"]:
            e = d["attributes"]["entity"]
            if e.get("status") == "ACTIVE" and e.get("registeredAs"):
                nach_nif[e["registeredAs"].strip().upper()].extend(nach_lei[d["id"]])
    print(f"[{CODE}] GLEIF {name}: {sum(map(len, nach_lei.values()))} spanische BICs, {len(nach_lei)} LEIs")
    return nach_lei, nach_nif, tabelle


def laden(args, alte_meta: dict) -> Stand:
    roh = args.input[0].read_bytes() if args.input else herunterladen(URL)
    blatt, zeilen = xlsx_lesen(roh)
    try:
        k = next(i for i, z in enumerate(zeilen) if "CÓDIGO BE" in z)
    except StopIteration:
        raise RuntimeError("Kopfzeile im BdE-Register nicht gefunden – Format geändert?")
    kopf = zeilen[k]
    fehlend = [s for s in _KOPF if s not in kopf]
    if fehlend:
        raise RuntimeError(f"Spalten fehlen im BdE-Register: {fehlend}")
    pos = {s: kopf.index(s) for s in _KOPF}
    stichtag = None
    for z in zeilen[:k]:
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", " ".join(z))
        if m:
            stichtag = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()

    banken: dict[str, dict] = {}
    abgemeldet: dict[str, dict] = {}
    for z in zeilen[k + 1:]:
        w = lambda s: z[pos[s]].strip() if pos[s] < len(z) else ""
        blz = w("CÓDIGO BE")
        if not re.fullmatch(r"\d{4}", blz):
            continue
        if w("FECHA BAJA"):
            datum = _datum(w("FECHA BAJA"))
            if blz not in abgemeldet or datum >= abgemeldet[blz]["Datum"]:
                abgemeldet[blz] = {"Bankleitzahl": blz, "Name": w("NOMBRE"), "Datum": datum,
                                   "Grund": w("MOTIVO BAJA"), "Nachfolge-Bankleitzahl": w("SUCESORAS")}
            continue
        if blz in banken:
            raise RuntimeError(f"Code {blz} ist im BdE-Register mehrfach aktiv")
        banken[blz] = {
            "Bankleitzahl": blz, "BIC": "", "Weitere BICs": "", "Bankenname": w("NOMBRE"), "Art": w("TIPO ENTIDAD"),
            "Art-Code": w("CODIGO TIPO ENTIDAD"), "NIF": w("DOCUMENTO IDENTIFICATIVO"), "LEI": w("CÓDIGO LEI"),
            "Muttergesellschaft": w("NOMBRE ENTIDAD MATRIZ"), "Eingetragen seit": _datum(w("FECHA ALTA")),
            "Straße": w("DIRECCIÓN"), "PLZ": w("CÓDIGO POSTAL"), "Ort": w("POBLACIÓN"), "Provinz": w("PROVINCIA"),
            "Land": w("PAÍS (ISO2)"), "Telefon": w("TELÉFONO"), "Homepage": w("PÁGINA WEB"),
            "Herkunftsland": w("PAÍS DE ORIGEN (ISO2)"),
        }
    if not banken:
        raise RuntimeError("keine eingetragenen Institute im BdE-Register gefunden")

    # BICs über GLEIF (bei Ausfall: letzter Stand)
    try:
        nach_lei, nach_nif, tabelle = _gleif_bics({z["LEI"] for z in banken.values() if z["LEI"]})
    except Exception as e:
        print(f"[{CODE}] Warnung: GLEIF nicht erreichbar ({e}) – BICs des letzten Stands werden verwendet")
        alt = {z[SCHLUESSEL]: z for z in kern.csv_lesen(kern.daten_ordner(sys.modules[__name__]) / "bankleitzahlen.csv")[1]}
        nach_lei, tabelle = None, alte_meta.get("GLEIF-Tabelle", "")
    for blz, z in banken.items():
        if nach_lei is None:
            z["BIC"], z["Weitere BICs"] = alt.get(blz, {}).get("BIC", ""), alt.get(blz, {}).get("Weitere BICs", "")
        else:
            bics = nach_lei.get(z["LEI"], []) if z["LEI"] else nach_nif.get(z["NIF"].upper(), []) if z["NIF"] else []
            haupt, weitere = _gleif.bic_wahl(sorted(set(bics)))
            z["BIC"], z["Weitere BICs"] = haupt, " ".join(weitere)

    frueher = [a for blz, a in sorted(abgemeldet.items()) if blz not in banken]
    mit_bic = sum(1 for z in banken.values() if z["BIC"])
    print(f"[{CODE}] Register vom {stichtag}: {len(banken)} Institute ({mit_bic} mit BIC über GLEIF), "
          f"{len(frueher)} frühere Codes")
    # Kein Stichtag in meta.json: er ändert sich täglich und würde sonst jeden Tag einen Commit auslösen.
    meta = {"Quelle": URL, "GLEIF-Tabelle": tabelle, "Abmeldungen": frueher}
    return Stand(spalten=SPALTEN, banken=sorted(banken.values(), key=lambda z: z[SCHLUESSEL]),
                 datum=stichtag or args.today.isoformat(), meta=meta,
                 dateien={"HINWEIS-BIC.txt": _gleif.hinweis_datei(tabelle, QUELLE["hinweis"])})


# ---------------------------------------------------------------- API

def _homepage(wert):
    wert = leer(wert)
    if wert:
        wert = re.sub(r"^(https?)://", lambda m: m.group(1).lower() + "://", wert, flags=re.I)
        if not re.match(r"https?://", wert):
            wert = "https://" + wert
    return wert


def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    g = lambda s: leer(z.get(s))
    return {
        "land": CODE,
        "bankleitzahl": g("Bankleitzahl"),
        "bic": g("BIC"),
        "name": g("Bankenname"),
        "status": None,
        "entfernt_am": None,
        "bic_quelle": "GLEIF" if g("BIC") else None,
        "weitere_bics": (z.get("Weitere BICs") or "").split(),
        "art": g("Art"),
        "art_code": g("Art-Code"),
        "nif": g("NIF"),
        "lei": g("LEI"),
        "muttergesellschaft": g("Muttergesellschaft"),
        "eingetragen_seit": g("Eingetragen seit"),
        "nachfolge_bankleitzahl": None,
        "abmeldegrund": None,
        "adresse": {"strasse": g("Straße"), "plz": g("PLZ"), "ort": g("Ort"), "provinz": g("Provinz"),
                    "land": g("Land")},
        "herkunftsland": g("Herkunftsland"),
        "kontakt": {"telefon": g("Telefon"), "homepage": _homepage(z.get("Homepage"))},
    }


def _endziel(blz: str, nachfolger: dict[str, str], aktiv: set[str]) -> str:
    """Folgt einer Kette von Nachfolgern bis zum heute aktiven Code (oder bis zum letzten bekannten Glied)."""
    gesehen = {blz}
    while blz not in aktiv and nachfolger.get(blz) and nachfolger[blz] not in gesehen:
        blz = nachfolger[blz]
        gesehen.add(blz)
    return blz


def zusatz_eintraege(eintraege: dict[str, dict], meta: dict) -> dict[str, dict]:
    """Abgemeldete Codes aus dem Register: letzter Name, Abmeldedatum, Grund und (heute aktiver) Nachfolger."""
    abm = meta.get("Abmeldungen", [])
    nachfolger = {a["Bankleitzahl"]: a.get("Nachfolge-Bankleitzahl", "") for a in abm}
    aktiv = {k for k, e in eintraege.items() if e["status"] == "aktiv"}
    extra = {}
    for a in abm:
        blz = a["Bankleitzahl"]
        ziel = _endziel(blz, nachfolger, aktiv) if nachfolger.get(blz) else None
        if blz in eintraege:  # schon als entfernt protokolliert: Datum, Grund und Nachfolger ergänzen
            e = eintraege[blz]
            if e["status"] == "entfernt":
                e["entfernt_am"] = a.get("Datum") or e["entfernt_am"]
                e["abmeldegrund"] = a.get("Grund") or None
                e["nachfolge_bankleitzahl"] = e.get("nachfolge_bankleitzahl") or ziel
            continue
        e = api_eintrag({"Bankleitzahl": blz, "Bankenname": a.get("Name", "")}, [], meta, True)
        e.update({"status": "entfernt", "entfernt_am": a.get("Datum") or None, "abmeldegrund": a.get("Grund") or None,
                  "nachfolge_bankleitzahl": ziel})
        extra[blz] = e
    return extra


# ---------------------------------------------------------------- Webseite

WEB = {
    "suche_platzhalter": "Bankleitzahl (4-stellig), BIC, Bankname, Ort oder LEI …",
    "suche": ["bankleitzahl", "bic", "name", "adresse.plz", "adresse.ort", "adresse.provinz", "lei", "nif"],
    "suche_listen": ["weitere_bics"],
    "filter": [{"feld": "art", "alle": "Alle Arten"}, {"feld": "adresse.provinz", "alle": "Alle Provinzen"}],
    "spalte5": {"titel": "Art", "feld": "art"},
    "aenderung_name": "Bankenname",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Täglicher Vergleich mit dem Vortag (Registro de Entidades des Banco de España). Frühere "
                           "Codes abgemeldeter Institute lassen sich über die Suche finden, wenn man sie genau eingibt.",
    "details": [
        ["Bankleitzahl", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"],
        ["BIC-Quelle", "bic_quelle"], ["Weitere BICs", "weitere_bics", "liste"], ["LEI", "lei", "lei"],
        ["Nachfolge-Code", "nachfolge_bankleitzahl", "blz"], ["Abmeldegrund", "abmeldegrund"],
        ["Art", "art"], ["NIF", "nif"], ["Muttergesellschaft", "muttergesellschaft"],
        ["Eingetragen seit", "eingetragen_seit", "datum"], ["Adresse", "adresse", "adresse"],
        ["Provinz", "adresse.provinz"], ["Herkunftsland", "herkunftsland"],
        ["Telefon", "kontakt.telefon"], ["Homepage", "kontakt.homepage", "url"],
    ],
}


def stand_text(meta: dict) -> str:
    return "BICs über GLEIF ergänzt"


def zusatz_hinweis(meta: dict) -> str:
    return _gleif.swift_hinweis(meta.get("GLEIF-Tabelle"))
