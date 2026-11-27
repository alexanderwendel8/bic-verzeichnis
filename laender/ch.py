"""Schweiz – SIX Bank Master. Enthält alle IIDs außer denen mit Sitz in Liechtenstein,
also auch ausländische Teilnehmer am Schweizer Zahlungsverkehr (Sitzland steht dabei)."""

from __future__ import annotations

from laender import _six

CODE = "CH"
NAME = "Schweiz"
BLZ_STELLEN = 5  # IID in der IBAN fünfstellig (100 -> 00100)
QUELLE = _six.QUELLE
WEB = _six.web("IID, BIC, Bankname oder Ort …")


def laden(args, alte_meta: dict):
    return _six.stand(args, laender=set(), ausser={"LI"})


def api_eintrag(z, filialen, meta, entfernt):
    return _six.api_eintrag(CODE, z, filialen, meta, entfernt)


def zusatz_eintraege(eintraege, meta):
    return _six.zusatz_eintraege(CODE, eintraege, meta)


def stand_text(meta: dict) -> str:
    return ""
