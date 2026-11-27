"""Slowakei – Prevodník identifikačných kódov der Slowakischen Nationalbank (NBS).

- Angeboten werden nur PDF und CSV, kein XML oder JSON. Die CSV ist Windows-1250-kodiert,
  nutzt Semikolons und hat vor der Kopfzeile eine Titelzeile.
- Der Download-Link enthält eine Dokument-ID, die sich ändern kann; er wird jedes Mal von
  der Seite gelesen (der Link, dessen Datei CSV ist).
- Der Kód platebného styku steht in der IBAN vierstellig an den Stellen 5–8; in der Datei
  fehlen führende Nullen (200 -> 0200). Die Liste enthält auch tschechische Institute,
  die im slowakischen Zahlungsverkehr erreichbar sind.
- Systém SIPS: „x“ = Teilnehmer am slowakischen Clearing-System SIPS.
"""

from __future__ import annotations

import csv
import html
import io
import re
import urllib.parse
import urllib.request

from kern import SCHLUESSEL, Stand, herunterladen, leer

CODE = "SK"
NAME = "Slowakei"
BLZ_STELLEN = 4
SEITE = "https://nbs.sk/platby/vseobecne-informacie/ciselniky-a-registre/prevodnik-sk/"
QUELLE = {
    "name": "Národná banka Slovenska – Prevodník identifikačných kódov",
    "kurz": "NBS",
    "url": SEITE,
    "bedingungen": SEITE,
}
SPALTEN = ["Bankleitzahl", "BIC", "Bankenname", "SIPS"]


def _csv_url(seite: str) -> str:
    links = dict.fromkeys(re.findall(r'href="([^"]*/dokument/[^"]+/stiahnut/[^"]*)"', seite))
    for l in links:
        url = urllib.parse.urljoin(SEITE, html.unescape(l))
        kopf = urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers={"User-Agent": "bic-verzeichnis-update"}), timeout=60)
        if kopf.headers.get("Content-Type", "").startswith("text/csv"):
            return url
    raise RuntimeError("kein CSV-Download auf der NBS-Seite gefunden – Seite geändert?")


def laden(args, alte_meta: dict) -> Stand:
    roh = args.input[0].read_bytes() if args.input else herunterladen(_csv_url(herunterladen(SEITE).decode("utf-8", "replace")))
    zeilen = roh.decode("cp1250").splitlines()
    try:
        start = next(i for i, z in enumerate(zeilen) if z.startswith("Kód platobného styku;"))
    except StopIteration:
        raise RuntimeError("Kopfzeile in der NBS-CSV nicht gefunden – Format geändert?")
    banken = []
    for r in csv.reader(io.StringIO("\n".join(zeilen[start + 1:])), delimiter=";"):
        if len(r) < 3 or not r[0].strip():
            continue
        banken.append({"Bankleitzahl": r[0].strip(), "BIC": r[2].strip(), "Bankenname": r[1].strip(),
                       "SIPS": "ja" if len(r) > 3 and r[3].strip().lower() == "x" else "nein"})
    banken.sort(key=lambda z: z[SCHLUESSEL].zfill(4))
    print(f"[{CODE}] NBS-Prevodník: {len(banken)} Einträge")
    return Stand(spalten=SPALTEN, banken=banken, datum=args.today.isoformat())


def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    return {
        "land": CODE,
        "bankleitzahl": leer(z.get("Bankleitzahl")),
        "bic": leer(z.get("BIC")),
        "name": leer(z.get("Bankenname")),
        "status": None,
        "entfernt_am": None,
        "sips": z.get("SIPS") == "ja",
    }


WEB = {
    "suche_platzhalter": "Bankleitzahl, BIC oder Bankname …",
    "suche": ["bankleitzahl", "bic", "name"],
    "filter": [],
    "spalte5": {"titel": "SIPS", "feld": "sips", "art": "ja_nein"},
    "aenderung_name": "Bankenname",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Täglicher Vergleich mit dem Vortag. Einträge, die aus dem Prevodník der NBS "
                           "verschwinden, bleiben hier mit ihrem letzten Stand erhalten.",
    "details": [
        ["Bankleitzahl", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"],
        ["SIPS", "sips", "ja:Teilnehmer am slowakischen Clearing (SIPS)"],
    ],
}


def stand_text(meta: dict) -> str:
    return ""
