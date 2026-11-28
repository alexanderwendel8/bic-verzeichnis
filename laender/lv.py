"""Lettland – BIC-Liste „BIC noteikšana pēc IBAN“ der Lettischen Zentralbank (Latvijas Banka).

- Angeboten wird nur eine Excel-Datei im alten Format (.xls), die sich ohne Zusatzbibliothek nicht lesen
  lässt. Dieselbe Tabelle steht auf der Seite als HTML; sie wird hier gelesen, die .xls-Datei verlinkt.
- Der Bankcode besteht aus vier Buchstaben (IBAN-Stellen 5–8) und entspricht den ersten vier Zeichen des
  BIC. In der Tabelle steht der BIC in zwei Teilen (Bankcode und Rest, z. B. „CBBR“ + „LV22XXX“).
- Die Seite nennt das Datum der letzten Aktualisierung („Aktualizēts 06.07.2026.“).
- Latvijas Banka nennt für diese Liste keine eigenen Bedingungen. Angewandt werden ihre Bedingungen für
  statistische Informationen: Latvijas Banka als Quelle nennen, Daten nicht verfälschen.
- Der Server lehnt Anfragen mit dem Standard-User-Agent von Python ab und bricht Verbindungen gelegentlich
  ab; geladen wird mit eigenem User-Agent und bis zu vier Versuchen.
"""

from __future__ import annotations

import html
import re
import time
import urllib.parse

from kern import SCHLUESSEL, Stand, herunterladen, leer

CODE = "LV"
NAME = "Lettland"
BLZ_STELLEN = None
SEITE = "https://www.bank.lv/darbibas-jomas/maksajumu-sistemas-uzdevumi/bic-noteiksana-pec-iban"
QUELLE = {
    "name": "Latvijas Banka – BIC noteikšana pēc IBAN",
    "kurz": "Latvijas Banka",
    "url": SEITE,
    # Keine eigenen Bedingungen für die Liste; „Datu izmantošana“: Latvijas Banka als Quelle nennen, nicht verfälschen
    "bedingungen": "https://www.bank.lv/statistika/informacija-statistikas-lietotajiem/datu-izmantosana",
    "hinweis": "Avots: Latvijas Banka – BIC noteikšana pēc IBAN. Inhalt unverändert übernommen, nur umformatiert "
               "(BIC aus zwei Spalten zusammengesetzt); die Originaldatei steht bei der Latvijas Banka.",
}
SPALTEN = ["Bankleitzahl", "BIC", "Bankenname", "IBAN-Struktur"]


def _holen(url: str) -> bytes:
    for versuch in range(4):
        try:
            return herunterladen(url, timeout=120)
        except Exception as e:
            if versuch == 3:
                raise
            print(f"[{CODE}] Download fehlgeschlagen ({e}) – neuer Versuch")
            time.sleep(5 * (versuch + 1))


def _zelle(wert: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", wert)).replace("\xa0", " ")).strip()


def tabelle_lesen(seite: str) -> tuple[list[dict], str | None, str | None]:
    """-> (Einträge, Datum der Aktualisierung JJJJ-MM-TT, Link zur .xls-Datei)."""
    banken = []
    for tabelle in re.findall(r"(?s)<table.*?</table>", seite):
        for tr in re.findall(r"(?s)<tr.*?</tr>", tabelle):
            z = [_zelle(c) for c in re.findall(r"(?s)<t[dh][^>]*>(.*?)</t[dh]>", tr)]
            if len(z) < 6 or not re.fullmatch(r"LV\*\*[A-Z]{4}", z[2].replace(" ", "")):
                continue
            code, bic = z[2].replace(" ", "")[4:], (z[4] + z[5]).replace(" ", "").upper()
            if not bic.startswith(code) or not re.fullmatch(r"[A-Z0-9]{8}([A-Z0-9]{3})?", bic):
                raise RuntimeError(f"unerwartete Zeile in der BIC-Liste: {z}")
            banken.append({"Bankleitzahl": code, "BIC": bic, "Bankenname": z[1],
                           "IBAN-Struktur": f"{z[2]} {z[3]}".strip()})
    m = re.search(r"Aktualizēts\s*(?:<[^>]+>\s*)*(\d{2})\.(\d{2})\.(\d{4})", seite)
    ab = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None
    links = re.findall(r'href="([^"]*BIC_IBAN/bic_saraksts[^"]*\.xls)"', seite)
    return banken, ab, urllib.parse.urljoin(SEITE, html.unescape(links[0])) if links else None


def laden(args, alte_meta: dict) -> Stand:
    seite = (args.input[0].read_bytes() if args.input else _holen(SEITE)).decode("utf-8", "replace")
    banken, ab, xls = tabelle_lesen(seite)
    if not banken:
        raise RuntimeError("keine Einträge in der BIC-Tabelle der Latvijas Banka gefunden – Seite geändert?")
    if len({z[SCHLUESSEL] for z in banken}) != len(banken):
        raise RuntimeError("Bankcodes in der BIC-Tabelle nicht eindeutig")
    banken.sort(key=lambda z: z[SCHLUESSEL])
    print(f"[{CODE}] BIC-Liste aktualisiert {ab or '?'}: {len(banken)} Banken")
    meta = {"Quelle": SEITE, "ValidFrom": ab or alte_meta.get("ValidFrom"), "Originaldatei": xls or alte_meta.get("Originaldatei")}
    meta = {k: v for k, v in meta.items() if v}
    neu = ab and alte_meta.get("ValidFrom") != ab and ab <= args.today.isoformat()
    return Stand(spalten=SPALTEN, banken=banken, datum=ab if neu else args.today.isoformat(), meta=meta)


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
        "iban_struktur": g("IBAN-Struktur"),
        "gueltig_ab": meta.get("ValidFrom"),
    }


# ---------------------------------------------------------------- Webseite

WEB = {
    "suche_platzhalter": "Bankcode (4 Buchstaben), BIC oder Name …",
    "suche": ["bankleitzahl", "bic", "name"],
    "filter": [],
    "spalte5": {"titel": "IBAN-Struktur", "feld": "iban_struktur"},
    "aenderung_name": "Bankenname",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Die Latvijas Banka aktualisiert die Liste bei Bedarf. Änderungen stehen unter dem Tag der "
                           "Aktualisierung. Der Bankcode sind die ersten vier Buchstaben des BIC.",
    "details": [
        ["Bankcode", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"], ["IBAN-Struktur", "iban_struktur"],
        ["Liste aktualisiert", "gueltig_ab", "datum"],
    ],
}


def original_url(meta: dict) -> str | None:
    """Link zur .xls-Datei der Latvijas Banka (Name wechselt je Version)."""
    return meta.get("Originaldatei")


def stand_text(meta: dict) -> str:
    if not meta.get("ValidFrom"):
        return ""
    return f"Liste aktualisiert am {'.'.join(reversed(meta['ValidFrom'].split('-')))}"
