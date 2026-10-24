"""Builds the McCurdy Coatings logo set as SVGs with all lettering converted to outlines,
so sign shops, embroiderers and printers get exact shapes without needing the fonts.

    python scripts/build_logo.py <Cinzel.ttf> <DMSans.ttf>

Fonts (SIL Open Font License): Cinzel and DM Sans from github.com/google/fonts.
Writes brand/logo-*.svg.
"""
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

OUT = Path(__file__).resolve().parent.parent / "brand"

NAVY = "#0E2A47"
GREEN = "#1E8A4C"
GREEN_LIGHT = "#9FD8B6"
INK = "#0B0F14"
WHITE = "#FFFFFF"
STEEL = "#B9C4CF"


def load(path, **axes):
    font = TTFont(path)
    if "fvar" in font:
        font = instantiateVariableFont(font, axes)
    return font


def text_path(font, text, x, baseline, size, tracking=0.0):
    """SVG path data for `text` with its baseline at y=baseline, left edge at x. tracking in em."""
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    scale = size / upm
    d, cursor = [], x
    for ch in text:
        name = cmap.get(ord(ch))
        if name is None:
            continue
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, cursor, baseline)))
        d.append(pen.getCommands())
        cursor += glyphs[name].width * scale + tracking * size
    width = cursor - x - tracking * size
    return " ".join(d), width


def shield(x, y, w, h):
    """Crest outline: a shallow low-slope roof ridge on top, straight sides, tapered point."""
    ridge = h * 0.10
    side = h * 0.58
    return (f"M{x},{y + ridge} L{x + w / 2},{y} L{x + w},{y + ridge} L{x + w},{y + side} "
            f"C{x + w},{y + h * 0.80} {x + w * 0.72},{y + h * 0.92} {x + w / 2},{y + h} "
            f"C{x + w * 0.28},{y + h * 0.92} {x},{y + h * 0.80} {x},{y + side} Z")


def mark(cinzel, x, y, w, field=NAVY, ink=WHITE, accent=GREEN, accent2=GREEN_LIGHT, primer=STEEL, simple=False):
    """The crest: navy shield, keyline, roof ridge, Cinzel M, and three coat bands (primer, base, top)."""
    h = w * 1.18
    parts = [f'<path d="{shield(x, y, w, h)}" fill="{field}"/>']
    if simple:
        # Small-size mark (favicons, 32 px and below): shield and a larger M only.
        m_size = w * 0.66
        _, mw = text_path(cinzel, "M", 0, 0, m_size)
        d, _ = text_path(cinzel, "M", x + (w - mw) / 2, y + h * 0.70, m_size)
        parts.append(f'<path d="{d}" fill="{ink}"/>')
        return "\n  ".join(parts), h
    inset = w * 0.06
    parts.append(f'<path d="{shield(x + inset, y + inset * 1.15, w - 2 * inset, h - 2.3 * inset)}" '
                 f'fill="none" stroke="{ink}" stroke-opacity="0.55" stroke-width="{w * 0.012:.2f}"/>')
    # roof ridge over the monogram
    rx0, rx1, ry = x + w * 0.20, x + w * 0.80, y + h * 0.29
    parts.append(f'<path d="M{rx0},{ry} L{x + w / 2},{ry - h * 0.075} L{rx1},{ry}" fill="none" stroke="{accent}" '
                 f'stroke-width="{w * 0.045:.2f}" stroke-linecap="square" stroke-linejoin="miter"/>')
    m_size = w * 0.50
    d, mw = text_path(cinzel, "M", 0, 0, m_size)
    mx = x + (w - mw) / 2
    d, _ = text_path(cinzel, "M", mx, y + h * 0.66, m_size)
    parts.append(f'<path d="{d}" fill="{ink}"/>')
    # three coats: primer / base / top
    bw, bh, gap = w * 0.46, h * 0.022, h * 0.022
    by = y + h * 0.72
    for i, col in enumerate([primer, accent2, accent]):
        bx = x + (w - bw * (1 - i * 0.12)) / 2
        parts.append(f'<rect x="{bx:.2f}" y="{by + i * (bh + gap):.2f}" width="{bw * (1 - i * 0.12):.2f}" '
                     f'height="{bh:.2f}" fill="{col}"/>')
    return "\n  ".join(parts), h


def svg(width, height, body, label, bg=None):
    rect = f'<rect width="{width}" height="{height}" fill="{bg}"/>\n  ' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
            f'width="{width:.0f}" height="{height:.0f}" role="img" aria-label="{label}">\n  {rect}{body}\n</svg>\n')


