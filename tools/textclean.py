"""Clean text extracted from HiMCM paper PDFs with `pdftotext -layout`.

Fixes the extraction artifacts found in the corpus:

* Headings typeset in a small-caps font come out as Private Use Area code
  points U+F074E..U+F0766 (a constant offset from ASCII lowercase).
* Equations typeset with the Adobe "Symbol" font come out as U+F020..U+F0FF.
* Large bracket pieces from TeX/Word math fonts come out as U+F8E5..U+F8FE.
* Ligatures, zero-width spaces, soft hyphens and runs of layout whitespace.

Anything still unmappable is replaced by U+FFFD so a reader knows a glyph was
lost; the PDF page remains the reference for exact notation.
"""

import re

SMALLCAPS_OFFSET = 984813  # chr(ord(c) - offset) maps U+F074E.. back to 'a'..

# Adobe Symbol font, offset by U+F000.
_SYMBOL = {
    0x20: " ", 0x21: "!", 0x22: "∀", 0x23: "#", 0x24: "∃", 0x25: "%", 0x26: "&",
    0x27: "∋", 0x28: "(", 0x29: ")", 0x2A: "∗", 0x2B: "+", 0x2C: ",", 0x2D: "−",
    0x2E: ".", 0x2F: "/", 0x3A: ":", 0x3B: ";", 0x3C: "<", 0x3D: "=", 0x3E: ">",
    0x3F: "?", 0x40: "≅", 0x41: "Α", 0x42: "Β", 0x43: "Χ", 0x44: "Δ", 0x45: "Ε",
    0x46: "Φ", 0x47: "Γ", 0x48: "Η", 0x49: "Ι", 0x4A: "ϑ", 0x4B: "Κ", 0x4C: "Λ",
    0x4D: "Μ", 0x4E: "Ν", 0x4F: "Ο", 0x50: "Π", 0x51: "Θ", 0x52: "Ρ", 0x53: "Σ",
    0x54: "Τ", 0x55: "Υ", 0x56: "ς", 0x57: "Ω", 0x58: "Ξ", 0x59: "Ψ", 0x5A: "Ζ",
    0x5B: "[", 0x5C: "∴", 0x5D: "]", 0x5E: "⊥", 0x5F: "_", 0x60: "‾", 0x61: "α",
    0x62: "β", 0x63: "χ", 0x64: "δ", 0x65: "ε", 0x66: "φ", 0x67: "γ", 0x68: "η",
    0x69: "ι", 0x6A: "ϕ", 0x6B: "κ", 0x6C: "λ", 0x6D: "μ", 0x6E: "ν", 0x6F: "ο",
    0x70: "π", 0x71: "θ", 0x72: "ρ", 0x73: "σ", 0x74: "τ", 0x75: "υ", 0x76: "ϖ",
    0x77: "ω", 0x78: "ξ", 0x79: "ψ", 0x7A: "ζ", 0x7B: "{", 0x7C: "|", 0x7D: "}",
    0x7E: "∼", 0xA1: "ϒ", 0xA2: "′", 0xA3: "≤", 0xA4: "⁄", 0xA5: "∞", 0xA6: "ƒ",
    0xAB: "↔", 0xAC: "←", 0xAD: "↑", 0xAE: "→", 0xAF: "↓", 0xB0: "°", 0xB1: "±",
    0xB2: "″", 0xB3: "≥", 0xB4: "×", 0xB5: "∝", 0xB6: "∂", 0xB7: "•", 0xB8: "÷",
    0xB9: "≠", 0xBA: "≡", 0xBB: "≈", 0xBC: "…", 0xC0: "ℵ", 0xC4: "⊗", 0xC5: "⊕",
    0xC6: "∅", 0xC7: "∩", 0xC8: "∪", 0xC9: "⊃", 0xCA: "⊇", 0xCB: "⊄", 0xCC: "⊂",
    0xCD: "⊆", 0xCE: "∈", 0xCF: "∉", 0xD0: "∠", 0xD1: "∇", 0xD5: "∏", 0xD6: "√",
    0xD7: "⋅", 0xD8: "¬", 0xD9: "∧", 0xDA: "∨", 0xDB: "⇔", 0xDC: "⇐", 0xDD: "⇑",
    0xDE: "⇒", 0xDF: "⇓", 0xE1: "⟨", 0xE5: "∑", 0xE6: "⎛", 0xE7: "⎜", 0xE8: "⎝",
    0xE9: "⎡", 0xEA: "⎢", 0xEB: "⎣", 0xEC: "⎧", 0xED: "⎨", 0xEE: "⎩", 0xEF: "⎪",
    0xF1: "⟩", 0xF2: "∫", 0xF3: "⌠", 0xF4: "⎮", 0xF5: "⌡", 0xF6: "⎞", 0xF7: "⎟",
    0xF8: "⎠", 0xF9: "⎤", 0xFA: "⎥", 0xFB: "⎦", 0xFC: "⎫", 0xFD: "⎬", 0xFE: "⎭",
}
_SYMBOL.update({d: chr(d) for d in range(0x30, 0x3A)})  # digits

# Extensible bracket pieces used by TeX and Office math fonts.
_BRACKETS = {
    0xF8E6: "⏐", 0xF8E7: "⎯", 0xF8EB: "⎛", 0xF8EC: "⎜", 0xF8ED: "⎝", 0xF8EE: "⎡",
    0xF8EF: "⎢", 0xF8F0: "⎣", 0xF8F1: "⎧", 0xF8F2: "⎨", 0xF8F3: "⎩", 0xF8F4: "⎪",
    0xF8F5: "⎮", 0xF8F6: "⎞", 0xF8F7: "⎟", 0xF8F8: "⎠", 0xF8F9: "⎤", 0xF8FA: "⎥",
    0xF8FB: "⎦", 0xF8FC: "⎫", 0xF8FD: "⎬", 0xF8FE: "⎭",
}

_LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st"}

# Wingdings-style bullets that share code points with Symbol letters.
_BULLET_AT_LINE_START = re.compile(r"^(\s*)[](?=\s)", re.M)


def _map_char(c: str) -> str:
    o = ord(c)
    if 0xF074E <= o <= 0xF0767:
        return chr(o - SMALLCAPS_OFFSET)
    if 0xF020 <= o <= 0xF0FF:
        return _SYMBOL.get(o - 0xF000, "�")
    if o in _BRACKETS:
        return _BRACKETS[o]
    if 0xE000 <= o <= 0xF8FF or o >= 0xF0000:
        return "�"
    return c


def clean_page(text: str) -> str:
    """Return cleaned text for one page of `pdftotext -layout` output."""
    text = text.replace("\f", "\n")
    text = _BULLET_AT_LINE_START.sub(r"\1•", text)
    text = "".join(_map_char(c) for c in text)
    for k, v in _LIGATURES.items():
        text = text.replace(k, v)
    text = text.replace("​", "").replace("­", "-").replace("﻿", "")
    lines = []
    for line in text.splitlines():
        line = re.sub(r"[ \t ]{3,}", "  ", line.strip())
        lines.append(line)
    out = "\n".join(lines)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()
