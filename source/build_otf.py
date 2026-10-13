"""Static desktop OpenType (.otf, CFF outlines) from a core variable font.

usage: python3 build_otf.py <core-VF.ttf> "<Family>" <PSFamily> <out-dir>

One .otf per named optical size: Text (solid), Small Display, Display, Poster (dot grid open).
Each style is its own legacy family ("Ans Mono Display") so it shows up in every app, and carries
the typographic family/subfamily names (IDs 16/17) so apps that support it group them under one
family ("Ans Mono" → Text / Small Display / Display / Poster). OpenType features (small caps)
are carried over.
"""
import sys, os
from fontTools.ttLib import TTFont, newTable
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.ttLib.removeOverlaps import removeOverlaps
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.boundsPen import BoundsPen
from version import NAME_VERSION, FONT_REVISION, NAME_META

SRC, FAMILY, PSFAM, OUTDIR = sys.argv[1:5]
os.makedirs(OUTDIR, exist_ok=True)
STYLES = [(8, 'Text'), (32, 'Small Display'), (72, 'Display'), (144, 'Poster')]

def contours(rec):
    """Split a RecordingPen into contours, dropping degenerate ones (the 1-point side-bearing anchor)."""
    out, cur = [], []
    for op, args in rec.value:
        cur.append((op, args))
        if op in ('closePath', 'endPath'):
            if sum(1 for o, _ in cur if o in ('lineTo', 'curveTo', 'qCurveTo')) >= 2:
                out.append(cur)
            cur = []
    return out

for opsz, style in STYLES:
    vf = TTFont(SRC)
    inst = instantiateVariableFont(vf, {'opsz': opsz})
    removeOverlaps(inst)                      # Text's overlapping dots merge into clean outlines
    gs = inst.getGlyphSet()
    order = inst.getGlyphOrder()
    upm = inst['head'].unitsPerEm
    charstrings, metrics = {}, {}
    for g in order:
        rec = RecordingPen(); gs[g].draw(rec)
        adv = inst['hmtx'][g][0]
        t2 = T2CharStringPen(adv, gs)
        rev = ReverseContourPen(t2)              # TrueType is clockwise; CFF wants counter-clockwise
        bp = BoundsPen(gs)
        for c in contours(rec):
            for op, args in c:
                getattr(rev, op)(*args); getattr(bp, op)(*args)
        charstrings[g] = t2.getCharString()
        metrics[g] = (adv, bp.bounds[0] if bp.bounds else 0)

    legacy = f'{FAMILY} {style}'
    ps = f'{PSFAM}-{style.replace(" ", "")}'
    fb = FontBuilder(upm, isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(inst.getBestCmap())
    fb.setupCFF(ps, {'FullName': legacy, 'FamilyName': legacy, 'Weight': 'Regular'}, charstrings, {})
    fb.setupHorizontalMetrics(metrics)
    h = inst['hhea']
    fb.setupHorizontalHeader(ascent=h.ascent, descent=h.descent)
    fb.setupNameTable({
        'familyName': legacy, 'styleName': 'Regular',
        'typographicFamily': FAMILY, 'typographicSubfamily': style,
        'uniqueFontIdentifier': f'{ps}-' + NAME_VERSION.split()[-1], 'fullName': legacy, 'psName': ps,
        'version': NAME_VERSION,
        **NAME_META,
    })
    o = inst['OS/2']
    fb.setupOS2(sTypoAscender=o.sTypoAscender, sTypoDescender=o.sTypoDescender, sTypoLineGap=0,
                usWinAscent=o.usWinAscent, usWinDescent=o.usWinDescent, sxHeight=o.sxHeight,
                sCapHeight=o.sCapHeight, xAvgCharWidth=o.xAvgCharWidth, achVendID='NONE',
                fsType=0, usWeightClass=400, fsSelection=0x40)
    fb.font['OS/2'].panose = o.panose
    fb.setupPost(isFixedPitch=1, underlinePosition=inst['post'].underlinePosition,
                 underlineThickness=inst['post'].underlineThickness)
    if 'GSUB' in inst:
        fb.font['GSUB'] = inst['GSUB']
    path = os.path.join(OUTDIR, f'{ps}.otf')
    fb.font['head'].fontRevision = FONT_REVISION
    fb.save(path)
    print(path, os.path.getsize(path))
