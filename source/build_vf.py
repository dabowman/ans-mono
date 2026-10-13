"""Variable builds.

usage: python3 build_vf.py <out-stem> <glyph-module> "<Family Name>" [--scroll]

Core file (default): one axis, opsz.
Scroll file (--scroll): opsz + SCRL. Ship it only where something actually animates.

opsz  Optical size 8–144. Every dot is its own square, inset from its cell by an amount that
      depends on opsz: overlapping (solid) up to 16px, opening into a visible LCD grid at display
      sizes. Two masters; the gap curve lives in the avar map, not in extra masters.
SCRL  Scroll -8–8, in whole dot rows. The 8-row cell is a fixed window; the bitmap slides through
      it by switching dots on and off (an off dot is a zero-area contour on its own centre), so the
      grid never moves. -8..0 rises in from below, 8..0 drops in from above. A stepped avar map
      holds every whole row flat, so a linear animation steps row by row with no half-lit dots.

Geometry is all integers (UPM 1024, 128 units per dot, even half-dot), so every master's points
are exact and an off dot interpolates to exactly zero area at every opsz.
Every glyph also carries a one-point contour at x = XMIN, so xMin is the same in every master and
the hmtx side bearing always matches the outline. Without it, glyphs whose first column is empty
(I, l, 1, …) were drawn a dot to the left.
"""
import sys, os, importlib, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from fontTools.ttLib.tables.ttProgram import Program
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor
from fontTools import varLib
from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib.tables.O_S_2f_2 import Panose
from version import NAME_VERSION, FONT_REVISION, NAME_META

OUT, MOD, NAME = sys.argv[1], sys.argv[2], sys.argv[3]
SCROLL_AXIS = '--scroll' in sys.argv
_mod = importlib.import_module(MOD)
G = _mod.G
SC = getattr(_mod, 'SC', {})   # small caps (unencoded; smcp / c2sc)
PS = NAME.replace(' ', '') + ('Scroll' if SCROLL_AXIS else '')

UPM, P, H = 1024, 128, 64      # 8 dot rows per em; H = half a dot
ADV = 6 * P
ROWS, COLS = 8, 5

# opsz masters: inset per side in font units. -3 = dots overlap (solid); 13 = gap of 26/128 ≈ 20%.
INSET_MIN, INSET_MAX = -3, 13
XMIN = min(0, INSET_MIN)          # leftmost any dot ever reaches; also every glyph's lsb
# avar: user opsz -> design. Design runs 8..144 linearly in inset, so this table IS the gap curve:
# solid to 16px, ~8% gap at 32, ~16% at 72, ~20% at 144.
OPSZ_MAP = [(8, 8), (16, 8), (32, 76), (72, 118.5), (144, 144)]
SCROLL = range(-8, 9)

def stepped_map():
    """user -> design: each whole row held flat from k-0.45 to k+0.45, a quick ramp between."""
    pts = []
    for k in SCROLL:
        lo, hi = max(k - 0.45, -8), min(k + 0.45, 8)
        if k == -8: pts += [(-8, -8), (hi, -8)]
        elif k == 8: pts += [(lo, 8), (8, 8)]
        elif k == 0: pts += [(lo, 0), (0, 0), (hi, 0)]
        else: pts += [(lo, k), (hi, k)]
    return pts

def gname(ch):
    return 'space' if ch == ' ' else 'uni%04X' % ord(ch)

NOTDEF = ['#####', '#...#', '#...#', '#...#', '#...#', '#...#', '#####', '.....']

def draw(rows, inset, shift):
    """shift = SCRL value: display row r shows source row r + shift."""
    rows = list(rows) + ['.....'] * (ROWS - len(rows))
    cols = [c for c in range(COLS) if any(row[c] == '#' for row in rows)]
    coords, ends = [(XMIN, 0)], [0]                    # left anchor: xMin is XMIN in every master
    for c in cols:
        for r in range(ROWS) if SCROLL_AXIS else [r for r in range(ROWS) if rows[r][c] == '#']:
            src = r + shift
            on = 0 <= src < ROWS and rows[src][c] == '#'
            cx, cy = c * P + H, (6 - r) * P + H
            h = (H - inset) if on else 0
            coords += [(cx - h, cy + h), (cx + h, cy + h), (cx + h, cy - h), (cx - h, cy - h)]
            ends.append(len(coords) - 1)
    gl = Glyph()
    gl.numberOfContours = len(ends)
    gl.coordinates = GlyphCoordinates(coords)
    gl.endPtsOfContours = ends
    gl.flags = bytearray([1] * len(coords))
    gl.flags[0] |= 0x40                                 # OVERLAP_SIMPLE
    gl.program = Program(); gl.program.fromBytecode(b'')
    return gl

