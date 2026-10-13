import sys, importlib
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
path, mod = sys.argv[1], sys.argv[2]
G = importlib.import_module(mod).G
base = TTFont(path)
print('avar', {k: len(v) for k, v in base['avar'].segments.items()})
bad = 0; checked = 0
for opsz in [8, 12, 16, 24, 32, 48, 64, 100, 144]:
    for s in [-8, -6, -4.4, -4, -1, 0, 0.3, 2, 4, 4.4, 6, 7, 8]:
        f = TTFont(path)
        inst = instantiateVariableFont(f, {'opsz': opsz, 'SCRL': s})
        k = round(s)
        glyf = inst['glyf']
        for ch, rows in G.items():
            name = 'space' if ch == ' ' else 'uni%04X' % ord(ch)
            rows = list(rows) + ['.....'] * (8 - len(rows))
            g = glyf[name]; coords, ends = g.getCoordinates(glyf)[0], g.endPtsOfContours
            assert min(x for x, y in coords) == -3, (ch, 'xMin', opsz, s, min(x for x, y in coords), coords[0])
            start = 1
            for e in ends[1:]:
                pts = coords[start:e + 1]; start = e + 1
                xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                w, h = max(xs) - min(xs), max(ys) - min(ys)
                c = int((min(xs) + max(xs)) / 2 // 128); r = 6 - int((min(ys) + max(ys)) / 2 // 128)
                src = r + k
                on = 0 <= src < 8 and rows[src][c] == '#'
                checked += 1
                if on and (w < 90 or w != h): bad += 1; print('weak', ch, opsz, s, w, h)
                if not on and (w or h): bad += 1; print('speck', ch, opsz, s, w, h) if bad < 20 else None
print('checked', checked, 'dots; problems', bad)
sys.exit(1 if bad else 0)
