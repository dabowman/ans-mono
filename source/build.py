import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import importlib
_mod = importlib.import_module(sys.argv[2] if len(sys.argv) > 2 else 'glyphs')
G = _mod.G
SC = getattr(_mod, 'SC', {})   # small caps, keyed by capital letter
W = getattr(_mod, 'W', {})     # advance widths in dots for non-cell glyphs (spaces)
from features import gname, width, extra_glyphs, fea, CELL
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from version import NAME_VERSION, FONT_REVISION, NAME_META

UPM, P = 1000, 125          # 8 pixel rows per em (7 glyph + 1 leading)
ADV = 6 * P                 # 5 px glyph + 1 px spacing
NAME = sys.argv[3] if len(sys.argv) > 3 else "Ans Mono"
OUT = sys.argv[1]

def contours(rows):
    filled = {(c, r) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == '#'}
    edges = set()
    for c, r in filled:
        x0, x1, yt, yb = c, c + 1, 7 - r, 6 - r
        # clockwise (y-up): top L->R, right down, bottom R->L, left up
        for e in (((x0, yt), (x1, yt)), ((x1, yt), (x1, yb)), ((x1, yb), (x0, yb)), ((x0, yb), (x0, yt))):
            rev = (e[1], e[0])
            if rev in edges:
                edges.remove(rev)
            else:
                edges.add(e)
    out = {}
    for a, b in edges:
        out.setdefault(a, []).append(b)
    loops = []
    while out:
        start = next(iter(out))
        pts, cur, prev_dir = [start], start, None
        while True:
            nexts = out[cur]
            if len(nexts) > 1 and prev_dir:
                # at a diagonal pinch, take the right-hand turn to keep loops apart
                def turn(n):
                    d = (n[0] - cur[0], n[1] - cur[1])
                    return prev_dir[0] * d[1] - prev_dir[1] * d[0]  # cross: <0 = right turn
                nexts.sort(key=turn)
            nxt = nexts.pop(0)
            if not nexts:
                del out[cur]
            prev_dir = (nxt[0] - cur[0], nxt[1] - cur[1])
            cur = nxt
            if cur == start:
                break
            pts.append(cur)
        # drop collinear points
        simp = []
        n = len(pts)
        for i in range(n):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
            if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
                simp.append(b)
        loops.append(simp)
    return loops

def draw(rows):
    pen = TTGlyphPen(None)
    for loop in contours(rows):
        pen.moveTo((loop[0][0] * P, loop[0][1] * P))
        for x, y in loop[1:]:
            pen.lineTo((x * P, y * P))
        pen.closePath()
    return pen.glyph()

order = ['.notdef'] + [gname(c) for c in G]
glyphs = {'.notdef': draw(('#####', '#...#', '#...#', '#...#', '#...#', '#...#', '#####', '.....'))}
cmap = {}
for ch, rows in G.items():
    glyphs[gname(ch)] = draw(rows)
    cmap[ord(ch)] = gname(ch)
adv = {'.notdef': CELL}
adv.update({gname(ch): width(ch, W) for ch in G})
for ch, rows in SC.items():
    order.append(gname(ch) + '.sc')
    glyphs[gname(ch) + '.sc'] = draw(rows)
    adv[gname(ch) + '.sc'] = CELL
for name, (rows, w) in extra_glyphs(G, W).items():     # ss01 unlit cells
    order.append(name)
    glyphs[name] = draw(rows)
    adv[name] = w

fb = FontBuilder(UPM, isTTF=True)
fb.setupGlyphOrder(order)
fb.setupCharacterMap(cmap)
fb.setupGlyf(glyphs)
def lsb(gl):
    if not gl.numberOfContours: return 0
    return min(x for x, y in gl.coordinates)
fb.setupHorizontalMetrics({n: (adv[n] * P, lsb(glyphs[n])) for n in order})
fb.setupHorizontalHeader(ascent=7 * P, descent=-P)
fb.setupNameTable({
    "familyName": NAME, "styleName": "Regular",
    "uniqueFontIdentifier": NAME.replace(' ', '') + "-Regular-" + NAME_VERSION.split()[-1],
    "fullName": NAME + " Regular", "psName": NAME.replace(' ', '') + "-Regular",
    "version": NAME_VERSION,
    **NAME_META,
})
fb.setupOS2(sTypoAscender=7 * P, sTypoDescender=-P, sTypoLineGap=0,
            usWinAscent=7 * P, usWinDescent=P, sxHeight=5 * P, sCapHeight=7 * P,
            xAvgCharWidth=ADV, achVendID="NONE",
            fsType=0)
from fontTools.ttLib.tables.O_S_2f_2 import Panose
pn = Panose(); pn.bFamilyType = 2; pn.bProportion = 9
fb.font["OS/2"].panose = pn
fb.addOpenTypeFeatures(fea(G, SC, W))
fb.setupPost(isFixedPitch=1, underlinePosition=-P // 2, underlineThickness=P)
fb.font["head"].fontRevision = FONT_REVISION
fb.save(OUT + ".ttf")
fb.font.flavor = "woff2"
fb.save(OUT + ".woff2")
fb.font.flavor = "woff"
fb.save(OUT + ".woff")
print(OUT, len(G), "glyphs +", len(SC), "small caps")
