"""Glyph widths, the unlit-cell glyphs and the OpenType feature code shared by every builder.

ss01 "Unlit cells": every character, spaces included, becomes a solid block of dots exactly as
wide as its own advance. Set the same text twice, the back copy with ss01 in a lighter colour,
and you get a readout whose unlit pixels line up dot for dot with the lit ones, thin spaces too.
"""

CELL = 6                                   # default advance, in dots
ROWS = 8


def gname(ch):
    return 'space' if ch == ' ' else ('uni%04X' % ord(ch) if ord(ch) <= 0xFFFF else 'u%05X' % ord(ch))


def width(ch, W):
    return W.get(ch, CELL)


def fill_name(w):
    return f'fill.w{w}'


def fill_rows(w):
    return tuple('#' * w for _ in range(ROWS))


def extra_glyphs(G, W):
    """Unencoded glyphs every build adds: one unlit fill per advance width in use."""
    widths = sorted({width(ch, W) for ch in G} | {CELL})
    return {fill_name(w): (fill_rows(w), w) for w in widths}


def fea(G, SC, W):
    parts = ['languagesystem DFLT dflt;', 'languagesystem latn dflt;']
    if SC:
        caps = sorted(SC)
        lower = ' '.join(gname(c.lower()) for c in caps)
        upper = ' '.join(gname(c) for c in caps)
        sc = ' '.join(gname(c) + '.sc' for c in caps)
        parts.append(f'feature smcp {{ sub [{lower}] by [{sc}]; }} smcp;')
        parts.append(f'feature c2sc {{ sub [{upper}] by [{sc}]; }} c2sc;')
    groups = {}
    for ch in G:
        groups.setdefault(width(ch, W), []).append(gname(ch))
    groups.setdefault(CELL, []).extend(gname(c) + '.sc' for c in sorted(SC))
    subs = '\n'.join(f'  sub [{" ".join(names)}] by {fill_name(w)};' for w, names in sorted(groups.items()))
    parts.append('feature ss01 {\n  featureNames { name "Unlit cells"; };\n' + subs + '\n} ss01;')
    return '\n'.join(parts) + '\n'
