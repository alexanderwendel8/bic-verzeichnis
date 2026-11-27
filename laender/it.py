"""Italien – Register der Banca d'Italia (Albi ed elenchi di vigilanza), BICs über GLEIF.

Quelle der Bankdaten: der Download-Bereich („Area download“) der Banca d'Italia, täglich aktualisiert,
als gezipptes XML. Er ist ohne Anmeldung zugänglich; die Webanwendung leitet dabei automatisch über
auth.bancaditalia.it und schickt für anonyme Besucher selbst „username=OBLIXANONYMOUS“ mit.
Die Dateinamen sind nicht fest veröffentlicht: Das Skript holt jedes Mal die Liste der Produkte
(api/areaDown) und lädt dann:

  VFLUSSO_INTERMEDIARIO   Lista intermediari      – Institute mit ABI-Code, Steuernummer, Sitz
  VFLUSSO_SEDE_BANCHE     Lista succursali banche – Filialen mit CAB-Code und Adresse
  VFLUSSO_EVENTO          Lista fusioni …         – Übernahmen/Fusionen mit Nachfolger

Die Dateien enthalten auch frühere Fassungen jedes Eintrags (DATA_I_VAL/DATA_F_VAL); verwendet wird
nur die heute gültige. Übernommen werden Banken (Albo 001), Zahlungsinstitute (012) und E-Geld-Institute
(016) mit ABI-Code, die heute eingetragen sind.

- ABI-Code: in der IBAN fünfstellig an den Stellen 6–10 (nach der Kontrollziffer CIN), CAB-Code
  (Filiale) an den Stellen 11–15.
- Die Banca d'Italia führt keine BICs. Sie kommen aus der BIC/LEI-Zuordnung von GLEIF, verknüpft über
  die italienische Steuernummer (in GLEIF „registeredAs“). Nicht jedes Institut ist dort zu finden.
  Fällt GLEIF aus, werden die BICs des letzten Stands weiterverwendet.
"""

from __future__ import annotations

import csv
import http.cookiejar
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import kern
from kern import SCHLUESSEL, Stand, leer

CODE = "IT"
NAME = "Italien"
BLZ_STELLEN = 5  # ABI-Code in der IBAN fünfstellig (3069 -> 03069)
SEITE = "https://www.bancaditalia.it/servizi-cittadino/servizi/albi-elenchi/index.html"
GIAVA = "https://infostat.bancaditalia.it/GIAVAInquiry-public"
QUELLE = {
    "name": "Banca d'Italia – Albi ed elenchi di vigilanza (BIC: GLEIF)",
    "kurz": "Banca d'Italia",
    "url": SEITE,
    # Die drei Listen sind Open Data der Banca d'Italia unter CC BY 4.0 (Katalog dati.gov.it)
    "bedingungen": "https://www.bancaditalia.it/footer/copyright/index.html",
    "lizenz": "https://creativecommons.org/licenses/by/4.0/deed.de",
    "hinweis": "Fonte: Banca d'Italia – Albi ed elenchi di vigilanza (Lista intermediari, Lista succursali banche, "
               "Lista fusioni, incorporazioni, cessioni attività e passività), Lizenz CC BY 4.0. Geändert: auf heute "
               "gültige Banken, Zahlungs- und E-Geld-Institute gefiltert, umformatiert, BICs aus der BIC/LEI-Zuordnung "
               "von GLEIF ergänzt.",
}
GLEIF_LIZENZ = ("https://www.gleif.org/lei-data/lei-mapping/download-bic-to-lei-relationship-files/"
                "2017-12-21_annex-2_bic-to-lei-mapping-table-license-agreement_final.pdf")
MONATE = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def swift_hinweis(tabelle: str | None) -> str:
    """Pflicht-Hinweis der BIC/LEI-Lizenz (Abschnitt 2) für jede Kopie, auch in Teilen. tabelle = JJJJ-MM."""
    datum = f"{MONATE[int(tabelle[5:7]) - 1]} {tabelle[:4]}" if tabelle else "[unbekannt]"
    return (f"SWIFT © and database rights {datum}. All rights reserved. "
            "This Mapping Table has been developed by SWIFT. Any use of the Mapping Table, in whole or in part, "
            "is subject to the BIC/LEI Mapping Table License Agreement as published with the Mapping Table available "
            "on GLEIF's website. The Mapping Table is updated monthly. For the latest BIC information and updates, "
            "always refer to www.swift.com/bic .")
GLEIF_MAPPING = "https://mapping.gleif.org/api/v2/bic-lei"
GLEIF_LEI = "https://api.gleif.org/api/v1/lei-records"

