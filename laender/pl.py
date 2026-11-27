"""Polen – Elektroniczny Wykaz Identyfikatorów Bankowych (EWIB) der Polnischen Nationalbank (NBP).

- Angeboten werden XML (plewiba.xml), eine Textdatei in CP852 und eine Abfrage-Schnittstelle; verwendet
  wird das XML. Es ist nach Institut (Instytucja) → Einheit (Jednostka, z. B. Zentrale, Filiale) →
  Abrechnungsnummer (NumerRozliczeniowy) gegliedert.
- Die Abrechnungsnummer (numer rozliczeniowy) ist achtstellig und steht in der IBAN an den Stellen 5–12;
  sie ist hier die Bankleitzahl. Jede Nummer ist eine Zeile, mit Angaben zu Einheit und Institut.
- BICs stehen je Nummer als „BIC …“, „BIC SEPA …“, „BIC SORBNET 3 …“, „BIC TARGET 2 …“. Als BIC gilt der
  allgemeine, sonst der SEPA-BIC.
- Nummer und Datum der Veröffentlichung („Pub.wer.533“, „2026-11-27“) stehen nur auf der Download-Seite,
  nicht in der Datei. Die Datei ist rund 11 MB groß; sie wird nicht abgelegt, sondern bei der NBP verlinkt.
- Die NBP nennt für EWIB keine Nutzungsbedingungen. Es gelten die gesetzlichen Regeln zur Weiterverwendung
  öffentlicher Informationen (Ustawa o otwartych danych …, 2021): Quelle, Stand und Hinweis auf die
  Verarbeitung werden angegeben.
"""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET

from kern import SCHLUESSEL, Stand, herunterladen, leer

CODE = "PL"
NAME = "Polen"
BLZ_STELLEN = None
URL = "https://ewib.nbp.pl/plewiba?dokNazwa=plewiba.xml"
SEITE = "https://ewib.nbp.pl/faces/pages/daneDoPobrania.xhtml"
QUELLE = {
    "name": "Narodowy Bank Polski – Elektroniczny Wykaz Identyfikatorów Bankowych (EWIB)",
    "kurz": "NBP",
    "url": "https://ewib.nbp.pl/",
    # Keine eigenen Bedingungen der NBP für EWIB auffindbar -> gesetzliche Regeln zur Weiterverwendung (Art. 4 ff.)
    "bedingungen": "https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20210001641",
    "hinweis": "Źródło: Narodowy Bank Polski – Elektroniczny Wykaz Identyfikatorów Bankowych (EWIB), ewib.nbp.pl; "
               "dane przetworzone (umformatiert: je Abrechnungsnummer eine Zeile, Angaben zu Einheit und Institut "
               "ergänzt, Öffnungszeiten und Dienstleistungen weggelassen). Die NBP ist für diese Zusammenstellung "
               "nicht verantwortlich.",
}
ORIGINAL_URL = URL
SPALTEN = ["Bankleitzahl", "BIC", "BIC SEPA", "BIC SORBNET 3", "BIC TARGET 2", "Bezeichnung", "Institut",
           "Institutsnummer", "Institutsart", "Untertyp", "Einheit", "Art der Einheit", "Straße", "PLZ", "Ort",
           "Woiwodschaft", "Telefon", "E-Mail", "Homepage", "LEI", "NIP", "Vergeben am"]
_BIC_ARTEN = {"BIC": "BIC", "BIC SEPA": "BIC SEPA", "BIC SORBNET 3": "BIC SORBNET 3", "BIC TARGET 2": "BIC TARGET 2"}


def _version(seite: str) -> tuple[str | None, str | None]:
    """-> (Datum JJJJ-MM-TT, Veröffentlichungsnummer) der XML-Datei laut Download-Seite."""
    text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", seite)))
    m = re.search(r"plewiba\.xml.{0,400}?(\d{4}-\d{2}-\d{2})\s*Pub\.\s*wer\.\s*(\d+)", text)
    return (m.group(1), m.group(2)) if m else (None, None)


def _t(e, pfad: str) -> str:
    return (e.findtext(pfad) or "").strip() if e is not None else ""


