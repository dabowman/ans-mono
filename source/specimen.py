"""Render docs/specimen.png from the built fonts (run from the repo root after build.sh)."""
import os
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont

LCD, INK, DIM = '#C3CDB2', '#1B2216', '#5E6A52'
tmp = 'build-specimen'; os.makedirs(tmp, exist_ok=True)

def inst(opsz, scrl=None, shape=0, xp=0, lcd=False):
    if scrl is not None:
        path, loc = 'fonts/variable/AnsMono-Scroll-VF.ttf', {'opsz': opsz, 'SCRL': scrl}
    else:
        path = 'fonts/variable/AnsMono-LCD-VF.ttf' if lcd else 'fonts/variable/AnsMono-VF.ttf'
        loc = {'opsz': opsz, 'ELSH': shape, 'ELXP': xp}
    out = f'{tmp}/i_{opsz}_{scrl}_{shape}_{xp}_{lcd}.ttf'
    instantiateVariableFont(TTFont(path), loc).save(out)
    return out

W, H = 1600, 1180
im = Image.new('RGBA', (W, H), LCD); d = ImageDraw.Draw(im)
f = lambda opsz, size, scrl=None, **k: ImageFont.truetype(inst(opsz, scrl, **k), size)
label = ImageFont.truetype(inst(8), 16)

d.text((64, 56), 'Ans Mono', font=f(144, 128), fill=INK)
d.text((64, 200), '5×7 PIXEL MONOSPACE · AFTER THE TI-84 PLUS HOME SCREEN', font=label, fill=DIM)
d.text((64, 256), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ  0123456789', font=f(8, 32), fill=INK)
d.text((64, 304), 'abcdefghijklmnopqrstuvwxyz  →≠≤≥π√θΣ∫ €£¥', font=f(8, 32), fill=INK)
d.text((64, 352), 'Small Caps & ALL SMALL CAPS', font=f(8, 32), fill=INK, features=['smcp', 'c2sc'])

y = 440
d.text((64, y), 'OPTICAL SIZE', font=label, fill=DIM)
x = 64
for size in (16, 32, 64, 128):
    d.text((x, y + 40 + (128 - size)), 'Ans', font=f(size, size), fill=INK)
    d.text((x, y + 184), f'{size}px', font=label, fill=DIM)
    x += size * 3 // 4 * 3 + 64

d.text((900, y), 'SCROLL (SCRL −8 … 0)', font=label, fill=DIM)
for i, s in enumerate((-7, -6, -5, -4, -3, -2, -1, 0)):
    cx = 900 + i * 76
    d.rectangle([cx - 2, y + 38, cx + 50, y + 106], outline='#9DA88E')
    d.text((cx, y + 40), '7', font=f(64, 64, s), fill=INK)
    d.text((cx + 8, y + 116), str(s), font=label, fill=DIM)

y = 700
d.text((64, y), 'DOT SHAPE (ELSH)', font=label, fill=DIM)
for i, (shape, name) in enumerate([(0, 'square 0'), (50, 'round 50'), (100, 'diamond 100')]):
    d.text((64 + i * 300, y + 40), 'Ans8', font=f(72, 64, shape=shape), fill=INK)
    d.text((64 + i * 300, y + 116), name, font=label, fill=DIM)
d.text((980, y), 'DOT SIZE (ELXP)', font=label, fill=DIM)
for i, xp in enumerate((-100, 0, 100)):
    d.text((980 + i * 200, y + 40), 'Ans', font=f(72, 64, shape=50, xp=xp), fill=INK)
    d.text((980 + i * 200, y + 116), str(xp), font=label, fill=DIM)

y = 880
d.text((64, y), 'ANS MONO LCD: LIT DOTS OVER UNLIT CELLS, IN ONE RUN OF TEXT', font=label, fill=DIM)
d.text((64, y + 40), '12 480  -3.5°C', font=f(72, 96, lcd=True), fill=INK, embedded_color=True)
d.text((64, y + 160), 'RND 09:41', font=f(144, 48, shape=50, lcd=True), fill=INK, embedded_color=True)

d.text((64, 1116), 'OFL-1.1 · Copyright 2026 David Bowman', font=label, fill=DIM)
os.makedirs('docs', exist_ok=True)
im.convert('RGB').save('docs/specimen.png', optimize=True)
for p in os.listdir(tmp): os.remove(f'{tmp}/{p}')
os.rmdir(tmp)
print('docs/specimen.png')
