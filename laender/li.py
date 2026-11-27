"""Liechtenstein – SIX Bank Master, nur IIDs mit Sitzland LI."""

from __future__ import annotations

from laender import _six

CODE = "LI"
NAME = "Liechtenstein"
BLZ_STELLEN = 5
QUELLE = _six.QUELLE
WEB = _six.web("IID, BIC, Bankname oder Ort …")


def laden(args, alte_meta: dict):
    return _six.stand(args, laender={"LI"})


def api_eintrag(z, filialen, meta, entfernt):
    return _six.api_eintrag(CODE, z, filialen, meta, entfernt)


def zusatz_eintraege(eintraege, meta):
    return _six.zusatz_eintraege(CODE, eintraege, meta)


def stand_text(meta: dict) -> str:
    return ""
