"""Gemeinsame Quelle für die Schweiz und Liechtenstein: SIX Bank Master (JSON).

Die SIX veröffentlicht alle IIDs (Institutsidentifikation, frühere BC-Nummer) des Schweizer
Zahlungsverkehrs in einer JSON-Datei – Schweiz, Liechtenstein und ausländische Teilnehmer.
Die IID steht in der IBAN der Schweiz und Liechtensteins fünfstellig an den Stellen 5–9.

- entryType „BankMaster“: eine IID; iidType HEADQUARTERS (Hauptsitz), MAIN_BRANCH (Filiale)
  oder QR_IID (nur für QR-Rechnungen).
- entryType „BankMasterConcatenated“: eine IID wurde in eine andere überführt (iid -> newIid).

Die Datei wird je Lauf nur einmal geladen, auch wenn beide Länder sie brauchen.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from kern import SCHLUESSEL, Stand, herunterladen, leer

URL = "https://api.six-group.com/api/epcd/bankmaster/v3/bankmaster.json"
QUELLE = {
    "name": "SIX – Bank Master (Bankenstamm)",
    "kurz": "SIX",
    "url": URL,
    "bedingungen": URL,
}

ARTEN = {"HEADQUARTERS": "Hauptsitz", "MAIN_BRANCH": "Filiale", "QR_IID": "QR-IID"}
TEILNAHME = [
    ("sicParticipation", "SIC"), ("euroSicParticipation", "euroSIC"),
    ("rtgsCustomerPaymentsChf", "SIC-Kundenzahlungen CHF"), ("ipCustomerPaymentsChf", "Instant Payments CHF"),
    ("lsvBddChfParticipation", "LSV+/BDD CHF"), ("lsvBddEurParticipation", "LSV+/BDD EUR"),
]
SPALTEN = ["Bankleitzahl", "BIC", "Bankenname", "Art", "Hauptsitz-IID", "QR-IID gehört zu", "Straße", "Hausnummer",
           "PLZ", "Ort", "Sitzland", "SIC-IID"] + [name for _, name in TEILNAHME]
FUSION_SPALTEN = ["Bankleitzahl", "Nachfolge-Bankleitzahl"]


@lru_cache(maxsize=None)
def _laden(quelle: str) -> dict:
    roh = Path(quelle).read_bytes() if quelle != URL else herunterladen(URL)
    daten = json.loads(roh)
    if "entries" not in daten:
        raise RuntimeError("SIX-Datei ohne 'entries' – Format geändert?")
    return daten


def stand(args, laender: set[str], ausser: set[str] = frozenset()) -> Stand:
    """Stand für die IIDs mit Sitzland in `laender` (leer = alle) außer `ausser`."""
    daten = _laden(str(args.input[0]) if args.input else URL)
    eintraege = daten["entries"]
    banken = []
    for e in eintraege:
        if e.get("entryType") != "BankMaster":
            continue
        land = e.get("country", "")
        if (laender and land not in laender) or land in ausser:
            continue
        z = {
            "Bankleitzahl": str(e["iid"]),
            "BIC": e.get("bic") or "",
            "Bankenname": (e.get("bankOrInstitutionName") or "").strip(),
            "Art": ARTEN.get(e.get("iidType"), e.get("iidType") or ""),
            "Hauptsitz-IID": str(e.get("headQuarters") or ""),
            "QR-IID gehört zu": str(e.get("qrIidBelongsTo") or ""),
            "Straße": e.get("streetName") or "",
            "Hausnummer": e.get("buildingNumber") or "",
            "PLZ": e.get("postCode") or "",
            "Ort": e.get("townName") or "",
            "Sitzland": land,
            "SIC-IID": e.get("sicIid") or "",
        }
        for feld, name in TEILNAHME:
            z[name] = "ja" if e.get(feld) else "nein"
        banken.append(z)
    if not banken:
        raise RuntimeError("keine passenden Einträge in der SIX-Datei")
    banken.sort(key=lambda z: int(z[SCHLUESSEL]))
    keys = {z[SCHLUESSEL] for z in banken}
    # Überführungen: nur behalten, wenn die neue IID zu diesem Land gehört
    fusionen = sorted(
        ({"Bankleitzahl": str(e["iid"]), "Nachfolge-Bankleitzahl": str(e["newIid"])}
         for e in eintraege if e.get("entryType") == "BankMasterConcatenated" and str(e.get("newIid")) in keys),
        key=lambda z: int(z[SCHLUESSEL]))
    print(f"SIX Bank Master gültig am {daten.get('validOn')}: {len(banken)} IIDs, {len(fusionen)} Überführungen")
    return Stand(spalten=SPALTEN, banken=banken, datum=args.today.isoformat(),
                 meta={"Quelle": URL, "Fusionen": fusionen})


def api_eintrag(code: str, z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    g = z.get
    strasse = " ".join(filter(None, [leer(g("Straße")), leer(g("Hausnummer"))])) or None
    nachfolger = {f["Bankleitzahl"]: f["Nachfolge-Bankleitzahl"] for f in meta.get("Fusionen", [])}
    return {
        "land": code,
        "bankleitzahl": leer(g("Bankleitzahl")),
        "bic": leer(g("BIC")),
        "name": leer(g("Bankenname")),
        "status": None,
        "entfernt_am": None,
        "art": leer(g("Art")),
        "hauptsitz_bankleitzahl": leer(g("Hauptsitz-IID")),
        "qr_iid_gehoert_zu": leer(g("QR-IID gehört zu")),
        "nachfolge_bankleitzahl": nachfolger.get(g("Bankleitzahl")),
        "adresse": {"strasse": strasse, "plz": leer(g("PLZ")), "ort": leer(g("Ort")), "land": leer(g("Sitzland"))},
        "sic_iid": leer(g("SIC-IID")),
        "teilnahme": [name for _, name in TEILNAHME if g(name) == "ja"],
    }


def zusatz_eintraege(code: str, eintraege: dict[str, dict], meta: dict) -> dict[str, dict]:
    """Überführte IIDs, die nicht mehr im Bankenstamm stehen: Verweis auf die neue IID.
    Bereits als entfernt protokollierte IIDs bekommen die Nachfolge-IID ergänzt."""
    extra = {}
    for f in meta.get("Fusionen", []):
        alt, neu = f["Bankleitzahl"], f["Nachfolge-Bankleitzahl"]
        if neu not in eintraege:
            continue
        if alt in eintraege:  # schon als entfernt protokolliert: Nachfolger ergänzen
            if eintraege[alt]["status"] == "entfernt" and not eintraege[alt].get("nachfolge_bankleitzahl"):
                eintraege[alt]["nachfolge_bankleitzahl"] = neu
            continue
        ziel = eintraege[neu]
        extra[alt] = {
            "land": code, "bankleitzahl": alt, "bic": None, "name": ziel["name"],
            "status": "entfernt", "entfernt_am": None, "art": None, "hauptsitz_bankleitzahl": None,
            "qr_iid_gehoert_zu": None, "nachfolge_bankleitzahl": neu,
            "adresse": {"strasse": None, "plz": None, "ort": None, "land": None}, "sic_iid": None, "teilnahme": [],
        }
    return extra


def web(platzhalter: str) -> dict:
    return {
        "suche_platzhalter": platzhalter,
        "suche": ["bankleitzahl", "bic", "name", "adresse.plz", "adresse.ort", "sic_iid"],
        "filter": [{"feld": "art", "alle": "Alle Arten"}],
        "spalte5": {"titel": "Art", "feld": "art"},
        "aenderung_name": "Bankenname",
        "aenderung_bic": "BIC",
        "hinweis_aenderungen": "Täglicher Vergleich mit dem Vortag (SIX Bank Master). IIDs, die nicht mehr im "
                               "Bankenstamm stehen, bleiben hier mit ihrem letzten Stand erhalten.",
        "details": [
            ["IID (Bankleitzahl)", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"], ["Art", "art"],
            ["Hauptsitz", "hauptsitz_bankleitzahl", "blz"], ["QR-IID gehört zu", "qr_iid_gehoert_zu", "blz"],
            ["Nachfolge-IID", "nachfolge_bankleitzahl", "blz"],
            ["Adresse", "adresse", "adresse"], ["Sitzland", "adresse.land"], ["SIC-IID", "sic_iid"],
            ["Teilnahme", "teilnahme", "liste"],
        ],
    }
