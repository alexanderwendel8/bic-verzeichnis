#!/usr/bin/env python3
"""Lädt die Bankverzeichnisse und protokolliert Änderungen – für alle oder ausgewählte Länder.

  python3 update.py                 alle Länder
  python3 update.py AT DE           nur diese Länder
  python3 update.py DE --input a.xml b.xml --today 2026-12-07   (lokale Dateien, Stichtag zum Testen)

Die Länder laufen unabhängig voneinander: Schlägt eines fehl, werden die anderen trotzdem
aktualisiert. Der Rückgabewert ist dann 1.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import traceback
from pathlib import Path

import kern


def main() -> int:
    laender = kern.laender_module()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("land", nargs="*", type=str.upper, help=f"Ländercodes: {', '.join(laender)} (Standard: alle)")
    ap.add_argument("--input", type=Path, nargs="+", help="Lokale Quelldatei(en) statt Download (nur mit genau einem Land)")
    ap.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today(), help="Stichtag JJJJ-MM-TT (zum Testen)")
    ap.add_argument("--force", action="store_true", help="Auch bei starkem Rückgang der Einträge übernehmen")
    args = ap.parse_args()
    auswahl = args.land or list(laender)
    unbekannt = [c for c in auswahl if c not in laender]
    if unbekannt:
        ap.error(f"unbekannte Länder: {', '.join(unbekannt)} (bekannt: {', '.join(laender)})")
    if args.input and len(auswahl) != 1:
        ap.error("--input geht nur zusammen mit genau einem Land")

    fehlgeschlagen = []
    for code in auswahl:
        land = laender[code]
        try:
            stand = land.laden(args, kern.meta_lesen(land))
            kern.aktualisieren(land, stand, erzwingen=args.force)
        except Exception as e:  # ein Land darf die anderen nicht aufhalten
            traceback.print_exc()
            kern.fehler(f"[{code}] {e}")
            fehlgeschlagen.append(code)
    if fehlgeschlagen:
        kern.fehler(f"fehlgeschlagen: {', '.join(fehlgeschlagen)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
