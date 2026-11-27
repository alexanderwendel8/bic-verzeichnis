"""Gemeinsamer Teil für alle Länder: Ablage, Vergleich, Änderungsprotokoll, API-Einträge.

Ein Land ist ein Modul in laender/ und liefert mit laden() einen Stand (siehe unten).
Alles Weitere – Vergleich mit dem letzten Stand, Änderungsdateien, Ablage, API und
Webseite – erledigt dieser Kern für alle Länder gleich.

Ablage je Land (<cc> = Ländercode in Kleinbuchstaben):
  data/<cc>/bankleitzahlen.csv      eine Zeile je Bankleitzahl
  data/<cc>/filialen.csv            weitere Orte je Bankleitzahl (nur wenn das Land welche hat)
  data/<cc>/meta.json               Angaben zur verwendeten Quelldatei (nur wenn das Land welche hat)
  changes/<cc>/JJJJ-MM-TT.csv       neue, geänderte und entfernte Bankleitzahlen eines Tages
  changes/<cc>/index.json           Liste der Tage mit Änderungen

Nur Python-Standardbibliothek.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

BASIS = Path(__file__).resolve().parent
SCHLUESSEL = "Bankleitzahl"
# Ablageformat: UTF-8 mit BOM, damit Excel die Umlaute korrekt anzeigt.
KODIERUNG = "utf-8-sig"
# Schutz gegen kaputte/abgeschnittene Downloads: Fällt die Anzahl der Bankleitzahlen unter
# diesen Anteil des vorherigen Stands, wird abgebrochen statt massenhaft „entfernt“ zu melden.
MIN_ANTEIL = 0.8
ART_REIHENFOLGE = {"neu": 0, "geändert": 1, "entfernt": 2}


@dataclass
class Stand:
    """Was ein Land-Modul aus seiner Quelle liefert."""
    spalten: list[str]                                   # Spalten von banken (muss SCHLUESSEL enthalten)
    banken: list[dict[str, str]]                         # aktive Bankleitzahlen, je eine Zeile
    datum: str                                           # Tag, unter dem Änderungen abgelegt werden (JJJJ-MM-TT)
    filialen: list[dict[str, str]] | None = None         # weitere Orte je Bankleitzahl, sonst None
    filial_spalten: list[str] | None = None
    meta: dict = field(default_factory=dict)             # z. B. Gültigkeit der Quelldatei
    entfernt: list[dict[str, str]] = field(default_factory=list)  # von der Quelle selbst als gelöscht markiert


# ---------------------------------------------------------------- Hilfen für Land-Module

def herunterladen(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "bic-verzeichnis-update"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def leer(wert: str | None) -> str | None:
    wert = (wert or "").strip()
    return wert or None


# ---------------------------------------------------------------- Pfade

def daten_ordner(land: ModuleType) -> Path:
    return BASIS / "data" / land.CODE.lower()


def aenderungs_ordner(land: ModuleType) -> Path:
    return BASIS / "changes" / land.CODE.lower()


# ---------------------------------------------------------------- CSV

def csv_lesen(pfad: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not pfad.exists():
        return [], []
    with pfad.open(encoding=KODIERUNG, newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        return list(reader.fieldnames or []), list(reader)


def csv_schreiben(pfad: Path, spalten: list[str], zeilen: list[dict[str, str]]) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with pfad.open("w", encoding=KODIERUNG, newline="") as f:
        w = csv.DictWriter(f, fieldnames=spalten, delimiter=";", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(zeilen)


def text_schreiben(pfad: Path, text: str) -> None:
    """Nur schreiben, wenn sich etwas ändert (vermeidet leere Commits)."""
    pfad.parent.mkdir(parents=True, exist_ok=True)
    if not pfad.exists() or pfad.read_text(encoding="utf-8") != text:
        pfad.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- Vergleich

def vergleichen(alt: list[dict], neu: list[dict], spalten: list[str]) -> list[tuple[str, str, dict]]:
    """-> Liste von (Art, Geänderte Felder, Zeile)."""
    alt_k = {r[SCHLUESSEL]: r for r in alt}
    neu_k = {r[SCHLUESSEL]: r for r in neu}
    ergebnis = []
    for k, zeile in neu_k.items():
        if k not in alt_k:
            ergebnis.append(("neu", "", zeile))
            continue
        vorher = alt_k[k]
        felder = [f"{c}: {vorher.get(c, '')} -> {zeile.get(c, '')}" for c in spalten if vorher.get(c, "") != zeile.get(c, "")]
        if felder:
            ergebnis.append(("geändert", " | ".join(felder), zeile))
    for k, zeile in alt_k.items():
        if k not in neu_k:
            ergebnis.append(("entfernt", "", zeile))
    return ergebnis


def filial_signatur(filialen: list[dict], spalten: list[str]) -> dict[str, set]:
    sig: dict[str, set] = {}
    vergleich = [c for c in spalten if c not in (SCHLUESSEL, "Datensatznummer")]
    for f in filialen:
        sig.setdefault(f[SCHLUESSEL], set()).add(tuple(f.get(c, "") for c in vergleich))
    return sig


def sortierschluessel(blz: str) -> str:
    return blz.zfill(12)


# ---------------------------------------------------------------- Änderungsprotokoll

def aenderungen_schreiben(land: ModuleType, tag: str, aenderungen: list[tuple[str, str, dict]], spalten: list[str]) -> Path:
    pfad = aenderungs_ordner(land) / f"{tag}.csv"
    bisher = csv_lesen(pfad)[1]  # mehrere Läufe am selben Tag: zusammenführen, letzte Meldung je BLZ gewinnt
    neue_keys = {z[SCHLUESSEL] for _, _, z in aenderungen}
    zeilen = [z for z in bisher if z[SCHLUESSEL] not in neue_keys]
    zeilen += [{"Änderung": art, "Geänderte Felder": felder, **z} for art, felder, z in aenderungen]
    zeilen.sort(key=lambda z: (ART_REIHENFOLGE.get(z["Änderung"], 9), sortierschluessel(z[SCHLUESSEL])))
    csv_schreiben(pfad, ["Änderung", "Geänderte Felder"] + spalten, zeilen)
    return pfad


def aenderungs_index_schreiben(land: ModuleType) -> None:
    ordner = aenderungs_ordner(land)
    tage = []
    for f in sorted(ordner.glob("????-??-??.csv"), reverse=True):
        arten = [z.get("Änderung", "") for z in csv_lesen(f)[1]]
        tage.append({"datum": f.stem, "neu": arten.count("neu"),
                     "geaendert": arten.count("geändert"), "entfernt": arten.count("entfernt")})
    text_schreiben(ordner / "index.json", json.dumps(tage, ensure_ascii=False, indent=1) + "\n")


# ---------------------------------------------------------------- Aktualisieren

def aktualisieren(land: ModuleType, stand: Stand, erzwingen: bool = False) -> None:
    ordner = daten_ordner(land)
    banken_pfad, filial_pfad, meta_pfad = ordner / "bankleitzahlen.csv", ordner / "filialen.csv", ordner / "meta.json"
    alt_spalten, alt_banken = csv_lesen(banken_pfad)
    alt_filialen = csv_lesen(filial_pfad)[1]

    print(f"[{land.CODE}] {len(stand.banken)} Bankleitzahlen"
          + (f", {len(stand.filialen)} Filialen" if stand.filialen is not None else "")
          + (f", {len(stand.entfernt)} von der Quelle als gelöscht markiert" if stand.entfernt else ""))

    if alt_banken and len(stand.banken) < MIN_ANTEIL * len(alt_banken) and not erzwingen:
        raise RuntimeError(f"nur {len(stand.banken)} statt bisher {len(alt_banken)} Bankleitzahlen – "
                           "Download vermutlich unvollständig (mit --force trotzdem übernehmen)")

    spalten = stand.spalten + [c for c in alt_spalten if c not in stand.spalten]
    if not alt_banken:
        print(f"[{land.CODE}] Kein vorheriger Stand vorhanden – Ausgangsstand wird angelegt.")
        aenderungen = [("entfernt", "", z) for z in stand.entfernt]
    else:
        aenderungen = vergleichen(alt_banken, stand.banken, spalten)
        if stand.filialen is not None:  # geänderte Filialen als Hinweis an der Bankleitzahl
            alt_sig = filial_signatur(alt_filialen, stand.filial_spalten or [])
            neu_sig = filial_signatur(stand.filialen, stand.filial_spalten or [])
            alt_keys = {z[SCHLUESSEL] for z in alt_banken}
            pos = {z[SCHLUESSEL]: i for i, (_, _, z) in enumerate(aenderungen)}
            for z in stand.banken:
                k = z[SCHLUESSEL]
                if k in alt_keys and alt_sig.get(k, set()) != neu_sig.get(k, set()):
                    hinweis = f"Filialen: {len(alt_sig.get(k, ()))} -> {len(neu_sig.get(k, ()))}"
                    if k in pos:
                        art, felder, zeile = aenderungen[pos[k]]
                        aenderungen[pos[k]] = (art, " | ".join(filter(None, [felder, hinweis])), zeile)
                    else:
                        aenderungen.append(("geändert", hinweis, z))
        # entfernte Bankleitzahlen: letzten Stand aus der Quelle nehmen, falls sie ihn mitliefert
        von_quelle = {z[SCHLUESSEL]: z for z in stand.entfernt}
        aenderungen = [(a, f, von_quelle.get(z[SCHLUESSEL], z) if a == "entfernt" else z) for a, f, z in aenderungen]

    if aenderungen:
        pfad = aenderungen_schreiben(land, stand.datum, aenderungen, spalten)
        n = {a: sum(x[0] == a for x in aenderungen) for a in ART_REIHENFOLGE}
        print(f"[{land.CODE}] Änderungen: {n['neu']} neu, {n['geändert']} geändert, {n['entfernt']} entfernt -> {pfad.relative_to(BASIS)}")
    else:
        print(f"[{land.CODE}] Keine Änderungen.")

    csv_schreiben(banken_pfad, spalten, stand.banken)
    if stand.filialen is not None:
        csv_schreiben(filial_pfad, stand.filial_spalten or [], stand.filialen)
    if stand.meta:
        text_schreiben(meta_pfad, json.dumps(stand.meta, ensure_ascii=False, indent=1) + "\n")
    aenderungs_index_schreiben(land)


# ---------------------------------------------------------------- Lesen für API und Webseite

def meta_lesen(land: ModuleType) -> dict:
    pfad = daten_ordner(land) / "meta.json"
    return json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else {}


def api_eintraege(land: ModuleType) -> dict[str, dict]:
    """Alle Bankleitzahlen eines Landes als API-Einträge, inklusive entfernter (letzter Stand)."""
    ordner = daten_ordner(land)
    meta = meta_lesen(land)
    filialen: dict[str, list] = {}
    for f in csv_lesen(ordner / "filialen.csv")[1]:
        filialen.setdefault(f[SCHLUESSEL], []).append(f)
    eintraege = {}
    for z in csv_lesen(ordner / "bankleitzahlen.csv")[1]:
        e = land.api_eintrag(z, filialen.get(z[SCHLUESSEL], []), meta, entfernt=False)
        e["status"], e["entfernt_am"] = "aktiv", None
        eintraege[z[SCHLUESSEL]] = e
    entfernt: dict[str, dict] = {}
    for f in sorted(aenderungs_ordner(land).glob("????-??-??.csv")):  # chronologisch, spätere überschreiben
        for z in csv_lesen(f)[1]:
            blz = z.get(SCHLUESSEL)
            if not blz:
                continue
            if z.get("Änderung") == "entfernt":
                e = land.api_eintrag(z, [], {}, entfernt=True)
                e["status"], e["entfernt_am"] = "entfernt", f.stem
                entfernt[blz] = e
            else:  # wieder aufgetaucht
                entfernt.pop(blz, None)
    eintraege.update({k: v for k, v in entfernt.items() if k not in eintraege})
    return dict(sorted(eintraege.items(), key=lambda kv: sortierschluessel(kv[0])))


def laender_module() -> dict[str, ModuleType]:
    from laender import LAENDER
    return LAENDER


def fehler(text: str) -> None:
    print(f"Fehler: {text}", file=sys.stderr)


def heute() -> dt.date:
    return dt.date.today()