REGISTER = {"001": "Bank", "012": "Zahlungsinstitut", "016": "E-Geld-Institut"}
FUSIONS_ARTEN = {"INCORPORAZIONE", "FUSIONE", "CESSIONE ATTIVITA/PASSIVITA"}
PRODUKTE = {"VFLUSSO_INTERMEDIARIO": "INTERMEDIARI", "VFLUSSO_SEDE_BANCHE": "SUCCURSALI",
            "VFLUSSO_EVENTO": "EVENTI"}

SPALTEN = ["Bankleitzahl", "BIC", "Weitere BICs", "Bankenname", "Register", "Rechtsform", "Steuernummer",
           "Registernummer", "Eingetragen seit", "Straße", "PLZ", "Ort", "Land"]
FILIAL_SPALTEN = ["Bankleitzahl", "CAB", "Art", "Straße", "PLZ", "Ort", "Ortsteil", "Land", "Eröffnet"]


# ---------------------------------------------------------------- Download Banca d'Italia

def _bdi_herunterladen() -> dict[str, bytes]:
    """Lädt die drei Produkte aus dem Download-Bereich -> {INTERMEDIARI|SUCCURSALI|EVENTI: zip-Bytes}."""
    ng = GIAVA + "/ng/"
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    kopf = {"Accept": "application/json, text/plain, */*", "Referer": ng, "User-Agent": "bic-verzeichnis-update"}

    def holen(url: str, timeout: int = 300) -> bytes:
        with op.open(urllib.request.Request(url, headers=kopf), timeout=timeout) as r:
            return r.read()

    holen(ng)  # Sitzung und Cookies (automatische Weiterleitung über auth.bancaditalia.it)
    liste = json.loads(holen(f"{ng}api/areaDown?languageId=it&refDate={int(time.time() * 1000)}"))
    produkte = {p["productName"]: p for p in liste}
    ergebnis = {}
    for name, kurz in PRODUKTE.items():
        p = produkte.get(name)
        if not p or not p.get("xml_size"):
            raise RuntimeError(f"Produkt {name} fehlt im Download-Bereich der Banca d'Italia")
        pruef = json.loads(holen(f"{ng}api/checkAreaDownloadElements?" + urllib.parse.urlencode(
            {"exportType": "XML", "exportProduct": name, "strReferenceDate": p["strReferenceDate"]})))
        if pruef.get("code") != "AREADOWNLOAD_OK":
            raise RuntimeError(f"Download von {name} nicht freigegeben: {pruef.get('code')}")
        ergebnis[kurz] = holen(f"{GIAVA}/getAreaDownloadExport.do?" + urllib.parse.urlencode({
            "referenceDate": p["strReferenceDate"], "product": name, "language": "it", "exportType": "XML",
            "username": "OBLIXANONYMOUS", "isCompressed": p.get("isCompressed", "S")}))
        print(f"[{CODE}] {name} vom {p['strReferenceDate']}: {len(ergebnis[kurz]) // 1024} KB")
    return ergebnis


def _zeilen(zip_bytes: bytes):
    """Liest die ROW-Elemente des XML im ZIP als dicts, ohne die (bis zu 200 MB große) Datei ganz zu laden."""
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    name = next(n for n in z.namelist() if n.lower().endswith(".xml"))
    with z.open(name) as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == "ROW":
                yield {c.tag: (c.text or "").strip() for c in el}
                el.clear()


def _stichtag(zip_bytes: bytes) -> str:
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    name = next(n for n in z.namelist() if n.lower().endswith(".xml"))
    with z.open(name) as f:
        for ev, el in ET.iterparse(f, events=("start",)):
            return el.get("DATERIF", "")
    return ""


# ---------------------------------------------------------------- BICs über GLEIF

def _ort_rang(bic: str) -> int:
    # 2. Zeichen des Ortscodes: 0 = Test-BIC, 1 = passiv, 2 = Reverse Billing; sonst voll verbunden
    return {"0": 0, "1": 1, "2": 2}.get(bic[7:8], 3)


