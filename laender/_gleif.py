"""BICs über die BIC/LEI-Zuordnung von SWIFT und GLEIF – für Quellen, die selbst keine BICs führen.

Die Zuordnungstabelle erscheint monatlich als ZIP mit CSV (BIC, LEI). Sie wird je Lauf nur einmal
geladen, auch wenn mehrere Länder sie brauchen. Für jede Kopie der BICs, auch in Teilen, ist der
SWIFT-Hinweis (swift_hinweis) Pflicht.
"""

from __future__ import annotations

import csv
import io
import json
import re
import urllib.request
import zipfile

MAPPING = "https://mapping.gleif.org/api/v2/bic-lei"
LEI_API = "https://api.gleif.org/api/v1/lei-records"
LIZENZ = ("https://www.gleif.org/lei-data/lei-mapping/download-bic-to-lei-relationship-files/"
          "2017-12-21_annex-2_bic-to-lei-mapping-table-license-agreement_final.pdf")
MONATE = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]

_cache: tuple[list[tuple[str, str]], str, str] | None = None


def swift_hinweis(tabelle: str | None) -> str:
    """Pflicht-Hinweis der BIC/LEI-Lizenz (Abschnitt 2) für jede Kopie, auch in Teilen. tabelle = JJJJ-MM."""
    datum = f"{MONATE[int(tabelle[5:7]) - 1]} {tabelle[:4]}" if tabelle else "[unbekannt]"
    return (f"SWIFT © and database rights {datum}. All rights reserved. "
            "This Mapping Table has been developed by SWIFT. Any use of the Mapping Table, in whole or in part, "
            "is subject to the BIC/LEI Mapping Table License Agreement as published with the Mapping Table available "
            "on GLEIF's website. The Mapping Table is updated monthly. For the latest BIC information and updates, "
            "always refer to www.swift.com/bic .")


def holen(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "bic-verzeichnis-update", "Accept": "application/vnd.api+json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def zuordnung() -> tuple[list[tuple[str, str]], str, str]:
    """-> ([(BIC, LEI), …] der neuesten gültigen Tabelle, Stand JJJJ-MM, Dateiname)."""
    global _cache
    if _cache is None:
        dateien = json.loads(holen(MAPPING))["data"]
        neueste = max((d for d in dateien if d["attributes"]["valid"]), key=lambda d: d["attributes"]["uploadedAt"])
        name = neueste["attributes"].get("fileName", "")
        z = zipfile.ZipFile(io.BytesIO(holen(neueste["attributes"]["downloadLink"])))
        csv_name = next(n for n in z.namelist() if n.endswith(".csv"))
        with z.open(csv_name) as f:
            paare = [(r["BIC"].strip().upper(), r["LEI"].strip())
                     for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")) if r.get("BIC") and r.get("LEI")]
        m = re.search(r"(\d{4})(\d{2})\d{2}", name) or re.search(r"(\d{4})-(\d{2})", neueste["attributes"].get("uploadedAt", ""))
        _cache = (paare, f"{m.group(1)}-{m.group(2)}" if m else "", name)
    return _cache


def ort_rang(bic: str) -> int:
    # 2. Zeichen des Ortscodes: 0 = Test-BIC, 1 = passiv, 2 = Reverse Billing; sonst voll verbunden
    return {"0": 0, "1": 1, "2": 2}.get(bic[7:8], 3)


def bic_wahl(bics: list[str]) -> tuple[str, list[str]]:
    """Haupt-BIC (voll verbunden, bevorzugt Hauptsitz …XXX) und die übrigen."""
    if not bics:
        return "", []
    haupt = max(bics, key=lambda b: (ort_rang(b), b.endswith("XXX"), -len(b)))
    return haupt, sorted(b for b in bics if b != haupt)


def hinweis_datei(tabelle: str, uebrige: str) -> bytes:
    """Inhalt von data/<land>/HINWEIS-BIC.txt."""
    return ("Die BICs in bankleitzahlen.csv (Spalten BIC und Weitere BICs) stammen aus der BIC/LEI-Zuordnung\n"
            "von SWIFT und GLEIF. Für sie gilt:\n\n" + swift_hinweis(tabelle) + "\n\nLizenz: " + LIZENZ +
            "\n\nAlle übrigen Angaben: " + uebrige + "\n").encode("utf-8")


# ---------------------------------------------------------------- Korrekturlisten

def korrekturen_anwenden(code: str, pfad, blz_muster: str, banken: dict[str, dict], quelle_name: str) -> int:
    """Von Hand gepflegte BICs (CSV: Bankleitzahl;BIC;Institut;Beleg;Geprüft am) auf banken anwenden.

    Ein abweichender bisheriger BIC rückt unter „Weitere BICs“; die BIC-Quelle wird „manuell“.
    Steht ein Code nicht mehr in der Quelle, gibt es eine Warnung. -> Anzahl angewandter Einträge."""
    import re as _re
    from pathlib import Path
    pfad = Path(pfad)
    if not pfad.exists():
        return 0
    with pfad.open(encoding="utf-8", newline="") as f:
        zeilen = [{k: (v or "").strip() for k, v in z.items()} for z in csv.DictReader(f, delimiter=";")]
    angewandt = 0
    for k in zeilen:
        if not _re.fullmatch(blz_muster, k["Bankleitzahl"]) or not _re.fullmatch(r"[A-Z0-9]{8}([A-Z0-9]{3})?", k["BIC"]):
            raise RuntimeError(f"ungültige Zeile in {pfad.name}: {k}")
        z = banken.get(k["Bankleitzahl"])
        if z is None:
            print(f"[{code}] Warnung: Korrektur für {k['Bankleitzahl']} ({k['Institut']}) – Code nicht mehr in {quelle_name}")
            continue
        if z["BIC"] != k["BIC"]:
            weitere = [b for b in [z["BIC"], *z["Weitere BICs"].split()] if b and b != k["BIC"]]
            z["BIC"], z["Weitere BICs"] = k["BIC"], " ".join(dict.fromkeys(weitere))
        z["BIC-Quelle"] = "manuell"
        angewandt += 1
    return angewandt
