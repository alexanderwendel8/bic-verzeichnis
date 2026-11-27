"""Excel-Dateien (.xlsx) ohne Zusatzbibliothek lesen.

Eine .xlsx ist ein ZIP-Archiv mit XML-Dateien; gelesen wird hier nur das erste Tabellenblatt,
Zellwerte als Text (Zahlen so, wie sie in der Datei stehen).
"""

from __future__ import annotations

import io
import re
import zipfile
import xml.etree.ElementTree as ET

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def xlsx_lesen(roh: bytes) -> tuple[str, list[list[str]]]:
    """-> (Name des ersten Blatts, Zeilen als Listen von Zellwerten)."""
    z = zipfile.ZipFile(io.BytesIO(roh))
    texte = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(_NS + "si"):
            texte.append("".join(t.text or "" for t in si.iter(_NS + "t")))
    blatt = ET.fromstring(z.read("xl/workbook.xml")).find(_NS + "sheets")[0].get("name", "")
    zeilen = []
    for r in ET.fromstring(z.read("xl/worksheets/sheet1.xml")).iter(_NS + "row"):
        zeile: dict[int, str] = {}
        for c in r.findall(_NS + "c"):
            spalte = re.match(r"[A-Z]+", c.get("r", "A")).group()
            idx = 0
            for ch in spalte:
                idx = idx * 26 + ord(ch) - 64
            typ, v = c.get("t"), c.find(_NS + "v")
            if typ == "inlineStr":
                wert = "".join(t.text or "" for t in c.iter(_NS + "t"))
            elif v is None:
                wert = ""
            else:
                wert = texte[int(v.text)] if typ == "s" else (v.text or "")
            zeile[idx - 1] = wert.strip()
        if zeile:
            zeilen.append([zeile.get(i, "") for i in range(max(zeile) + 1)])
    return blatt, zeilen