def laden(args, alte_meta: dict) -> Stand:
    if args.input:
        roh, (ab, version) = args.input[0].read_bytes(), (None, None)
    else:
        try:
            ab, version = _version(herunterladen(SEITE).decode("utf-8", "replace"))
        except Exception as e:
            print(f"[{CODE}] Warnung: Download-Seite nicht lesbar ({e}) – Version unbekannt")
            ab, version = None, None
        roh = herunterladen(URL, timeout=300)
    root = ET.fromstring(roh)
    if root.tag != "Instytucje":
        raise RuntimeError(f"unerwartetes EWIB-Format ({root.tag})")

    banken = []
    for i in root.findall("Instytucja"):
        for j in i.findall("Jednostka"):
            a = j.find("DaneAdresowe")
            strasse = " ".join(filter(None, [_t(a, "ulica"), _t(a, "numerBudynku")]))
            for n in j.findall("NumerRozliczeniowy"):
                bics = {}
                for k in n.findall("KodyBIC"):
                    m = re.fullmatch(r"(.*?)\s+([A-Z0-9]{8}(?:[A-Z0-9]{3})?)", (k.text or "").strip())
                    if m and m.group(1) in _BIC_ARTEN:
                        bics.setdefault(_BIC_ARTEN[m.group(1)], m.group(2))
                banken.append({
                    "Bankleitzahl": _t(n, "NrRozliczeniowy"),
                    "BIC": bics.get("BIC") or bics.get("BIC SEPA", ""),
                    "BIC SEPA": bics.get("BIC SEPA", ""), "BIC SORBNET 3": bics.get("BIC SORBNET 3", ""),
                    "BIC TARGET 2": bics.get("BIC TARGET 2", ""),
                    "Bezeichnung": _t(n, "NazwaNumeru"), "Institut": _t(i, "NazwaInstytucji"),
                    "Institutsnummer": _t(i, "NrInstytucji"), "Institutsart": _t(i, "TypInstytucji"),
                    "Untertyp": _t(i, "PodtypInstytucji"), "Einheit": _t(j, "NazwaJednostki"),
                    "Art der Einheit": _t(j, "TypJednostki"), "Straße": strasse, "PLZ": _t(a, "kodPocztowy"),
                    "Ort": _t(a, "miejscowosc"), "Woiwodschaft": _t(a, "wojewodztwo"),
                    "Telefon": _t(j, "NumerTelefonu"), "E-Mail": _t(j, "AdresEmail"), "Homepage": _t(i, "WWW"),
                    "LEI": _t(i, "IdentyfikatorLEI"), "NIP": _t(i, "NIP"),
                    "Vergeben am": _t(n, "DataWygenerowania"),
                })
    banken = [z for z in banken if re.fullmatch(r"\d{8}", z[SCHLUESSEL])]
    if len({z[SCHLUESSEL] for z in banken}) != len(banken):
        raise RuntimeError("Abrechnungsnummern im EWIB-XML nicht eindeutig")
    banken.sort(key=lambda z: z[SCHLUESSEL])
    print(f"[{CODE}] EWIB {'Pub.wer.' + version if version else '(Version unbekannt)'} vom {ab or '?'}: "
          f"{len(banken)} Abrechnungsnummern, {sum(1 for z in banken if z['BIC'])} mit BIC")
    meta = {"Quelle": URL}
    if version:
        meta.update({"Version": version, "ValidFrom": ab})
    else:  # Version nicht lesbar: letzten Stand behalten
        meta.update({k: alte_meta[k] for k in ("Version", "ValidFrom") if k in alte_meta})
    neu = version and alte_meta.get("Version") != version
    datum = ab if neu and ab and ab <= args.today.isoformat() else args.today.isoformat()
    return Stand(spalten=SPALTEN, banken=banken, datum=datum, meta=meta)


# ---------------------------------------------------------------- API

def _homepage(wert):
    wert = leer(wert)
    if wert and not re.match(r"https?://", wert, re.I):
        wert = "https://" + wert
    return wert


