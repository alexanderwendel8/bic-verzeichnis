"""Deutschland – Bankleitzahlendatei der Deutschen Bundesbank.

- Gelesen wird die XML-Fassung: nur sie nennt im Dateikopf ValidFrom/ValidTill.
- Die Bundesbank stellt die gültige und (etwa einen Monat vorher) die nächste Datei bereit;
  genommen wird die, die heute gilt. Die Links werden jedes Mal von der Download-Seite gelesen.
- Je Bankleitzahl genau ein Haupteintrag (Merkmal „1“), nur dessen BIC gilt für Zahlungen.
  Zusatzeinträge (Merkmal „2“) sind weitere Orte derselben Bankleitzahl → Filialen.
- Änderungskennzeichen „D“ = gelöscht zum Gültigkeitstag. Das Kennzeichen selbst wird nicht
  abgelegt, sonst erschiene jedes Quartal fast jeder Eintrag als „geändert“.
- Die Bankleitzahl ist achtstellig (IBAN-Stellen 5–12).
"""

from __future__ import annotations

import datetime as dt
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET

from kern import SCHLUESSEL, Stand, herunterladen, leer

CODE = "DE"
NAME = "Deutschland"
BLZ_STELLEN = None
SEITE = ("https://www.bundesbank.de/de/aufgaben/unbarer-zahlungsverkehr/"
         "serviceangebot/bankleitzahlen/download-bankleitzahlen-602592")
QUELLE = {
    "name": "Deutsche Bundesbank – Bankleitzahlendatei",
    "kurz": "Deutscher Bundesbank",
    "url": SEITE,
    "bedingungen": "https://www.bundesbank.de/de/startseite/impressum",
    "hinweis": "Quelle: Deutsche Bundesbank, Bankleitzahlendatei (von der Bundesbank unverbindlich bereitgestellt). "
               "Übernommen werden die Haupteinträge je Bankleitzahl, Zusatzeinträge als Filialen.",
}
NS = "{urn:BBk:BLZ:xsd:BLZDat}"

BANK_FELDER = {
    "BLZ": "Bankleitzahl", "BIC": "BIC", "Bezeichnung": "Bezeichnung", "Kurzbez": "Kurzbezeichnung",
    "PLZ": "PLZ", "Ort": "Ort", "PAN": "PAN", "PruefZiffMeth": "Prüfzifferberechnungsmethode",
    "DsNr": "Datensatznummer", "BLZLoesch": "Bankleitzahllöschung", "NachfolgeBLZ": "Nachfolge-Bankleitzahl",
}
FILIAL_FELDER = {
    "BLZ": "Bankleitzahl", "Bezeichnung": "Bezeichnung", "Kurzbez": "Kurzbezeichnung",
    "PLZ": "PLZ", "Ort": "Ort", "BIC": "BIC", "PAN": "PAN", "DsNr": "Datensatznummer",
}


def _xml_links(seite: str) -> list[str]:
    links = re.findall(r'href="([^"]+-xml-data\.xml)"', seite)
    links = [urllib.parse.urljoin(SEITE, html.unescape(l)) for l in dict.fromkeys(links)]
    if not links:
        raise RuntimeError("keine XML-Links auf der Bundesbank-Seite gefunden – Seite geändert?")
    return links


def _xml_lesen(roh: bytes):
    root = ET.fromstring(roh)
    if root.tag != NS + "Document":
        raise RuntimeError(f"unerwartetes XML-Format ({root.tag})")
    kopf = {c.tag.replace(NS, ""): (c.text or "").strip() for c in root.find(NS + "FileHdr")}
    for k in ("ValidFrom", "ValidTill", "FileRef"):
        if not kopf.get(k):
            raise RuntimeError(f"Dateikopf ohne {k}")
    eintraege = [{c.tag.replace(NS, ""): (c.text or "").strip() for c in e} for e in root.findall(NS + "BLZEintrag")]
    return kopf, eintraege


