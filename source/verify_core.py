"""Check the core (or LCD) variable font's component structure across its axes.

usage: python3 verify_core.py <VF.ttf> <glyph-module> [--lcd]

At 9 optical sizes × 5 element shapes × 5 expansions, every glyph decomposes to exactly one dot per
lit cell of its bitmap, centred on that cell and identical to `_dot`, and the glyf xMin equals the
hmtx side bearing (XMIN). A component that only counts as empty in the bounds (a one-point
`_anchor`) puts xMin on the first lit dot instead, and glyphs whose first column is empty
(I, l, 1, …) are drawn dots to the left.
With --lcd, also checks the colour layers: every character is its unlit cell (the fill of its own
width, palette colour 0) under itself (the text colour), and CPAL has a light and a dark palette.
"""
import sys, importlib
from features import gname, extra_glyphs, fill_name, width, CELL
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.recordingPen import DecomposingRecordingPen

path, mod = sys.argv[1], sys.argv[2]
LCD = '--lcd' in sys.argv
m = importlib.import_module(mod)
G, SC, W = m.G, getattr(m, 'SC', {}), getattr(m, 'W', {})
expect = {gname(ch): rows for ch, rows in G.items()}
expect.update({gname(ch) + '.sc': rows for ch, rows in SC.items()})
expect.update({name: rows for name, (rows, w) in extra_glyphs(G, W).items()})
P, H, XMIN = 128, 64, -3

def dots(gs, name):
    """Each contour of the decomposed glyph as (centre, bounding box size, point count)."""
    rec = DecomposingRecordingPen(gs); gs[name].draw(rec)
    out, cur = [], []
    for op, args in rec.value:
        if op in ('closePath', 'endPath'):
            if len(cur) > 2:
                xs, ys = [p[0] for p in cur], [p[1] for p in cur]
                out.append((((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2),
                            (round(max(xs) - min(xs), 6), round(max(ys) - min(ys), 6)), len(cur)))
            cur = []
        else:
            cur += args
    return out

bad = checked = 0
def fail(*msg):
    global bad
    bad += 1
    if bad < 20: print(*msg)

base = TTFont(path)
axes = {a.axisTag for a in base['fvar'].axes}
assert axes == {'opsz', 'ELSH', 'ELXP'}, axes
for opsz in [8, 12, 16, 24, 32, 48, 64, 100, 144]:
    for shape in [0, 25, 50, 75, 100]:
        for xp in [-100, -40, 0, 60, 100]:
            loc = {'opsz': opsz, 'ELSH': shape, 'ELXP': xp}
            f = instantiateVariableFont(TTFont(path), loc)
            gs, glyf, hmtx = f.getGlyphSet(), f['glyf'], f['hmtx']
            (_, dot_size, dot_pts), = dots(gs, '_dot')
            if not (0 < dot_size[0] == dot_size[1] <= 2 * (H - XMIN)) or abs(glyf['_dot'].xMin * -2 - dot_size[0]) > 2:   # xMin is rounded
                fail('_dot', loc, dot_size)
            for name, rows in expect.items():
                checked += 1
                want = {(c * P + H, (6 - r) * P + H) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == '#'}
                got = dots(gs, name)
                if {c for c, _, _ in got} != want or len(got) != len(want):
                    fail(name, loc, 'dots', sorted({c for c, _, _ in got} ^ want)[:3])
                if any((s, n) != (dot_size, dot_pts) for _, s, n in got):
                    fail(name, loc, 'a dot differs from _dot')
                if glyf[name].xMin != XMIN or hmtx[name][1] != XMIN:
                    fail(name, loc, f'xMin {glyf[name].xMin} lsb {hmtx[name][1]}')

if LCD:
    colr, cpal = base['COLR'], base['CPAL']
    if len(cpal.palettes) != 2 or list(cpal.paletteTypes) != [1, 2]:
        fail("CPAL: want a light and a dark palette", len(cpal.palettes), cpal.paletteTypes)
    layers = colr.ColorLayers
    bases = {gname(ch): width(ch, W) for ch in G}
    bases.update({gname(ch) + '.sc': CELL for ch in SC})
    for name, w in bases.items():
        checked += 1
        got = [(l.name, l.colorID) for l in layers.get(name, [])]
        if got != [(fill_name(w), 0), (name, 0xFFFF)]:
            fail('COLR', name, got)
print('checked', checked, 'glyphs; problems', bad)
sys.exit(1 if bad else 0)
