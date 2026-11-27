#!/usr/bin/env python3
"""Lädt die Bankleitzahlendatei der Deutschen Bundesbank und protokolliert Änderungen.

Ablauf:
  1. Download-Seite der Bundesbank abrufen und die Links zu den XML-Dateien
     („aktuell“ und „neu“) dort auslesen – die Adressen sind nicht fest.
  2. Beide XML-Dateien laden und die verwenden, die heute gilt
     (Dateikopf ValidFrom <= heute <= ValidTill).
  3. Pro Bankleitzahl den Haupteintrag (Merkmal „1“) als Bank übernehmen,
     Zusatzeinträge (Merkmal „2“) als Filialen dieser Bankleitzahl.
     Einträge mit Änderungskennzeichen „D“ gelten als entfernt.
  4. Mit dem zuletzt abgelegten Stand vergleichen; neue, geänderte und
     entfernte Bankleitzahlen nach changes/de/JJJJ-MM-TT.csv schreiben.
  5. Stand ablegen: data/de/bankleitzahlen.csv, data/de/filialen.csv, data/de/meta.json.

Nur Python-Standardbibliothek.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from update_bic import MIN_ROW_RATIO, OUT_ENCODING, diff, read_stored, write_csv

PAGE_URL = ("https://www.bundesbank.de/de/aufgaben/unbarer-zahlungsverkehr/"
            "serviceangebot/bankleitzahlen/download-bankleitzahlen-602592")
NS = "{urn:BBk:BLZ:xsd:BLZDat}"
KEY = "Bankleitzahl"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "de"
BANKS_FILE = DATA_DIR / "bankleitzahlen.csv"
BRANCHES_FILE = DATA_DIR / "filialen.csv"
META_FILE = DATA_DIR / "meta.json"
CHANGES_DIR = BASE_DIR / "changes" / "de"

# XML-Element -> Spaltenname in der Ablage
BANK_FIELDS = {
    "BLZ": "Bankleitzahl", "BIC": "BIC", "Bezeichnung": "Bezeichnung", "Kurzbez": "Kurzbezeichnung",
    "PLZ": "PLZ", "Ort": "Ort", "PAN": "PAN", "PruefZiffMeth": "Prüfzifferberechnungsmethode",
    "DsNr": "Datensatznummer", "BLZLoesch": "Bankleitzahllöschung", "NachfolgeBLZ": "Nachfolge-Bankleitzahl",
}
BRANCH_FIELDS = {
    "BLZ": "Bankleitzahl", "Bezeichnung": "Bezeichnung", "Kurzbez": "Kurzbezeichnung",
    "PLZ": "PLZ", "Ort": "Ort", "BIC": "BIC", "PAN": "PAN", "DsNr": "Datensatznummer",
}
BANK_COLUMNS = list(BANK_FIELDS.values())
BRANCH_COLUMNS = list(BRANCH_FIELDS.values())


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "bic-update-script"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def find_xml_links(page: str) -> list[str]:
    links = re.findall(r'href="([^"]+-xml-data\.xml)"', page)
    links = [urllib.parse.urljoin(PAGE_URL, html.unescape(l)) for l in dict.fromkeys(links)]
    if not links:
        raise SystemExit("Fehler: keine XML-Links auf der Bundesbank-Seite gefunden – Seite geändert?")
    return links


def parse_xml(raw: bytes) -> tuple[dict[str, str], list[dict[str, str]]]:
    root = ET.fromstring(raw)
    if root.tag != NS + "Document":
        raise SystemExit(f"Fehler: unerwartetes XML-Format ({root.tag}).")
    hdr = {c.tag.replace(NS, ""): (c.text or "").strip() for c in root.find(NS + "FileHdr")}
    rows = [{c.tag.replace(NS, ""): (c.text or "").strip() for c in e} for e in root.findall(NS + "BLZEintrag")]
    for k in ("ValidFrom", "ValidTill", "FileRef"):
        if not hdr.get(k):
            raise SystemExit(f"Fehler: Dateikopf ohne {k}.")
    return hdr, rows


def pick_valid(files: list[tuple[dict, list]], today: dt.date):
    def d(s: str) -> dt.date:
        return dt.date.fromisoformat(s)
    current = [f for f in files if d(f[0]["ValidFrom"]) <= today <= d(f[0]["ValidTill"])]
    if not current:  # Lücke zwischen den Dateien: die zuletzt gültig gewordene nehmen
        current = [f for f in files if d(f[0]["ValidFrom"]) <= today]
    if not current:
        raise SystemExit("Fehler: keine der Bundesbank-Dateien ist heute gültig.")
    return max(current, key=lambda f: f[0]["ValidFrom"])


def split_records(rows: list[dict[str, str]]):
    """-> (aktive Banken, gelöschte Banken (D), Filialen)"""
    banks, removed, branches = [], [], []
    for r in rows:
        if r.get("Merkmal") == "1":
            rec = {col: r.get(tag, "") for tag, col in BANK_FIELDS.items()}
            (removed if r.get("Aenderungskennz") == "D" else banks).append(rec)
        elif r.get("Merkmal") == "2" and r.get("Aenderungskennz") != "D":
            branches.append({col: r.get(tag, "") for tag, col in BRANCH_FIELDS.items()})
    key = lambda r: r[KEY]
    banks.sort(key=key)
    removed.sort(key=key)
    branches.sort(key=lambda r: (r[KEY], r["Ort"], r["PLZ"], r["Datensatznummer"].zfill(10)))
    return banks, removed, branches


def branch_signature(branches: list[dict[str, str]]) -> dict[str, set]:
    sig: dict[str, set] = {}
    for b in branches:
        sig.setdefault(b[KEY], set()).add((b["Bezeichnung"], b["PLZ"], b["Ort"], b["BIC"], b["PAN"]))
    return sig


def write_changes_index() -> None:
    days = []
    for f in sorted(CHANGES_DIR.glob("????-??-??.csv"), reverse=True):
        with f.open(encoding=OUT_ENCODING, newline="") as fh:
            kinds = [r.get("Änderung", "") for r in csv.DictReader(fh, delimiter=";")]
        days.append({"datum": f.stem, "neu": kinds.count("neu"),
                     "geaendert": kinds.count("geändert"), "entfernt": kinds.count("entfernt")})
    CHANGES_DIR.mkdir(parents=True, exist_ok=True)
    text = json.dumps(days, ensure_ascii=False, indent=1) + "\n"
    index = CHANGES_DIR / "index.json"
    if not index.exists() or index.read_text(encoding="utf-8") != text:
        index.write_text(text, encoding="utf-8")


def write_changes(day: str, changes: list[tuple[str, str, dict]]) -> None:
    out = CHANGES_DIR / f"{day}.csv"
    existing = []
    if out.exists():  # mehrere Läufe am selben Tag: zusammenführen, letzte Meldung je BLZ gewinnt
        with out.open(encoding=OUT_ENCODING, newline="") as fh:
            existing = list(csv.DictReader(fh, delimiter=";"))
    new_keys = {row[KEY] for _, _, row in changes}
    rows = [r for r in existing if r[KEY] not in new_keys]
    rows += [{"Änderung": kind, "Geänderte Felder": fields, **row} for kind, fields, row in changes]
    order = {"neu": 0, "geändert": 1, "entfernt": 2}
    rows.sort(key=lambda r: (order.get(r["Änderung"], 9), r[KEY]))
    write_csv(out, ["Änderung", "Geänderte Felder"] + BANK_COLUMNS, rows)
    c = {k: sum(r["Änderung"] == k for r in rows) for k in order}
    print(f"Änderungen: {c['neu']} neu, {c['geändert']} geändert, {c['entfernt']} entfernt -> {out}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", type=Path, nargs="+", help="Lokale Bundesbank-XML-Dateien statt Download")
    ap.add_argument("--today", type=dt.date.fromisoformat, help="Stichtag (JJJJ-MM-TT), nur zum Testen")
    ap.add_argument("--force", action="store_true", help="Auch bei starkem Rückgang der Einträge übernehmen")
    args = ap.parse_args()
    today = args.today or dt.date.today()

    if args.input:
        raws = [p.read_bytes() for p in args.input]
    else:
        links = find_xml_links(fetch(PAGE_URL).decode("utf-8", "replace"))
        raws = [fetch(u) for u in links]
    files = [parse_xml(r) for r in raws]
    for hdr, rows in files:
        print(f"Bundesbank-Datei {hdr['FileRef']}: gültig {hdr['ValidFrom']} bis {hdr['ValidTill']}, {len(rows)} Datensätze")
    hdr, rows = pick_valid(files, today)
    banks, removed_now, branches = split_records(rows)
    print(f"Verwendet: {hdr['FileRef']} – {len(banks)} Bankleitzahlen, {len(branches)} Filialen, "
          f"{len(removed_now)} zum {hdr['ValidFrom']} gelöscht")

    old_meta = json.loads(META_FILE.read_text(encoding="utf-8")) if META_FILE.exists() else {}
    _, old_banks = read_stored(BANKS_FILE)
    _, old_branches = read_stored(BRANCHES_FILE)

    if old_banks and len(banks) < MIN_ROW_RATIO * len(old_banks) and not args.force:
        print(f"Fehler: nur {len(banks)} statt bisher {len(old_banks)} Bankleitzahlen – Abbruch "
              "(mit --force übernehmen).", file=sys.stderr)
        return 1

    # Gültigkeitswechsel -> Änderungen zum Gültigkeitstag, sonst (Korrektur) zum heutigen Tag
    day = hdr["ValidFrom"] if old_meta.get("ValidFrom") != hdr["ValidFrom"] else today.isoformat()

    if not old_banks:
        print("Kein vorheriger Stand vorhanden – Ausgangsstand wird angelegt.")
        changes = [("entfernt", "", r) for r in removed_now]
    else:
        changes = diff(old_banks, banks, BANK_COLUMNS)
        old_sig, new_sig = branch_signature(old_branches), branch_signature(branches)
        new_keys = {r[KEY] for r in banks}
        by_key = {c[2][KEY]: i for i, c in enumerate(changes)}
        for r in banks:  # geänderte Filialen als Hinweis an der Bankleitzahl
            k = r[KEY]
            if k in {o[KEY] for o in old_banks} and old_sig.get(k, set()) != new_sig.get(k, set()):
                note = f"Filialen: {len(old_sig.get(k, ()))} -> {len(new_sig.get(k, ()))}"
                if k in by_key:
                    kind, fields, row = changes[by_key[k]]
                    changes[by_key[k]] = (kind, " | ".join(filter(None, [fields, note])), row)
                else:
                    changes.append(("geändert", note, r))
        # entfernte Bankleitzahlen mit dem letzten Stand aus der Bundesbank-Datei (inkl. Nachfolge-BLZ)
        removed_map = {r[KEY]: r for r in removed_now}
        changes = [(k, f, removed_map.get(row[KEY], row) if k == "entfernt" else row) for k, f, row in changes]
        changes = [c for c in changes if not (c[0] == "entfernt" and c[2][KEY] in new_keys)]

    if changes:
        write_changes(day, changes)
    else:
        print("Keine Änderungen.")

    write_csv(BANKS_FILE, BANK_COLUMNS, banks)
    write_csv(BRANCHES_FILE, BRANCH_COLUMNS, branches)
    meta = {k: hdr[k] for k in ("FileRef", "FileCreDt", "ValidFrom", "ValidTill") if k in hdr}
    meta["Quelle"] = PAGE_URL
    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(meta, ensure_ascii=False, indent=1) + "\n"
    if not META_FILE.exists() or META_FILE.read_text(encoding="utf-8") != text:
        META_FILE.write_text(text, encoding="utf-8")
    write_changes_index()
    return 0


if __name__ == "__main__":
    sys.exit(main())
