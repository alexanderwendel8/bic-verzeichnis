"""Rumänien – Teilnehmer am Großbetragszahlungssystem ReGIS der Banca Națională a României (BNR).

- Die BNR veröffentlicht die Teilnehmer nur als PDF; der Dateiname ist eine Nummer und kann sich ändern. Die
  Seite lädt ihren Inhalt nachträglich: Der Link steht in der Antwort auf POST https://www.bnr.ro//blocks.
  Gelesen wird die PDF ohne Zusatzbibliothek (laender/_pdf.py).
- Laut BNR sind die IBAN-Stellen 5–8 „primele patru caractere ale codului BIC atribuit instituției“: Der
  Bankcode sind die ersten vier Zeichen des BIC. Übernommen werden die Abschnitte I (Kreditinstitute),
  II (Staatskasse) und III (BNR); Hilfssysteme und Kartensysteme (Abschnitt IV) haben keine Konten mit IBAN.
- Ein Teil der Anfragen an bnr.ro bekommt statt der Antwort eine kurze Fehlerseite („This page can't be
  displayed“); das Skript erkennt sie und versucht es bis zu zehnmal.
- Bedingungen der BNR: Weitergabe in jeder Form erlaubt, wenn die Quelle genannt wird; Änderungen sind
  ausdrücklich zu kennzeichnen. Die Originaldatei liegt unverändert bei.
"""

from __future__ import annotations

import html
import re
import time
import urllib.parse
import urllib.request

from kern import SCHLUESSEL, Stand, leer
from laender import _pdf

CODE = "RO"
NAME = "Rumänien"
BLZ_STELLEN = None
SEITE = "https://www.bnr.ro/2153-regis"
BLOCKS = "https://www.bnr.ro//blocks"
QUELLE = {
    "name": "Banca Națională a României – Participanți ReGIS",
    "kurz": "BNR",
    "url": SEITE,
    # „Redistribuirea sub orice formă şi prin orice mijloace a conţinutului informațional este permisă numai cu
    # indicarea sursei. În cazul alterării informației preluate din website, acest lucru trebuie menţionat explicit.“
    "bedingungen": "https://www.bnr.ro/2281-termeni-si-conditii",
    "hinweis": "Sursa: Banca Națională a României – Participanți ReGIS. Geändert: aus der PDF in eine Tabelle "
               "übertragen, nur Kreditinstitute, Staatskasse und BNR; Bankcode = erste vier Zeichen des BIC (so "
               "beschreibt es die BNR für die IBAN). Die Originaldatei der BNR liegt unverändert bei.",
}
ORIGINAL = "original-bnr.pdf"
SPALTEN = ["Bankleitzahl", "BIC", "Bankenname", "Art"]
_ABSCHNITTE = {"I": "Kreditinstitut", "II": "Staatskasse", "III": "Zentralbank"}


def _holen(url: str, daten: bytes | None = None, erwartet: str = "") -> bytes:
    """Lädt mit Wiederholung; erkennt die kurze Fehlerseite von bnr.ro."""
    letzter = None
    for versuch in range(10):
        req = urllib.request.Request(url, data=daten, headers={"User-Agent": "bic-verzeichnis-update"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                inhalt, typ = r.read(), r.headers.get("Content-Type", "")
            if (not erwartet or erwartet in typ) and b"This page can't be displayed" not in inhalt[:2000]:
                return inhalt
            letzter = f"Fehlerseite ({typ}, {len(inhalt)} Bytes)"
        except Exception as e:
            letzter = str(e)
        time.sleep(3 + 2 * versuch)
    raise RuntimeError(f"bnr.ro nicht erreichbar: {letzter}")


def _pdf_links() -> list[str]:
    antwort = _holen(BLOCKS, urllib.parse.urlencode({"bid": 3150, "currentSlug": "2153-regis", "cat_id": ""}).encode(),
                     erwartet="html").decode("utf-8", "replace")
    links = []
    for href, text in re.findall(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>(.*?)</a>', antwort, re.S):
        if re.search(r"particip", re.sub(r"<[^>]+>", "", text), re.I):
            links.append(urllib.parse.urljoin(SEITE, html.unescape(href)))
    if not links:
        raise RuntimeError("kein Link zur Teilnehmerliste auf der ReGIS-Seite gefunden – Seite geändert?")
    return list(dict.fromkeys(links))


def eintraege_lesen(pdf: bytes) -> list[dict]:
    banken, art = [], None
    for z in _pdf.zeilen(pdf):
        m = re.match(r"^(I{1,3}|IV|V)\.\s+(.*)$", z)
        if m:
            art = _ABSCHNITTE.get(m.group(1))
            z = m.group(2)
            if art is None:
                break  # Abschnitt IV: Hilfssysteme und Kartensysteme
        m = re.match(r"^(.*?)\s*\b([A-Z]{4}RO[A-Z0-9]{2}(?:[A-Z0-9]{3})?)$", z)
        if art and m and m.group(1):
            bic = m.group(2)
            banken.append({"Bankleitzahl": bic[:4], "BIC": bic, "Bankenname": m.group(1).strip(" -"), "Art": art})
    return banken


def laden(args, alte_meta: dict) -> Stand:
    if args.input:
        roh = args.input[0].read_bytes()
    else:
        roh = None
        for url in _pdf_links():
            try:
                roh = _holen(url, erwartet="pdf")
                break
            except RuntimeError as e:
                print(f"[{CODE}] {url}: {e}")
        if roh is None:
            raise RuntimeError("Teilnehmerliste der BNR nicht ladbar")
    banken = eintraege_lesen(roh)
    if len(banken) < 10:
        raise RuntimeError(f"nur {len(banken)} Teilnehmer aus der PDF gelesen – Format geändert?")
    codes = {}
    for b in banken:
        if b[SCHLUESSEL] in codes:
            raise RuntimeError(f"Bankcode {b[SCHLUESSEL]} mehrfach in der ReGIS-Liste")
        codes[b[SCHLUESSEL]] = b
    print(f"[{CODE}] ReGIS-Teilnehmer: {len(codes)} Bankcodes")
    return Stand(spalten=SPALTEN, banken=sorted(codes.values(), key=lambda z: z[SCHLUESSEL]),
                 datum=args.today.isoformat(), meta={"Quelle": SEITE}, dateien={ORIGINAL: roh})


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
        "art": g("Art"),
    }


# ---------------------------------------------------------------- Webseite

WEB = {
    "suche_platzhalter": "Bankcode (4 Buchstaben), BIC oder Name …",
    "suche": ["bankleitzahl", "bic", "name"],
    "filter": [],
    "spalte5": {"titel": "Art", "feld": "art"},
    "aenderung_name": "Bankenname",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Täglicher Vergleich mit dem Vortag (Teilnehmer am Zahlungssystem ReGIS der BNR). Der "
                           "Bankcode sind die ersten vier Zeichen des BIC.",
    "details": [["Bankcode", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"], ["Art", "art"]],
}


def stand_text(meta: dict) -> str:
    return "Teilnehmer am Zahlungssystem ReGIS"
