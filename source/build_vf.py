"""Variable builds.

usage: python3 build_vf.py <out-stem> <glyph-module> "<Family Name>" [--scroll | --lcd]

Core file (default): opsz + ELSH + ELXP.
LCD file (--lcd): the core file plus colour layers (COLR/CPAL), family "<Family Name> LCD".
Scroll file (--scroll): opsz + SCRL. Ship it only where something actually animates.

opsz  Optical size 8–144. Every dot is its own square, inset from its cell by an amount that
      depends on opsz: overlapping (solid) up to 16px, opening into a visible LCD grid at display
      sizes. The gap curve lives in masters (8, 16, 32, 72, 144), not in an avar map: Figma applies
      avar to its optical-size slider but not to the named styles, so Display (72) drew half the slider's gap at 72.
ELSH  Element shape 0–100: 0 square dots, 50 round, 100 diamond. Every shape is the same
      16-point contour (on, off, on, off per quarter), so they interpolate into each other.
ELXP  Element expansion -100–100: 0 is the gap opsz sets, 100 grows every dot to a solid cell,
      -100 shrinks it to half the dot pitch, at any optical size.
SCRL  Scroll -8–8, in whole dot rows. The 8-row cell is a fixed window; the bitmap slides through
      it by switching dots on and off (an off dot is a zero-area contour on its own centre), so the
      grid never moves. -8..0 rises in from below, 8..0 drops in from above. A stepped avar map
      holds every whole row flat, so a linear animation steps row by row with no half-lit dots.

Components: like Bitcount, the core file is built from one element. `_dot` is a single LCD dot,
centred on the origin, and it alone carries the opsz masters. Every character is a composite that
places `_dot` at its lit cells, so the dot's gap, shape and size change every glyph at once, and
gvar holds deltas for one glyph: three axes cost about what one did. The scroll file can't use
components: TrueType can move a component between masters but not switch it off, and SCRL works
by switching dots off. It draws each dot as its own square contour and has no element axes.

Colour layers (--lcd), like Bitcount Ink: every character is a COLR glyph of two layers, its
unlit cell (the ss01 fill of its width, in palette colour 0) under its lit dots (the text colour).
CPAL has two palettes, one for light and one for dark backgrounds (CSS font-palette: light | dark,
or @font-palette-values to set the unlit colour). Apps without colour-font support draw the lit
dots only, the same as the core font.

Geometry is all integers (UPM 1024, 128 units per dot, even half-dot), so every master's points
are exact and an off dot interpolates to exactly zero area at every opsz.
Every glyph also carries a one-point contour (in the core file, the zero-area `_anchor` component) at x = XMIN, so xMin is the same in every master and
the hmtx side bearing always matches the outline. Without it, glyphs whose first column is empty
(I, l, 1, …) were drawn a dot to the left.
"""
import sys, os, importlib, tempfile, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates, GlyphComponent
from fontTools.ttLib.tables.ttProgram import Program
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor
from fontTools import varLib
from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib.tables.O_S_2f_2 import Panose
from fontTools.colorLib.builder import buildCOLR, buildCPAL
from version import NAME_VERSION, FONT_REVISION, NAME_META

OUT, MOD, NAME = sys.argv[1], sys.argv[2], sys.argv[3]
SCROLL_AXIS = '--scroll' in sys.argv
LCD = '--lcd' in sys.argv
SUFFIX = ' Scroll' if SCROLL_AXIS else ' LCD' if LCD else ''
FAMILY = NAME + SUFFIX
_mod = importlib.import_module(MOD)
G = _mod.G
SC = getattr(_mod, 'SC', {})   # small caps (unencoded; smcp / c2sc)
W = getattr(_mod, 'W', {})     # advance widths in dots for non-cell glyphs (spaces)
from features import gname, width, extra_glyphs, fea, fill_name, CELL
PS = FAMILY.replace(' ', '')

UPM, P, H = 1024, 128, 64      # 8 dot rows per em; H = half a dot
ADV = 6 * P
ROWS = 8

