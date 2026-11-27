#!/usr/bin/env python3
"""Stellt die Webseite samt API für GitHub Pages zusammen.

  python3 build_site.py _site

Ergebnis:
  <ziel>/index.html, app.js, style.css      Weboberfläche (aus web/)
  <ziel>/laender.json                       Länder und ihre Einstellungen für die Weboberfläche
  <ziel>/build.json                         Datum der Erzeugung („geprüft am“)
  <ziel>/data/…, <ziel>/changes/…           Rohdaten und Änderungsprotokolle zum Herunterladen
  <ziel>/api/v1/index.json                  Übersicht: Länder, Anzahl, Quelle
  <ziel>/api/v1/<CC>/index.json             alle Bankleitzahlen eines Landes kurz
  <ziel>/api/v1/<CC>/alle.json              alle Bankleitzahlen eines Landes mit allen Daten
  <ziel>/api/v1/<CC>/<bankleitzahl>.json    eine Bankleitzahl
  (alles unter api/v1/ zusätzlich mit Ländercode in Kleinbuchstaben)
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import kern

VERSION = "v1"


def json_schreiben(pfad: Path, obj, kompakt: bool = False) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) if kompakt \
        else json.dumps(obj, ensure_ascii=False, indent=2)
    pfad.write_text(text + "\n", encoding="utf-8")


def api_schreiben(api: Path, land, eintraege: dict[str, dict]) -> None:
    for code in (land.CODE, land.CODE.lower()):
        ordner = api / code
        for blz, e in eintraege.items():
            json_schreiben(ordner / f"{blz}.json", e)
            if land.BLZ_STELLEN:  # kürzere Bankleitzahl auch in IBAN-Schreibweise (100 -> 00100)
                lang = blz.zfill(land.BLZ_STELLEN)
                if lang != blz and lang not in eintraege:
                    json_schreiben(ordner / f"{lang}.json", e)
        json_schreiben(ordner / "index.json", {
            "land": land.CODE,
            "anzahl": len(eintraege),
            "banken": [{"bankleitzahl": e["bankleitzahl"], "bic": e["bic"], "name": e["name"], "status": e["status"]}
                       for e in eintraege.values()],
        })
        json_schreiben(ordner / "alle.json", list(eintraege.values()), kompakt=True)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    ziel = Path(sys.argv[1])
    if ziel.exists():
        shutil.rmtree(ziel)
    ziel.mkdir(parents=True)

    # Weboberfläche und Rohdaten
    for f in (kern.BASIS / "web").iterdir():
        shutil.copy2(f, ziel / f.name)
    shutil.copytree(kern.BASIS / "data", ziel / "data")
    if (kern.BASIS / "changes").exists():
        shutil.copytree(kern.BASIS / "changes", ziel / "changes")

    api = ziel / "api" / VERSION
    uebersicht, web_laender = {}, {}
    for code, land in kern.laender_module().items():
        if not (kern.daten_ordner(land) / "bankleitzahlen.csv").exists():
            print(f"[{code}] noch keine Daten – übersprungen")
            continue
        eintraege = kern.api_eintraege(land)
        meta = kern.meta_lesen(land)
        api_schreiben(api, land, eintraege)
        cc = code.lower()
        idx = ziel / "changes" / cc / "index.json"
        if not idx.exists():
            idx.parent.mkdir(parents=True, exist_ok=True)
            idx.write_text("[]\n", encoding="utf-8")
        aktiv = sum(e["status"] == "aktiv" for e in eintraege.values())
        uebersicht[code] = {"name": land.NAME, "quelle": land.QUELLE["name"], "anzahl": len(eintraege),
                            "aktiv": aktiv, "entfernt": len(eintraege) - aktiv}
        if meta.get("ValidFrom"):
            uebersicht[code].update({"gueltig_ab": meta["ValidFrom"], "gueltig_bis": meta.get("ValidTill")})
        web_laender[code] = {
            "name": land.NAME,
            # Hinweis mit Stand der Daten, wo die Quelle das verlangt (z. B. Frankreich)
            "quelle": {**land.QUELLE, "hinweis": land.quellen_hinweis(meta)} if hasattr(land, "quellen_hinweis") else land.QUELLE,
            "daten": f"api/{VERSION}/{code}/alle.json",
            "csv": f"data/{cc}/bankleitzahlen.csv",
            "aenderungen": f"changes/{cc}/",
            "stand_text": land.stand_text(meta),
            "blz_stellen": land.BLZ_STELLEN,
            "original": f"data/{cc}/{land.ORIGINAL}" if getattr(land, "ORIGINAL", None)
            else getattr(land, "ORIGINAL_URL", None),  # zu große, täglich neue Originale: Link zur Quelle
            "zusatz_hinweis": land.zusatz_hinweis(meta) if hasattr(land, "zusatz_hinweis") else "",
            **land.WEB,
        }
        alt = getattr(land, "ALTE_CSV_ADRESSE", None)  # frühere Download-Adresse weiter bedienen
        if alt:
            (ziel / alt).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(kern.daten_ordner(land) / "bankleitzahlen.csv", ziel / alt)
        print(f"[{code}] API: {len(eintraege)} Bankleitzahlen ({aktiv} aktiv)")

    json_schreiben(api / "index.json", {
        "version": VERSION,
        "erzeugt_am": dt.datetime.now(ZoneInfo("Europe/Vienna")).date().isoformat(),
        "laender": uebersicht,
        "aufruf": f"/api/{VERSION}/{{land}}/{{bankleitzahl}}.json",
    })
    json_schreiben(ziel / "laender.json", web_laender)
    json_schreiben(ziel / "build.json", {"geprueft": dt.datetime.now(ZoneInfo("Europe/Vienna")).date().isoformat()})
    (ziel / ".nojekyll").touch()
    return 0


if __name__ == "__main__":
    sys.exit(main())