def build_master(inset, shift, path):
    order = ['.notdef'] + [gname(c) for c in G]
    glyphs = {'.notdef': draw(NOTDEF, inset, shift)}
    cmap = {}
    for ch, rows in G.items():
        glyphs[gname(ch)] = draw(rows, inset, shift)
        cmap[ord(ch)] = gname(ch)
    for ch, rows in SC.items():
        order.append(gname(ch) + '.sc')
        glyphs[gname(ch) + '.sc'] = draw(rows, inset, shift)
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({n: (ADV, XMIN) for n in order})
    fb.setupHorizontalHeader(ascent=7 * P, descent=-P)
    fam = NAME + (' Scroll' if SCROLL_AXIS else '')
    fb.setupNameTable({
        "familyName": fam, "styleName": "Regular",
        "uniqueFontIdentifier": PS + "-VF-" + NAME_VERSION.split()[-1], "fullName": fam + " Regular",
        "psName": PS + "-Regular", "version": NAME_VERSION,
        **NAME_META,
    })
    fb.setupOS2(sTypoAscender=7 * P, sTypoDescender=-P, sTypoLineGap=0,
                usWinAscent=7 * P + 16, usWinDescent=P + 16, sxHeight=5 * P, sCapHeight=7 * P,
                xAvgCharWidth=ADV, achVendID="NONE", fsType=0)
    pn = Panose(); pn.bFamilyType = 2; pn.bProportion = 9
    fb.font["OS/2"].panose = pn
    if SC:
        caps = sorted(SC)
        fb.addOpenTypeFeatures(
            "languagesystem DFLT dflt; languagesystem latn dflt;\n"
            "feature smcp { sub [%s] by [%s]; } smcp;\n" % (' '.join(gname(c.lower()) for c in caps), ' '.join(gname(c) + '.sc' for c in caps)) +
            "feature c2sc { sub [%s] by [%s]; } c2sc;\n" % (' '.join(gname(c) for c in caps), ' '.join(gname(c) + '.sc' for c in caps)))
    fb.setupPost(isFixedPitch=1, underlinePosition=-H, underlineThickness=P)
    fb.save(path)

# The masters form a full grid (opsz × SCRL). fontTools' default region search can give a scroll
# master a support that reaches past its neighbours (e.g. -1…-0.75…-0.625). Neighbouring masters
# then sit at fractional scalars, deltas get rounded to integers, and an "off" dot comes back as a
# sub-unit speck. Tensor-product tents (each region ends exactly at the next master on every axis)
# keep every scalar at a master 0 or 1, so integer deltas reproduce every master exactly.
from fontTools.varLib import models as _models
def _grid_supports(self):
    grid = {}
    for loc in self.locations:
        for ax, v in loc.items():
            grid.setdefault(ax, {0.0}).add(v)
    grid = {ax: sorted(vs) for ax, vs in grid.items()}
    self.supports = []
    for loc in self.locations:
        sup = {}
        for ax, p in loc.items():
            vs = grid[ax]; i = vs.index(p)
            lo = vs[i - 1] if i > 0 else p
            hi = vs[i + 1] if i < len(vs) - 1 else p
            sup[ax] = (lo, p, hi) if p > 0 else (lo, p, hi)
            if p > 0: sup[ax] = (max(lo, 0.0), p, hi)
            if p < 0: sup[ax] = (lo, p, min(hi, 0.0))
        self.supports.append(sup)
    self._computeDeltaWeights()
_models.VariationModel._computeMasterSupports = _grid_supports

tmp = tempfile.mkdtemp()
ds = DesignSpaceDocument()
a1 = AxisDescriptor()
a1.tag, a1.name, a1.minimum, a1.default, a1.maximum = 'opsz', 'Optical size', 8, 8, 144
a1.map = OPSZ_MAP
ds.addAxis(a1)
if SCROLL_AXIS:
    a2 = AxisDescriptor()
    a2.tag, a2.name, a2.minimum, a2.default, a2.maximum = 'SCRL', 'Scroll', -8, 0, 8
    a2.map = stepped_map()
    ds.addAxis(a2)
for opsz, inset in [(8, INSET_MIN), (144, INSET_MAX)]:
    for s in (SCROLL if SCROLL_AXIS else [0]):
        p = os.path.join(tmp, f'm{opsz}_{s}.ttf')
        build_master(inset, s, p)
        src = SourceDescriptor(); src.path = p
        src.location = {'Optical size': opsz, **({'Scroll': s} if SCROLL_AXIS else {})}
        if opsz == 8 and s == 0:
            src.copyInfo = True
        ds.addSource(src)

# Named instances, so desktop apps list styles in their font menus.
for opsz, label in [(8, 'Text'), (32, 'Small Display'), (72, 'Display'), (144, 'Poster')]:
    inst = InstanceDescriptor()
    inst.familyName = NAME + (' Scroll' if SCROLL_AXIS else '')
    inst.styleName = label
    inst.postScriptFontName = PS + '-' + label.replace(' ', '')
    inst.userLocation = {'Optical size': opsz, **({'Scroll': 0} if SCROLL_AXIS else {})}
    ds.addInstance(inst)

vf, _, _ = varLib.build(ds, optimize=True)   # IUP-optimised; verify.py confirms no specks
axes = [dict(tag='opsz', name='Optical size', values=[
    dict(value=8, name='Text', flags=0x2), dict(value=32, name='Small Display'),
    dict(value=72, name='Display'), dict(value=144, name='Poster')])]
if SCROLL_AXIS:
    axes.append(dict(tag='SCRL', name='Scroll', values=[dict(value=0, name='Rest', flags=0x2)]))
# The stepped avar's flat run around 0 makes fontTools invert SCRL=0 to -0.45; pin it back.
for inst in vf['fvar'].instances:
    if 'SCRL' in inst.coordinates:
        inst.coordinates['SCRL'] = 0.0
buildStatTable(vf, axes)
vf['head'].fontRevision = FONT_REVISION
vf.save(OUT + '.ttf')
vf.flavor = 'woff2'; vf.save(OUT + '.woff2')
print(OUT, len(G), 'glyphs', os.path.getsize(OUT + '.woff2'), 'bytes woff2')
