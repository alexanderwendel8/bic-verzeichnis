#!/usr/bin/env python3
"""Erzeugt die statische JSON-API für GitHub Pages.

Aufruf:  python3 build_api.py <zielordner>      (z. B. _site/api)

Ergebnis (Beispiel für Österreich):
  <ziel>/v1/index.json            Übersicht: Länder, Stand, Anzahl
  <ziel>/v1/AT/index.json         alle Banken kurz (Bankleitzahl, BIC, Name, Status)
  <ziel>/v1/AT/20111.json         eine Bank mit allen Daten
                                  (kurze BLZ auch fünfstellig: 100.json und 00100.json)
  (zusätzlich alles unter <ziel>/v1/at/… in Kleinbuchstaben)

Banken, die aus dem OeNB-Verzeichnis entfernt wurden, bleiben mit
"status": "entfernt" und ihrem letzten bekannten Stand abrufbar.
Nur Python-Standardbibliothek.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "sepa-zv-vz_gesamt.csv"
CHANGES_DIR = BASE_DIR / "changes"
COUNTRY = "AT"
VERSION = "v1"
ENCODING = "utf-8-sig"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding=ENCODING, newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def clean(value: str | None) -> str | None:
    value = (value or "").strip()
    return None if value in ("", "nullnull") else value


def iso_date(value: str | None) -> str | None:
    """'08.11.2006' -> '2006-11-08'."""
    value = clean(value)
    m = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", value or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else value


def homepage(value: str | None) -> str | None:
    value = clean(value)
    if value and not re.match(r"https?://", value):
        value = "https://" + value
    return value


def bank_record(row: dict[str, str], status: str, removed_on: str | None = None) -> dict:
    return {
        "land": COUNTRY,
        "bankleitzahl": clean(row.get("Bankleitzahl")),
        "bic": clean(row.get("SWIFT-Code")),
        "name": clean(row.get("Bankenname")),
        "status": status,
        "entfernt_am": removed_on,
        "art": clean(row.get("Kennzeichen")),
        "sektor": clean(row.get("Sektor")),
        "institutsart": clean(row.get("Institutsart")),
        "identnummer": clean(row.get("Identnummer")),
        "firmenbuchnummer": clean(row.get("Firmenbuchnummer")),
        "lei": clean(row.get("LEI")),
        "gruendungsdatum": iso_date(row.get("Gründungsdatum")),
        "adresse": {
            "strasse": clean(row.get("Straße")),
            "plz": clean(row.get("PLZ")),
            "ort": clean(row.get("Ort")),
            "bundesland": clean(row.get("Bundesland")),
        },
        "postadresse": {
            "strasse": clean(row.get("Postadresse / Straße")),
            "plz": clean(row.get("Postadresse / PLZ")),
            "ort": clean(row.get("Postadresse / Ort")),
            "postfach": clean(row.get("Postfach")),
        },
        "kontakt": {
            "telefon": clean(row.get("Telefon")),
            "fax": clean(row.get("Fax")),
            "email": clean(row.get("E-Mail")),
            "homepage": homepage(row.get("Homepage")),
        },
    }


def removed_banks(active_keys: set[str]) -> dict[str, dict]:
    """Letzter bekannter Stand aller Banken, die heute nicht mehr im Verzeichnis sind."""
    removed: dict[str, dict] = {}
    for f in sorted(CHANGES_DIR.glob("????-??-??.csv")):  # chronologisch: spätere überschreiben
        for row in read_csv(f):
            blz = clean(row.get("Bankleitzahl"))
            if not blz:
                continue
            if row.get("Änderung") == "entfernt":
                removed[blz] = bank_record(row, "entfernt", f.stem)
            else:  # wieder aufgetaucht
                removed.pop(blz, None)
    return {k: v for k, v in removed.items() if k not in active_keys}


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    out = Path(sys.argv[1])
    root = out / VERSION
    if root.exists():
        shutil.rmtree(root)

    banks = {}
    for row in read_csv(DATA_FILE):
        rec = bank_record(row, "aktiv")
        if rec["bankleitzahl"]:
            banks[rec["bankleitzahl"]] = rec
    banks.update(removed_banks(set(banks)))

    for code in (COUNTRY, COUNTRY.lower()):
        for blz, rec in banks.items():
            write_json(root / code / f"{blz}.json", rec)
            # In der IBAN steht die Bankleitzahl immer fünfstellig (100 -> 00100).
            padded = blz.zfill(5)
            if padded != blz and padded not in banks:
                write_json(root / code / f"{padded}.json", rec)
        write_json(root / code / "index.json", {
            "land": COUNTRY,
            "anzahl": len(banks),
            "banken": [
                {"bankleitzahl": r["bankleitzahl"], "bic": r["bic"], "name": r["name"], "status": r["status"]}
                for r in sorted(banks.values(), key=lambda r: r["bankleitzahl"].zfill(10))
            ],
        })

    write_json(root / "index.json", {
        "version": VERSION,
        "quelle": "Oesterreichische Nationalbank – SEPA-Zahlungsverkehrs-Verzeichnis",
        "erzeugt_am": dt.date.today().isoformat(),
        "laender": {COUNTRY: {
            "anzahl": len(banks),
            "aktiv": sum(r["status"] == "aktiv" for r in banks.values()),
            "entfernt": sum(r["status"] == "entfernt" for r in banks.values()),
        }},
        "aufruf": f"/api/{VERSION}/{{land}}/{{bankleitzahl}}.json",
    })
    print(f"API erzeugt: {len(banks)} Banken für {COUNTRY} -> {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
