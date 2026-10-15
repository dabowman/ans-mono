"""Check the core variable font's component structure at 9 optical sizes.

usage: python3 verify_core.py <core-VF.ttf> <glyph-module>

Every glyph decomposes to exactly one square `_dot` per lit cell of its bitmap, centred on that
cell, and the glyf xMin equals the hmtx side bearing (XMIN). A component that only counts as empty
in the bounds (a one-point `_anchor`) puts xMin on the first lit dot instead, and glyphs whose
first column is empty (I, l, 1, …) are drawn dots to the left.
"""
import sys, importlib
from features import gname, extra_glyphs
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.recordingPen import DecomposingRecordingPen

path, mod = sys.argv[1], sys.argv[2]
m = importlib.import_module(mod)
G, SC, W = m.G, getattr(m, 'SC', {}), getattr(m, 'W', {})
expect = {gname(ch): rows for ch, rows in G.items()}
expect.update({gname(ch) + '.sc': rows for ch, rows in SC.items()})
expect.update({name: rows for name, (rows, w) in extra_glyphs(G, W).items()})
P, H, XMIN = 128, 64, -3

bad = checked = 0
for opsz in [8, 12, 16, 24, 32, 48, 64, 100, 144]:
    f = instantiateVariableFont(TTFont(path), {'opsz': opsz})
    gs, glyf, hmtx = f.getGlyphSet(), f['glyf'], f['hmtx']
    for name, rows in expect.items():
        checked += 1
        want = {(c * P + H, (6 - r) * P + H) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == '#'}
        rec = DecomposingRecordingPen(gs); gs[name].draw(rec)
        got, cur, sizes = set(), [], set()
        for op, args in rec.value:
            if op in ('moveTo', 'lineTo'):
                cur.append(args[0])
            else:
                if len(cur) == 4:
                    xs, ys = [p[0] for p in cur], [p[1] for p in cur]
                    got.add(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2))
                    sizes.add((round(max(xs) - min(xs), 6), round(max(ys) - min(ys), 6)))
                cur = []
        problem = []
        if got != want: problem.append(f'dots {sorted(got ^ want)[:3]}')
        if len(sizes) > 1 or any(w != h for w, h in sizes): problem.append(f'dot sizes {sizes}')
        if glyf[name].xMin != XMIN or hmtx[name][1] != XMIN:
            problem.append(f'xMin {glyf[name].xMin} lsb {hmtx[name][1]}')
        if problem:
            bad += 1
            if bad < 20: print(name, opsz, '; '.join(problem))
print('checked', checked, 'glyphs; problems', bad)
sys.exit(1 if bad else 0)
