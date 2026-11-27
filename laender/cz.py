"""Tschechien – Číselník kódů platebního styku der Tschechischen Nationalbank (ČNB).

- Angeboten werden nur PDF und CSV (UTF-8, Semikolon), kein XML oder JSON.
- Die ČNB stellt die gültige und meist schon die nächste Fassung bereit („Číselník 255 platný od …“,
  „Číselník 256 platný od …“). Nummer und Gültigkeitsdatum stehen nur auf der Seite, nicht in der
  Datei. Das Skript liest beides von der Seite und nimmt die Fassung, die heute gilt.
- Der Kód platebního styku ist vierstellig und steht in der IBAN an den Stellen 5–8.
- Systém CERTIS: „A“ = Teilnehmer am tschechischen Clearing-System CERTIS.
"""

from __future__ import annotations

import csv
import datetime as dt
import html
import io
import re
import urllib.parse

from kern import SCHLUESSEL, Stand, herunterladen, leer

CODE = "CZ"
NAME = "Tschechien"
BLZ_STELLEN = None
SEITE = "https://www.cnb.cz/cs/platebni-styk/ucty-kody-bank/"
QUELLE = {
    "name": "Česká národní banka – Číselník kódů platebního styku",
    "kurz": "ČNB",
    "url": SEITE,
    "bedingungen": "https://www.cnb.cz/en/privacy-statement-and-disclaimer/disclaimer-copyright/",
    # Bedingungen: „The CNB must always be stated as the source of the information (Source: the CNB),
    # the file and its content may not be altered in any manner“
    "hinweis": "Source: the CNB (Zdroj: ČNB) – Číselník kódů platebního styku. Inhalt unverändert übernommen, "
               "nur umformatiert; die Originaldatei der ČNB liegt unverändert bei.",
}
ORIGINAL = "original-cnb.csv"
SPALTEN = ["Bankleitzahl", "BIC", "Bankenname", "CERTIS"]
_SPALTEN_QUELLE = {"Kód platebního styku": "Bankleitzahl", "BIC kód (SWIFT)": "BIC",
                   "Poskytovatel platebních služeb": "Bankenname", "Systém CERTIS": "CERTIS"}


def _fassungen(seite: str) -> list[dict]:
    """[{nummer, gueltig_ab, url}] aus der ČNB-Seite (ohne auskommentierte Bereiche)."""
    seite = re.sub(r"(?s)<!--.*?-->", "", seite)
    ergebnis = []
    for m in re.finditer(r'href="([^"]+\.csv)"', seite):
        url = urllib.parse.urljoin(SEITE, html.unescape(m.group(1)))
        if urllib.parse.urlparse(url).netloc != "www.cnb.cz":
            continue
        davor = re.sub(r"<[^>]+>", " ", seite[max(0, m.start() - 1500):m.start()])
        nummer = re.findall(r"Číselník\s+(\d+)", davor)
        ab = re.findall(r"platný od\s+(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})", davor)
        if not ab:
            continue
        d, mo, j = ab[-1]
        ergebnis.append({"nummer": nummer[-1] if nummer else "", "gueltig_ab": dt.date(int(j), int(mo), int(d)), "url": url})
    if not ergebnis:
        raise RuntimeError("keine CSV-Fassung mit Gültigkeitsdatum auf der ČNB-Seite gefunden – Seite geändert?")
    return ergebnis


def _csv_lesen(roh: bytes) -> list[dict[str, str]]:
    text = roh.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    fehlend = [k for k in _SPALTEN_QUELLE if k not in (reader.fieldnames or [])]
    if fehlend:
        raise RuntimeError(f"Spalten fehlen in der ČNB-CSV: {fehlend}")
    banken = []
    for r in reader:
        z = {ziel: (r.get(quelle) or "").strip() for quelle, ziel in _SPALTEN_QUELLE.items()}
        if z[SCHLUESSEL]:
            banken.append(z)
    return sorted(banken, key=lambda z: z[SCHLUESSEL])


def laden(args, alte_meta: dict) -> Stand:
    if args.input:  # lokale Datei: gilt ab --today
        fassung = {"nummer": "lokal", "gueltig_ab": args.today, "url": str(args.input[0])}
        roh = args.input[0].read_bytes()
    else:
        fassungen = _fassungen(herunterladen(SEITE).decode("utf-8", "replace"))
        for f in fassungen:
            print(f"[{CODE}] Číselník {f['nummer']}: gültig ab {f['gueltig_ab']}")
        gueltig = [f for f in fassungen if f["gueltig_ab"] <= args.today]
        if not gueltig:
            raise RuntimeError("keine der ČNB-Fassungen ist heute gültig")
        fassung = max(gueltig, key=lambda f: f["gueltig_ab"])
        roh = herunterladen(fassung["url"])
    banken = _csv_lesen(roh)
    ab = fassung["gueltig_ab"].isoformat()
    print(f"[{CODE}] Verwendet: Číselník {fassung['nummer']} ({len(banken)} Einträge)")
    meta = {"Číselník": fassung["nummer"], "ValidFrom": ab, "Quelle": SEITE}
    datum = ab if alte_meta.get("ValidFrom") != ab else args.today.isoformat()
    return Stand(spalten=SPALTEN, banken=banken, datum=datum, meta=meta, dateien={ORIGINAL: roh})


def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    return {
        "land": CODE,
        "bankleitzahl": leer(z.get("Bankleitzahl")),
        "bic": leer(z.get("BIC")),
        "name": leer(z.get("Bankenname")),
        "status": None,
        "entfernt_am": None,
        "certis": z.get("CERTIS", "").strip() == "A",
        "gueltig_ab": meta.get("ValidFrom"),
    }


WEB = {
    "suche_platzhalter": "Bankleitzahl (Kód banky), BIC oder Bankname …",
    "suche": ["bankleitzahl", "bic", "name"],
    "filter": [],
    "spalte5": {"titel": "CERTIS", "feld": "certis", "art": "ja_nein"},
    "aenderung_name": "Bankenname",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Die ČNB gibt neue Fassungen des Číselník mit Gültigkeitsdatum heraus. Änderungen "
                           "stehen unter dem Tag, ab dem sie gelten.",
    "details": [
        ["Bankleitzahl", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"],
        ["CERTIS", "certis", "ja:Teilnehmer am tschechischen Clearing (CERTIS)"],
    ],
}


def stand_text(meta: dict) -> str:
    if not meta.get("ValidFrom"):
        return ""
    return f"Číselník {meta.get('Číselník', '')} gültig ab {'.'.join(reversed(meta['ValidFrom'].split('-')))}"