def laden(args, alte_meta: dict) -> Stand:
    if args.input:
        roh = [p.read_bytes() for p in args.input]
    else:
        roh = [herunterladen(u) for u in _xml_links(herunterladen(SEITE).decode("utf-8", "replace"))]
    dateien = [_xml_lesen(r) for r in roh]
    for kopf, e in dateien:
        print(f"[{CODE}] Bundesbank-Datei {kopf['FileRef']}: gültig {kopf['ValidFrom']} bis {kopf['ValidTill']}, {len(e)} Datensätze")

    heute = args.today
    d = dt.date.fromisoformat
    gueltig = [f for f in dateien if d(f[0]["ValidFrom"]) <= heute <= d(f[0]["ValidTill"])]
    gueltig = gueltig or [f for f in dateien if d(f[0]["ValidFrom"]) <= heute]  # Lücke: zuletzt gültig gewordene
    if not gueltig:
        raise RuntimeError("keine der Bundesbank-Dateien ist heute gültig")
    kopf, eintraege = max(gueltig, key=lambda f: f[0]["ValidFrom"])
    print(f"[{CODE}] Verwendet: {kopf['FileRef']}")

    banken, entfernt, filialen = [], [], []
    for e in eintraege:
        if e.get("Merkmal") == "1":
            z = {spalte: e.get(tag, "") for tag, spalte in BANK_FELDER.items()}
            (entfernt if e.get("Aenderungskennz") == "D" else banken).append(z)
        elif e.get("Merkmal") == "2" and e.get("Aenderungskennz") != "D":
            filialen.append({spalte: e.get(tag, "") for tag, spalte in FILIAL_FELDER.items()})
    banken.sort(key=lambda z: z[SCHLUESSEL])
    entfernt.sort(key=lambda z: z[SCHLUESSEL])
    filialen.sort(key=lambda z: (z[SCHLUESSEL], z["Ort"], z["PLZ"], z["Datensatznummer"].zfill(10)))

    meta = {k: kopf[k] for k in ("FileRef", "FileCreDt", "ValidFrom", "ValidTill") if k in kopf}
    meta["Quelle"] = SEITE
    # Wechsel der Quelldatei -> Änderungen zum Gültigkeitstag, sonst (Korrektur) zum heutigen Tag
    datum = kopf["ValidFrom"] if alte_meta.get("ValidFrom") != kopf["ValidFrom"] else heute.isoformat()
    return Stand(spalten=list(BANK_FELDER.values()), banken=banken, datum=datum,
                 filialen=filialen, filial_spalten=list(FILIAL_FELDER.values()), meta=meta, entfernt=entfernt)


# ---------------------------------------------------------------- API

def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    g = z.get
    nachfolger = leer(g("Nachfolge-Bankleitzahl"))
    return {
        "land": CODE,
        "bankleitzahl": leer(g("Bankleitzahl")),
        "bic": leer(g("BIC")),
        "name": leer(g("Bezeichnung")),
        "kurzbezeichnung": leer(g("Kurzbezeichnung")),
        "status": None,
        "entfernt_am": None,
        "loeschung_angekuendigt": (g("Bankleitzahllöschung") == "1") and not entfernt,
        "nachfolge_bankleitzahl": None if nachfolger in (None, "00000000") else nachfolger,
        "adresse": {"plz": leer(g("PLZ")), "ort": leer(g("Ort"))},
        "pan": leer(g("PAN")),
        "pruefziffermethode": leer(g("Prüfzifferberechnungsmethode")),
        "datensatznummer": leer(g("Datensatznummer")),
        "gueltig_ab": meta.get("ValidFrom"),
        "gueltig_bis": meta.get("ValidTill"),
        "filialen": [
            {"name": leer(f.get("Bezeichnung")), "plz": leer(f.get("PLZ")), "ort": leer(f.get("Ort")),
             "bic": leer(f.get("BIC")), "pan": leer(f.get("PAN"))}
            for f in filialen
        ],
    }


# ---------------------------------------------------------------- Webseite

WEB = {
    "suche_platzhalter": "Bankleitzahl, BIC (auch Filial-BIC), Bankname oder Ort …",
    "suche": ["bankleitzahl", "bic", "name", "kurzbezeichnung", "adresse.plz", "adresse.ort"],
    "filter": [],
    "spalte5": {"titel": "Filialen", "feld": "filialen", "art": "anzahl"},
    "aenderung_name": "Bezeichnung",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Die Bundesbank aktualisiert die Bankleitzahlendatei viermal im Jahr (März, Juni, "
                           "September, Dezember). Änderungen stehen unter dem Tag, ab dem sie gelten. Gelöschte "
                           "Bankleitzahlen bleiben mit ihrem letzten Stand erhalten.",
    "details": [
        ["Bankleitzahl", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"],
        ["Kurzbezeichnung", "kurzbezeichnung"], ["Ort", "adresse", "adresse"],
        ["Löschung", "loeschung_angekuendigt", "ja:angekündigt – Bankleitzahl wird künftig gelöscht"],
        ["Nachfolge-BLZ", "nachfolge_bankleitzahl", "blz"],
        ["Prüfziffermethode", "pruefziffermethode"], ["Kartennummer (PAN)", "pan"],
        ["Datensatznummer", "datensatznummer"],
    ],
}


def stand_text(meta: dict) -> str:
    if not meta.get("ValidFrom"):
        return ""
    f = lambda s: ".".join(reversed(s.split("-")))
    return f"Bundesbank-Datei gültig {f(meta['ValidFrom'])}–{f(meta['ValidTill'])}"
