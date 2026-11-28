"""Text aus einfachen PDF-Dateien lesen, ohne Zusatzbibliothek.

Reicht für Tabellen, die mit Office-Programmen erzeugt wurden (z. B. Microsoft Word): Inhalts-Streams
mit FlateDecode (zlib), Schriften vom Typ TrueType/Type1 (Literal-Strings) oder Type0 (zwei Byte je
Zeichen) mit ToUnicode-Tabelle. Nicht unterstützt: Objekt-Streams (/ObjStm), verschlüsselte PDFs,
andere Filter. Das Ergebnis sind Textzeilen je Seite, von oben nach unten, links nach rechts.
"""

from __future__ import annotations

import re
import zlib
from collections import defaultdict

_ESC = {ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12, ord("("): 40, ord(")"): 41, ord("\\"): 92}
_OPS = re.compile(
    rb"/([A-Za-z0-9_.+-]+)\s+[-\d.]+\s+Tf"                       # Schrift
    rb"|([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+Tm"  # Textmatrix (x, y)
    rb"|(\[(?:[^\]\\]|\\.)*\])\s*TJ"                             # Text mit Abständen
    rb"|(\((?:[^)\\]|\\.)*\))\s*Tj"                              # Text (Literal)
    rb"|(<[0-9A-Fa-f\s]*>)\s*Tj",                                # Text (Hex)
    re.S)


def _objekte(d: bytes) -> dict[int, bytes]:
    return {int(m.group(1)): m.group(2) for m in re.finditer(rb"(\d+)\s+\d+\s+obj\b(.*?)endobj", d, re.S)}


def _strom(body: bytes) -> bytes:
    m = re.search(rb"stream\r?\n(.*?)\r?\nendstream", body, re.S)
    if not m:
        return b""
    daten = m.group(1)
    if b"/FlateDecode" in body.split(b"stream", 1)[0]:
        try:
            return zlib.decompress(daten)
        except zlib.error:
            return zlib.decompressobj().decompress(daten)
    return daten


def _cmap(s: bytes) -> dict[int, str]:
    tab: dict[int, str] = {}
    for blk in re.findall(rb"beginbfchar(.*?)endbfchar", s, re.S):
        for a, b in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            tab[int(a, 16)] = bytes.fromhex(b.decode()).decode("utf-16-be", "replace")
    for blk in re.findall(rb"beginbfrange(.*?)endbfrange", s, re.S):
        for a, b, c in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            start, ende, ziel = int(a, 16), int(b, 16), int(c, 16)
            for i in range(start, ende + 1):
                tab[i] = chr(ziel + i - start)
    return tab


def _literal(b: bytes) -> bytes:
    out, i = bytearray(), 0
    while i < len(b):
        c = b[i]
        if c == 0x5C and i + 1 < len(b):
            n = b[i + 1]
            if n in _ESC:
                out.append(_ESC[n]); i += 2
            elif 48 <= n <= 55:
                j = i + 1
                while j < len(b) and j < i + 4 and 48 <= b[j] <= 55:
                    j += 1
                out.append(int(b[i + 1:j], 8) & 255); i = j
            else:
                i += 2  # Zeilenfortsetzung o. Ä.
            continue
        out.append(c); i += 1
    return bytes(out)


def zeilen(d: bytes) -> list[str]:
    """-> Textzeilen aller Seiten (Fragmente einer Zeile in x-Reihenfolge zusammengefügt)."""
    if b"/Encrypt" in d:
        raise RuntimeError("PDF ist verschlüsselt")
    o = _objekte(d)
    schriften = {}
    for n, b in o.items():
        if re.search(rb"/Type\s*/Font\b", b):
            m = re.search(rb"/ToUnicode\s+(\d+)\s+0\s+R", b)
            schriften[n] = (_cmap(_strom(o.get(int(m.group(1)), b""))) if m else {}, b"/Type0" in b)
    stuecke: dict[tuple[int, int], list[tuple[float, str]]] = defaultdict(list)
    seite = 0
    for n, b in sorted(o.items()):
        if not re.search(rb"/Type\s*/Page\b", b):
            continue
        seite += 1
        res = b
        m = re.search(rb"/Resources\s+(\d+)\s+0\s+R", b)
        if m:
            res = o.get(int(m.group(1)), b"")
        fonts = {k.decode(): int(v) for k, v in re.findall(rb"/([A-Za-z0-9_.+-]+)\s+(\d+)\s+0\s+R", res)}
        m = re.search(rb"/Contents\s*(\[[^\]]*\]|\d+\s+0\s+R)", b)
        inhalt = b"".join(_strom(o.get(int(c), b"")) for c in re.findall(rb"(\d+)\s+0\s+R", m.group(1))) if m else b""
        tab, zwei, x, y = {}, False, 0.0, 0.0
        for m in _OPS.finditer(inhalt):
            if m.group(1):
                tab, zwei = schriften.get(fonts.get(m.group(1).decode(), -1), ({}, False))
                continue
            if m.group(2):
                x, y = float(m.group(6)), float(m.group(7))
                continue
            text = ""
            for h, lit in re.findall(rb"<([0-9A-Fa-f\s]*)>|\(((?:[^)\\]|\\.)*)\)", m.group(8) or m.group(9) or m.group(10)):
                if h or not lit:
                    roh = bytes.fromhex(re.sub(rb"\s", b"", h).decode() or "")
                    schritt = 2 if zwei else 1
                    for i in range(0, len(roh), schritt):
                        code = int.from_bytes(roh[i:i + schritt], "big")
                        text += tab.get(code, "" if zwei else chr(code))
                else:
                    roh = _literal(lit)
                    text += "".join(tab.get(c, bytes([c]).decode("cp1252", "replace")) for c in roh) if tab \
                        else roh.decode("cp1252", "replace")
            stuecke[(seite, -round(y))].append((x, text))
    return [re.sub(r"\s+", " ", "".join(t for _, t in sorted(stuecke[k], key=lambda s: s[0]))).strip()
            for k in sorted(stuecke)]