def lockup(cinzel, dm, dark_bg=False, one_color=None, tagline=True):
    """Horizontal logo: crest + McCURDY / COATINGS / tagline. one_color = a single ink for vinyl/embroidery."""
    word = WHITE if dark_bg else NAVY
    sub = GREEN_LIGHT if dark_bg else GREEN
    tag = "#C9D3DD" if dark_bg else "#5B6573"
    field = GREEN if dark_bg else NAVY
    if one_color:
        word = sub = tag = field = one_color
    crest, ch = mark(cinzel, 0, 0, 200, field=field, accent=WHITE if (dark_bg or one_color) else GREEN,
                     accent2=WHITE if one_color else GREEN_LIGHT, primer=WHITE if one_color else STEEL)
    tx = 250
    d1, w1 = text_path(cinzel, "McCURDY", tx, 118, 112, tracking=0.02)
    d2, w2 = text_path(dm, "COATINGS", tx + 4, 178, 44, tracking=0.42)
    d3, w3 = text_path(dm, "COMMERCIAL ROOF RENEWAL  ·  EST. 1985", tx + 4, 226, 22, tracking=0.16)
    rule_y = 140
    width = tx + max(w1, w2, w3 if tagline else 0) + 10
    body = "\n  ".join([
        crest,
        f'<path d="{d1}" fill="{word}"/>',
        f'<rect x="{tx + 4}" y="{rule_y}" width="{w1 - 4:.1f}" height="3" fill="{sub}"/>',
        f'<path d="{d2}" fill="{sub}"/>',
    ] + ([f'<path d="{d3}" fill="{tag}"/>'] if tagline else []))
    return body, width, ch


def stacked(cinzel, dm, dark_bg=False):
    word = WHITE if dark_bg else NAVY
    sub = GREEN_LIGHT if dark_bg else GREEN
    field = GREEN if dark_bg else NAVY
    _, w1 = text_path(cinzel, "McCURDY", 0, 0, 112, tracking=0.02)
    _, w2 = text_path(dm, "COATINGS", 0, 0, 44, tracking=0.42)
    _, w3 = text_path(dm, "EST. 1985", 0, 0, 24, tracking=0.3)
    width = max(w1, w2) + 40
    crest, ch = mark(cinzel, (width - 260) / 2, 0, 260, field=field, accent=WHITE if dark_bg else GREEN)
    y = ch + 140
    d1, _ = text_path(cinzel, "McCURDY", (width - w1) / 2, y, 112, tracking=0.02)
    d2, _ = text_path(dm, "COATINGS", (width - w2) / 2, y + 70, 44, tracking=0.42)
    d3, _ = text_path(dm, "EST. 1985", (width - w3) / 2, y + 124, 24, tracking=0.3)
    body = "\n  ".join([crest, f'<path d="{d1}" fill="{word}"/>', f'<path d="{d2}" fill="{sub}"/>',
                        f'<path d="{d3}" fill="{word}" fill-opacity="0.7"/>'])
    return body, width, y + 140


def main(cinzel_path, dm_path):
    cinzel = load(cinzel_path, wght=700)
    dm = load(dm_path, wght=600, opsz=14)
    OUT.mkdir(exist_ok=True)

    body, h = mark(cinzel, 20, 20, 400)
    (OUT / "logo-crest.svg").write_text(svg(440, h + 40, body, "McCurdy Coatings crest"))

    for dark, name in [(False, "logo-horizontal.svg"), (True, "logo-horizontal-white.svg")]:
        body, w, h = lockup(cinzel, dm, dark)
        pad = 30
        (OUT / name).write_text(svg(w + 2 * pad, h + 2 * pad, f'<g transform="translate({pad},{pad})">{body}</g>',
                                    "McCurdy Coatings"))

    # Compact (no tagline) for small uses: business-card fronts, email signatures, shirt chests
    body, w, h = lockup(cinzel, dm, tagline=False)
    (OUT / "logo-horizontal-compact.svg").write_text(
        svg(w + 60, h + 60, f'<g transform="translate(30,30)">{body}</g>', "McCurdy Coatings"))
    # One-color versions for vinyl, embroidery, stamps and single-color print
    for ink, name in [(INK, "logo-horizontal-black.svg")]:
        body, w, h = lockup(cinzel, dm, one_color=ink)
        (OUT / name).write_text(svg(w + 60, h + 60, f'<g transform="translate(30,30)">{body}</g>', "McCurdy Coatings"))
    body, h = mark(cinzel, 20, 20, 400, field=INK, accent=WHITE, accent2=WHITE, primer=WHITE)
    (OUT / "logo-crest-black.svg").write_text(svg(440, h + 40, body, "McCurdy Coatings crest, one color"))
    # Reversed crest for navy or dark backgrounds (a navy shield disappears there)
    body, h = mark(cinzel, 20, 20, 400, field=GREEN, accent=WHITE)
    (OUT / "logo-crest-reversed.svg").write_text(svg(440, h + 40, body, "McCurdy Coatings crest, for dark backgrounds"))
    # Simplified mark for 32 px and below (favicon, app badge, hard-hat sticker under 1 in.)
    body, h = mark(cinzel, 20, 20, 400, simple=True)
    (OUT / "logo-favicon.svg").write_text(svg(440, h + 40, body, "McCurdy Coatings"))

    for dark, name in [(False, "logo-stacked.svg"), (True, "logo-stacked-white.svg")]:
        body, w, h = stacked(cinzel, dm, dark)
        (OUT / name).write_text(svg(w, h, body, "McCurdy Coatings"))

    # Square app/profile icon on navy
    body, h = mark(cinzel, 112, 70, 288, field=NAVY)
    (OUT / "logo-mark.svg").write_text(svg(512, 512, body, "McCurdy Coatings", bg="#0B1E33"))
    print("wrote", sorted(p.name for p in OUT.glob("logo-*.svg")))


if __name__ == "__main__":
    main(*sys.argv[1:3])