def _gleif_bics() -> tuple[dict[str, list[str]], str]:
    """({Steuernummer ohne führende Nullen: [BICs]} für aktive italienische LEIs, Stand der Tabelle JJJJ-MM)."""
    def holen(url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": "bic-verzeichnis-update", "Accept": "application/vnd.api+json"})
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.read()

    dateien = json.loads(holen(GLEIF_MAPPING))["data"]
    neueste = max((d for d in dateien if d["attributes"]["valid"]), key=lambda d: d["attributes"]["uploadedAt"])
    z = zipfile.ZipFile(io.BytesIO(holen(neueste["attributes"]["downloadLink"])))
    name = next(n for n in z.namelist() if n.endswith(".csv"))
    with z.open(name) as f:
        zuordnung = {r["BIC"].strip().upper(): r["LEI"].strip()
                     for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")) if r["BIC"][4:6].upper() == "IT"}
    leis = sorted(set(zuordnung.values()))
    entitaeten = {}
    for i in range(0, len(leis), 100):
        q = urllib.parse.urlencode({"filter[lei]": ",".join(leis[i:i + 100]), "page[size]": 100})
        for d in json.loads(holen(f"{GLEIF_LEI}?{q}"))["data"]:
            entitaeten[d["id"]] = d["attributes"]["entity"]
    bics = defaultdict(list)
    for bic, lei in sorted(zuordnung.items()):
        e = entitaeten.get(lei)
        if e and e.get("status") == "ACTIVE" and e.get("registeredAs"):
            bics[e["registeredAs"].strip().lstrip("0")].append(bic)
    print(f"[{CODE}] GLEIF {neueste['attributes'].get('fileName', '')}: {len(zuordnung)} italienische BICs, "
          f"{len(bics)} Steuernummern")
    m = re.search(r"(\d{4})(\d{2})\d{2}", neueste["attributes"].get("fileName", "")) \
        or re.search(r"(\d{4})-(\d{2})", neueste["attributes"].get("uploadedAt", ""))
    return bics, f"{m.group(1)}-{m.group(2)}" if m else ""


def _bic_wahl(bics: list[str]) -> tuple[str, list[str]]:
    """Haupt-BIC (voll verbunden, bevorzugt Hauptsitz …XXX) und die übrigen."""
    if not bics:
        return "", []
    haupt = max(bics, key=lambda b: (_ort_rang(b), b.endswith("XXX"), -len(b)))
    return haupt, sorted(b for b in bics if b != haupt)


# ---------------------------------------------------------------- Laden

def _gilt(z: dict, heute: str) -> bool:
    return (z.get("DATA_I_VAL") or "0000") <= heute and (not z.get("DATA_F_VAL") or z["DATA_F_VAL"] > heute)


def laden(args, alte_meta: dict) -> Stand:
    heute = args.today.isoformat()
    if args.input:  # lokale ZIP-Dateien, erkannt am Dateinamen
        dateien = {}
        for p in args.input:
            for kurz in PRODUKTE.values():
                if kurz in Path(p).name.upper():
                    dateien[kurz] = Path(p).read_bytes()
        fehlend = set(PRODUKTE.values()) - set(dateien)
        if fehlend:
            raise RuntimeError(f"--input: es fehlen Dateien für {sorted(fehlend)}")
    else:
        dateien = _bdi_herunterladen()

    # Institute
    banken: dict[str, dict] = {}
    for z in _zeilen(dateien["INTERMEDIARI"]):
        abi = z.get("COD_MECC", "")
        if (z.get("TIPO_ALBO") not in REGISTER or not abi or not _gilt(z, heute)
                or (z.get("DATA_CAN_ALBO") and z["DATA_CAN_ALBO"] <= heute)):
            continue
        im_ausland = bool(z.get("DES_STATO_CM_SL"))
        banken[abi] = {
            "Bankleitzahl": abi, "BIC": "", "Weitere BICs": "", "Bankenname": z.get("DEN_INT", ""),
            "Register": REGISTER[z["TIPO_ALBO"]], "Rechtsform": z.get("DES_CLASSIF", ""),
            "Steuernummer": z.get("COD_FISCALE", ""), "Registernummer": z.get("MATR_ISC_ALBO", ""),
            "Eingetragen seit": z.get("DATA_ISC_ALBO", ""),
            "Straße": z.get("INDIRIZZO_CM_SL" if im_ausland else "INDIRIZZO_SL", ""),
            "PLZ": "" if im_ausland else z.get("CAP_SL", ""),
            "Ort": z.get("DES_LOC_ESTERA_CM_SL" if im_ausland else "DES_COM_ITA_SL", ""),
            "Land": z.get("DES_STATO_CM_SL", "") if im_ausland else "ITALIA",
        }
    if not banken:
        raise RuntimeError("keine aktiven Institute in der Lista intermediari gefunden")

    # BICs über GLEIF (bei Ausfall: letzter Stand)
    try:
        nach_steuer, tabelle = _gleif_bics()
    except Exception as e:
        print(f"[{CODE}] Warnung: GLEIF nicht erreichbar ({e}) – BICs des letzten Stands werden verwendet")
        alt = {z[SCHLUESSEL]: z for z in kern.csv_lesen(kern.daten_ordner(sys.modules[__name__]) / "bankleitzahlen.csv")[1]}
        nach_steuer, tabelle = None, alte_meta.get("GLEIF-Tabelle", "")
    for abi, z in banken.items():
        if nach_steuer is None:
            z["BIC"], z["Weitere BICs"] = alt.get(abi, {}).get("BIC", ""), alt.get(abi, {}).get("Weitere BICs", "")
        else:
            haupt, weitere = _bic_wahl(nach_steuer.get(z["Steuernummer"].lstrip("0"), []))
            z["BIC"], z["Weitere BICs"] = haupt, " ".join(weitere)

    # Filialen
    filialen = []
    for z in _zeilen(dateien["SUCCURSALI"]):
        abi = z.get("COD_MECC", "")
        if abi not in banken or not _gilt(z, heute) or (z.get("DATA_F_OPER") and z["DATA_F_OPER"] <= heute):
            continue
        cab = z.get("CAB_SEDE", "")
        filialen.append({
            "Bankleitzahl": abi, "CAB": cab.zfill(5) if cab and cab != "0" else "",
            "Art": (z.get("DES_TIPO_SEDE") or "").capitalize(), "Straße": z.get("INDIRIZZO", ""),
            "PLZ": z.get("CAP", ""), "Ort": z.get("DES_COM_ITA") or z.get("DES_LOC_ESTERA", ""),
            "Ortsteil": z.get("FRAZIONE", ""), "Land": z.get("DES_STATO", ""), "Eröffnet": z.get("DATA_I_OPER", ""),
        })
    # je Bank nach CAB; Filialen ohne CAB (meist im Ausland) ans Ende
    filialen.sort(key=lambda f: (f["Bankleitzahl"].zfill(5), not f["CAB"], f["CAB"], f["Ort"], f["Straße"]))

    # Übernahmen/Fusionen: übernommene ABI -> neue ABI (jeweils das jüngste Ereignis)
    fusionen: dict[str, dict] = {}
    for z in _zeilen(dateien["EVENTI"]):
        alt_abi, neu_abi = z.get("COD_MECC_INT_PAS", ""), z.get("COD_MECC_INT_ATT", "")
        if z.get("DES_TIPO_EVENTO") not in FUSIONS_ARTEN or not alt_abi or not neu_abi or alt_abi == neu_abi:
            continue
        if alt_abi not in fusionen or z.get("DATA_EFFICACIA", "") >= fusionen[alt_abi]["Datum"]:
            fusionen[alt_abi] = {"Bankleitzahl": alt_abi, "Nachfolge-Bankleitzahl": neu_abi,
                                 "Datum": z.get("DATA_EFFICACIA", ""), "Art": z.get("DES_TIPO_EVENTO", "").capitalize(),
                                 "Name": z.get("DEN_INT_PAS", "")}

    stichtag = _stichtag(dateien["INTERMEDIARI"])
    mit_bic = sum(1 for z in banken.values() if z["BIC"])
    print(f"[{CODE}] Stand {stichtag}: {len(banken)} Institute ({mit_bic} mit BIC über GLEIF), "
          f"{len(filialen)} Filialen, {len(fusionen)} frühere ABI-Codes mit Nachfolger")
    # Kein Stichtag in meta.json: er ändert sich täglich und würde sonst jeden Tag einen Commit auslösen.
    meta = {"Quelle": SEITE, "GLEIF-Tabelle": tabelle, "Fusionen": sorted(fusionen.values(), key=lambda f: f["Bankleitzahl"].zfill(5))}
    return Stand(spalten=SPALTEN, banken=sorted(banken.values(), key=lambda z: z[SCHLUESSEL].zfill(5)),
                 datum=heute, filialen=filialen, filial_spalten=FILIAL_SPALTEN, meta=meta,
                 dateien={"HINWEIS-BIC.txt": (
                     "Die BICs in bankleitzahlen.csv (Spalten BIC und Weitere BICs) stammen aus der BIC/LEI-Zuordnung\n"
                     "von SWIFT und GLEIF. Für sie gilt:\n\n" + swift_hinweis(tabelle) + "\n\nLizenz: " + GLEIF_LIZENZ +
                     "\n\nAlle übrigen Angaben: " + QUELLE["hinweis"] + "\n").encode("utf-8")})


# ---------------------------------------------------------------- API

def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    g = z.get
    return {
        "land": CODE,
        "bankleitzahl": leer(g("Bankleitzahl")),
        "bic": leer(g("BIC")),
        "name": leer(g("Bankenname")),
        "status": None,
        "entfernt_am": None,
        "bic_quelle": "GLEIF" if leer(g("BIC")) else None,
        "weitere_bics": (g("Weitere BICs") or "").split(),
        "register": leer(g("Register")),
        "rechtsform": leer(g("Rechtsform")),
        "steuernummer": leer(g("Steuernummer")),
        "registernummer": leer(g("Registernummer")),
        "eingetragen_seit": leer(g("Eingetragen seit")),
        "nachfolge_bankleitzahl": None,
        "adresse": {"strasse": leer(g("Straße")), "plz": leer(g("PLZ")), "ort": leer(g("Ort")), "land": leer(g("Land"))},
        "filialen": [
            {"cab": leer(f.get("CAB")), "art": leer(f.get("Art")), "strasse": leer(f.get("Straße")),
             "plz": leer(f.get("PLZ")), "ort": leer(f.get("Ort")), "ortsteil": leer(f.get("Ortsteil")),
             "land": leer(f.get("Land")), "eroeffnet": leer(f.get("Eröffnet"))}
            for f in filialen
        ],
    }


def _endziel(abi: str, nachfolger: dict[str, str], aktiv: set[str]) -> str:
    """Folgt einer Kette von Übernahmen bis zur heute aktiven ABI (oder bis zum letzten bekannten Glied)."""
    gesehen = {abi}
    while abi not in aktiv and abi in nachfolger and nachfolger[abi] not in gesehen:
        abi = nachfolger[abi]
        gesehen.add(abi)
    return abi


def zusatz_eintraege(eintraege: dict[str, dict], meta: dict) -> dict[str, dict]:
    """Frühere ABI-Codes aus der Fusionsliste: Verweis auf den (heute aktiven) Nachfolger."""
    nachfolger = {f["Bankleitzahl"]: f["Nachfolge-Bankleitzahl"] for f in meta.get("Fusionen", [])}
    aktiv = {k for k, e in eintraege.items() if e["status"] == "aktiv"}
    extra = {}
    for f in meta.get("Fusionen", []):
        alt = f["Bankleitzahl"]
        ziel = _endziel(alt, nachfolger, aktiv)
        if alt in eintraege:  # schon als entfernt protokolliert: Nachfolger ergänzen
            if eintraege[alt]["status"] == "entfernt" and not eintraege[alt].get("nachfolge_bankleitzahl"):
                eintraege[alt]["nachfolge_bankleitzahl"] = ziel
            continue
        extra[alt] = {
            "land": CODE, "bankleitzahl": alt, "bic": None, "name": f.get("Name") or None,
            "status": "entfernt", "entfernt_am": f.get("Datum") or None, "bic_quelle": None, "weitere_bics": [],
            "register": None, "rechtsform": None, "steuernummer": None, "registernummer": None,
            "eingetragen_seit": None, "nachfolge_bankleitzahl": ziel,
            "adresse": {"strasse": None, "plz": None, "ort": None, "land": None}, "filialen": [],
        }
    return extra


# ---------------------------------------------------------------- Webseite

WEB = {
    "suche_platzhalter": "ABI, CAB, BIC, Bankname oder Ort …",
    "suche": ["bankleitzahl", "bic", "name", "adresse.plz", "adresse.ort", "steuernummer"],
    "suche_listen": ["weitere_bics"],
    "filial_suche": ["cab", "strasse", "plz", "ort", "ortsteil"],
    "filial_spalten": [["CAB", "cab", "mono"], ["Ort", "plz_ort"], ["Adresse", "strasse"]],
    "filter": [{"feld": "register", "alle": "Alle Arten"}],
    "spalte5": {"titel": "Filialen", "feld": "filialen", "art": "anzahl"},
    "aenderung_name": "Bankenname",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Täglicher Vergleich mit dem Vortag (Register der Banca d'Italia). Frühere ABI-Codes "
                           "aus Übernahmen und Fusionen lassen sich über die Suche finden, wenn man sie genau eingibt.",
    "details": [
        ["ABI (Bankleitzahl)", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"],
        ["BIC-Quelle", "bic_quelle"], ["Weitere BICs", "weitere_bics", "liste"],
        ["Nachfolge-ABI", "nachfolge_bankleitzahl", "blz"],
        ["Art", "register"], ["Rechtsform", "rechtsform"], ["Steuernummer", "steuernummer"],
        ["Registernummer", "registernummer"], ["Eingetragen seit", "eingetragen_seit", "datum"],
        ["Sitz", "adresse", "adresse"], ["Land", "adresse.land"],
    ],
}


def stand_text(meta: dict) -> str:
    return "BICs über GLEIF ergänzt"


def zusatz_hinweis(meta: dict) -> str:
    return swift_hinweis(meta.get("GLEIF-Tabelle"))