def api_eintrag(z: dict, filialen: list, meta: dict, entfernt: bool) -> dict:
    g = lambda s: leer(z.get(s))
    weitere = [b for b in dict.fromkeys(z.get(s, "") for s in ("BIC SEPA", "BIC SORBNET 3", "BIC TARGET 2"))
               if b and b != z.get("BIC")]
    return {
        "land": CODE,
        "bankleitzahl": g("Bankleitzahl"),
        "bic": g("BIC"),
        "name": g("Institut"),
        "status": None,
        "entfernt_am": None,
        "bezeichnung": g("Bezeichnung"),
        "bics": {"sepa": g("BIC SEPA"), "sorbnet3": g("BIC SORBNET 3"), "target2": g("BIC TARGET 2")},
        "weitere_bics": weitere,
        "institutsnummer": g("Institutsnummer"),
        "institutsart": g("Institutsart"),
        "untertyp": g("Untertyp"),
        "einheit": g("Einheit"),
        "art_der_einheit": g("Art der Einheit"),
        "lei": g("LEI"),
        "nip": g("NIP"),
        "vergeben_am": g("Vergeben am"),
        "adresse": {"strasse": g("Straße"), "plz": g("PLZ"), "ort": g("Ort"), "woiwodschaft": g("Woiwodschaft")},
        "kontakt": {"telefon": g("Telefon"), "email": g("E-Mail"), "homepage": _homepage(z.get("Homepage"))},
        "version": meta.get("Version"),
    }


# ---------------------------------------------------------------- Webseite

WEB = {
    "suche_platzhalter": "Abrechnungsnummer (8-stellig), BIC, Bank, Filiale oder Ort …",
    "suche": ["bankleitzahl", "bic", "name", "bezeichnung", "einheit", "adresse.plz", "adresse.ort", "lei", "nip"],
    "suche_listen": ["weitere_bics"],
    "filter": [{"feld": "institutsart", "alle": "Alle Institutsarten"},
               {"feld": "adresse.woiwodschaft", "alle": "Alle Woiwodschaften"}],
    "spalte5": {"titel": "Einheit", "feld": "art_der_einheit"},
    "aenderung_name": "Institut",
    "aenderung_bic": "BIC",
    "hinweis_aenderungen": "Die NBP veröffentlicht EWIB bei jeder Änderung neu. Änderungen stehen unter dem Tag der "
                           "Veröffentlichung. Jede Zeile ist eine Abrechnungsnummer (Zentrale, Filiale oder andere Einheit).",
    "details": [
        ["Abrechnungsnummer (Bankleitzahl)", "bankleitzahl", "kopieren"], ["BIC", "bic", "kopieren"],
        ["BIC SEPA", "bics.sepa"], ["BIC SORBNET 3", "bics.sorbnet3"], ["BIC TARGET 2", "bics.target2"],
        ["Bezeichnung", "bezeichnung"], ["Einheit", "einheit"], ["Art der Einheit", "art_der_einheit"],
        ["Institutsnummer", "institutsnummer"], ["Institutsart", "institutsart"], ["Untertyp", "untertyp"],
        ["LEI", "lei", "lei"], ["NIP", "nip"], ["Adresse", "adresse", "adresse"], ["Woiwodschaft", "adresse.woiwodschaft"],
        ["Telefon", "kontakt.telefon"], ["E-Mail", "kontakt.email", "email"], ["Homepage", "kontakt.homepage", "url"],
        ["Vergeben am", "vergeben_am", "datum"], ["EWIB-Veröffentlichung", "version"],
    ],
}


def quellen_hinweis(meta: dict) -> str:
    """Quellenangabe mit Stand (Veröffentlichung) der verwendeten EWIB-Datei."""
    if not meta.get("Version"):
        return QUELLE["hinweis"]
    stan = f"stan na {meta['ValidFrom']}, " if meta.get("ValidFrom") else ""
    return QUELLE["hinweis"].replace("ewib.nbp.pl; ", f"ewib.nbp.pl ({stan}Pub.wer.{meta['Version']}); ")


def stand_text(meta: dict) -> str:
    if not meta.get("Version"):
        return ""
    ab = ".".join(reversed(meta["ValidFrom"].split("-"))) if meta.get("ValidFrom") else ""
    return f"EWIB Pub.wer.{meta['Version']}" + (f" vom {ab}" if ab else "")
