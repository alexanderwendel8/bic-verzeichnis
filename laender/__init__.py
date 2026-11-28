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
  quellen_hinweis(meta) -> str                Quellenangabe mit Stand der Daten (statt QUELLE["hinweis"])
  ORIGINAL                                    Name der unverändert beigelegten Originaldatei in data/<land>/
  ORIGINAL_URL                                stattdessen Link zur Originaldatei bei der Quelle
  original_url(meta) -> str                   dasselbe, wenn der Link je Version wechselt
"""

from laender import at, be, ch, cy, cz, de, ee, es, fr, gr, hr, hu, it, li, lt, lv, mt, nl, pl, ro, si, sk

# Reihenfolge = Reihenfolge der Länderknöpfe auf der Webseite
LAENDER = {m.CODE: m for m in (at, de, ch, li, it, cz, sk, hu, si, be, es, fr, pl, lv, lt, ee, nl, hr, ro, cy, gr, mt)}
