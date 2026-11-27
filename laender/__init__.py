"""Alle unterstützten Länder. Ein neues Land = ein Modul in diesem Ordner + ein Eintrag hier.

Jedes Land-Modul stellt bereit:
  CODE, NAME            Ländercode (ISO, Großbuchstaben) und Anzeigename
  BLZ_STELLEN           Stellen der Bankleitzahl in der IBAN, falls kürzere Schreibweisen
                        zusätzlich abrufbar sein sollen (sonst None)
  QUELLE                dict mit name, kurz, url, bedingungen
  laden(args, alte_meta) -> kern.Stand
  api_eintrag(zeile, filialen, meta, entfernt) -> dict   (mit Platzhaltern status / entfernt_am)
  WEB                   Einstellungen für die Webseite (Suche, Filter, Detailfelder …)
  stand_text(meta)      kurzer Text zur verwendeten Quelldatei (oder "")
Optional:
  zusatz_eintraege(eintraege, meta) -> dict   weitere API-Einträge, z. B. überführte Bankleitzahlen
  zusatz_hinweis(meta) -> str                 weiterer Pflichthinweis, z. B. SWIFT-Hinweis für BICs von GLEIF
  ORIGINAL                                    Name der unverändert beigelegten Originaldatei in data/<land>/
  ORIGINAL_URL                                stattdessen Link zur Originaldatei bei der Quelle
"""

from laender import at, be, ch, cz, de, es, hu, it, li, si, sk

# Reihenfolge = Reihenfolge der Länderknöpfe auf der Webseite
LAENDER = {m.CODE: m for m in (at, de, ch, li, it, cz, sk, hu, si, be, es)}