# opsz masters: inset per side in font units at each optical size; linear between them.
# -3 = dots overlap (solid) up to 16px; ~8% gap at 32, ~16% at 72, 26/128 ≈ 20% at 144.
OPSZ_MASTERS = [(8, -3), (16, -3), (32, 5), (72, 10), (144, 13)]
XMIN = min(0, OPSZ_MASTERS[0][1])  # leftmost any dot ever reaches; also every glyph's lsb
SHAPES = [0, 50, 100]                # ELSH masters: square, round, diamond
EXPANSION = [-100, 0, 100]           # ELXP masters

def dot_half(inset, xp):
    """Half-side of the dot: the opsz gap at ELXP 0, a solid cell at 100, half the pitch at -100."""
    return {-100: H // 2, 0: H - inset, 100: H - XMIN}[xp]
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

NOTDEF = ['#####', '#...#', '#...#', '#...#', '#...#', '#...#', '#####', '.....']

DOT, ANCHOR = '_dot', '_anchor'     # the element, and the xMin anchor (core file)

def square(cx, cy, h):
    """Scroll file's dot: a plain square of half-side h centred on (cx, cy)."""
    return [(cx - h, cy + h), (cx + h, cy + h), (cx + h, cy - h), (cx - h, cy - h)]

# One quarter of the element, clockwise from the top of the dot to its right side, in units of the
# half-side: on-curve, off-curve, on-curve, off-curve. The other quarters are this turned by 90°.
# Square: the corner points coincide, so both curves are straight edges. Round: two quadratic arcs
# of 45° each (within 0.1% of a circle). Diamond: all four points on the diagonal.
_T, _S = math.tan(math.pi / 8), math.sqrt(0.5)
QUARTER = {
    0:   [(0, 1), (1, 1), (1, 1), (1, 1)],
    50:  [(0, 1), (_T, 1), (_S, _S), (1, _T)],
    100: [(0, 1), (0.25, 0.75), (0.5, 0.5), (0.75, 0.25)],
}
QUARTER_ON = [1, 0, 1, 0]

def element(h, shape):
    """The dot (`_dot`), centred on the origin: 16 points at every shape, so shapes interpolate."""
    pts, on = [], []
    q = QUARTER[shape]
    for turn in range(4):
        for x, y in q:
            for _ in range(turn):
                x, y = y, -x
            pts.append((round(x * h), round(y * h)))
        on += QUARTER_ON
    return pts, on

def simple(contours, on=None):
    coords, ends = [], []
    for c in contours:
        coords += c
        ends.append(len(coords) - 1)
    gl = Glyph()
    gl.numberOfContours = len(ends)
    gl.coordinates = GlyphCoordinates(coords)
    gl.endPtsOfContours = ends
    gl.flags = bytearray(on if on else [1] * len(coords))
    gl.flags[0] |= 0x40                                 # OVERLAP_SIMPLE
    gl.program = Program(); gl.program.fromBytecode(b'')
    return gl

def grid(rows):
    w = max(len(r) for r in rows)
    return [r.ljust(w, '.') for r in rows] + ['.' * w] * (ROWS - len(rows)), w

def centre(c, r):
    return c * P + H, (6 - r) * P + H

def draw(rows, inset, shift):
    """Scroll file: every dot its own contour. shift = SCRL value: display row r shows source row r + shift."""
    rows, w = grid(rows)
    cols = [c for c in range(w) if any(row[c] == '#' for row in rows)]
    contours = [[(XMIN, 0)]]                            # left anchor: xMin is XMIN in every master
    for c in cols:
        for r in range(ROWS):
            src = r + shift
            on = 0 <= src < ROWS and rows[src][c] == '#'
            contours.append(square(*centre(c, r), (H - inset) if on else 0))
    return simple(contours)

def component(name, x, y):
    gc = GlyphComponent()
    gc.glyphName, gc.x, gc.y, gc.flags = name, x, y, 0     # no ROUND_XY_TO_GRID: dots land where contours did
    return gc

def compose(rows):
    """Core file: the anchor plus one `_dot` per lit cell. Same in every master; only `_dot` varies."""
    rows, w = grid(rows)
    comps = [component(ANCHOR, XMIN, 0)]
    comps += [component(DOT, *centre(c, r)) for r in range(ROWS) for c in range(w) if rows[r][c] == '#']
    comps[0].flags |= 0x400                             # OVERLAP_COMPOUND: solid sizes overlap dots
    gl = Glyph()
    gl.numberOfContours = -1
    gl.components = comps
    return gl

def make(rows, inset, shift):
    return draw(rows, inset, shift) if SCROLL_AXIS else compose(rows)

def build_master(inset, shift, path, h=None, shape=0):
    order = ['.notdef'] + [gname(c) for c in G]
    glyphs = {'.notdef': make(NOTDEF, inset, shift)}
    cmap = {}
    for ch, rows in G.items():
        glyphs[gname(ch)] = make(rows, inset, shift)
        cmap[ord(ch)] = gname(ch)
    adv = {'.notdef': CELL}
    adv.update({gname(ch): width(ch, W) for ch in G})
    for ch, rows in SC.items():
        order.append(gname(ch) + '.sc')
        glyphs[gname(ch) + '.sc'] = make(rows, inset, shift)
        adv[gname(ch) + '.sc'] = CELL
    for name, (rows, w) in extra_glyphs(G, W).items():     # ss01 unlit cells
        order.append(name)
        glyphs[name] = make(rows, inset, shift)
        adv[name] = w
    if not SCROLL_AXIS:
        order += [DOT, ANCHOR]
        pts, on = element(h, shape)
        glyphs[DOT] = simple([pts], on)
        # A zero-area stroke: a one-point glyph counts as empty in composite bounds, so xMin would
        # fall on the first lit dot instead of XMIN. Horizontal, so no inked glyph's bounds change.
        glyphs[ANCHOR] = simple([[(0, 0), (1, 0)]])
        adv[DOT] = adv[ANCHOR] = 0
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    lsb = {} if SCROLL_AXIS else {DOT: -h, ANCHOR: 0}
    fb.setupHorizontalMetrics({n: (adv[n] * P, lsb.get(n, XMIN)) for n in order})
    fb.setupHorizontalHeader(ascent=7 * P, descent=-P)
    fam = FAMILY
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
    fb.addOpenTypeFeatures(fea(G, SC, W))
    fb.setupPost(isFixedPitch=1, underlinePosition=-H, underlineThickness=P)
    fb.save(path)

# The masters form a full grid (opsz × SCRL, or opsz × ELSH × ELXP). fontTools' default region search can give a scroll
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
            sup[ax] = (lo, p, hi)
            if p > 0: sup[ax] = (max(lo, 0.0), p, hi)
            if p < 0: sup[ax] = (lo, p, min(hi, 0.0))
        self.supports.append(sup)
    self._computeDeltaWeights()
_models.VariationModel._computeMasterSupports = _grid_supports

tmp = tempfile.mkdtemp()
ds = DesignSpaceDocument()
a1 = AxisDescriptor()
a1.tag, a1.name, a1.minimum, a1.default, a1.maximum = 'opsz', 'Optical size', 8, 8, 144
ds.addAxis(a1)
def axis(tag, name, lo, default, hi):
    a = AxisDescriptor()
    a.tag, a.name, a.minimum, a.default, a.maximum = tag, name, lo, default, hi
    ds.addAxis(a)
    return a

if SCROLL_AXIS:
    axis('SCRL', 'Scroll', -8, 0, 8).map = stepped_map()
    for opsz, inset in OPSZ_MASTERS:
        for s in SCROLL:
            p = os.path.join(tmp, f'm{opsz}_{s}.ttf')
            build_master(inset, s, p)
            src = SourceDescriptor(); src.path = p
            src.location = {'Optical size': opsz, 'Scroll': s}
            src.copyInfo = opsz == 8 and s == 0
            ds.addSource(src)
else:
    axis('ELSH', 'Element shape', 0, 0, 100)
    axis('ELXP', 'Element expansion', -100, 0, 100)
    for opsz, inset in OPSZ_MASTERS:
        for shape in SHAPES:
            for xp in EXPANSION:
                p = os.path.join(tmp, f'm{opsz}_{shape}_{xp}.ttf')
                build_master(inset, 0, p, dot_half(inset, xp), shape)
                src = SourceDescriptor(); src.path = p
                src.location = {'Optical size': opsz, 'Element shape': shape, 'Element expansion': xp}
                src.copyInfo = opsz == 8 and shape == 0 and xp == 0
                ds.addSource(src)

# Named instances, so desktop apps list styles in their font menus: each optical size, and in the
# core and LCD files each one again with round and diamond dots.
SHAPE_NAMES = [(0, 'Square'), (50, 'Round'), (100, 'Diamond')]
for opsz, label in [(8, 'Text'), (32, 'Small Display'), (72, 'Display'), (144, 'Poster')]:
    for shape, sname in ([(0, 'Square')] if SCROLL_AXIS else SHAPE_NAMES):
        style = label + ('' if shape == 0 else ' ' + sname)
        inst = InstanceDescriptor()
        inst.familyName = FAMILY
        inst.styleName = style
        inst.postScriptFontName = PS + '-' + style.replace(' ', '')
        inst.userLocation = {'Optical size': opsz, **({'Scroll': 0} if SCROLL_AXIS else
                                                      {'Element shape': shape, 'Element expansion': 0})}
        ds.addInstance(inst)

vf, _, _ = varLib.build(ds, optimize=True)   # IUP-optimised; verify.py confirms no specks
axes = [dict(tag='opsz', name='Optical size', values=[
    dict(value=8, name='Text', flags=0x2), dict(value=32, name='Small Display'),
    dict(value=72, name='Display'), dict(value=144, name='Poster')])]
if SCROLL_AXIS:
    axes.append(dict(tag='SCRL', name='Scroll', values=[dict(value=0, name='Rest', flags=0x2)]))
else:
    axes.append(dict(tag='ELSH', name='Element shape', values=[
        dict(value=v, name=n, **({'flags': 0x2} if v == 0 else {})) for v, n in SHAPE_NAMES]))
    axes.append(dict(tag='ELXP', name='Element expansion', values=[
        dict(value=-100, name='Fine'), dict(value=0, name='Normal', flags=0x2), dict(value=100, name='Full')]))
# The stepped avar's flat run around 0 makes fontTools invert SCRL=0 to -0.45; pin it back.
for inst in vf['fvar'].instances:
    if 'SCRL' in inst.coordinates:
        inst.coordinates['SCRL'] = 0.0
buildStatTable(vf, axes)

if LCD:
    # Light backgrounds: unlit dots are black at 12%; dark backgrounds: white at 14%.
    UNLIT = [[(0, 0, 0, 0.12)], [(1, 1, 1, 0.14)]]
    FOREGROUND = 0xFFFF                                 # the text colour
    layers = {}
    for ch in G:
        layers[gname(ch)] = [(fill_name(width(ch, W)), 0), (gname(ch), FOREGROUND)]
    for ch in SC:
        layers[gname(ch) + '.sc'] = [(fill_name(CELL), 0), (gname(ch) + '.sc', FOREGROUND)]
    vf['COLR'] = buildCOLR(layers, version=0)
    vf['CPAL'] = buildCPAL(UNLIT, paletteTypes=[1, 2])  # usable with light / dark background
vf['head'].fontRevision = FONT_REVISION
vf.save(OUT + '.ttf')
vf.flavor = 'woff2'; vf.save(OUT + '.woff2')
print(OUT, len(G), 'glyphs', os.path.getsize(OUT + '.woff2'), 'bytes woff2')
