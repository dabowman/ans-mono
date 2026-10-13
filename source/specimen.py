"""Render docs/specimen.png from the built fonts (run from the repo root after build.sh)."""
import os
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont

LCD, INK, DIM = '#C3CDB2', '#1B2216', '#5E6A52'
tmp = 'build-specimen'; os.makedirs(tmp, exist_ok=True)

def inst(opsz, scrl=None):
    path = 'fonts/variable/AnsMono-Scroll-VF.ttf' if scrl is not None else 'fonts/variable/AnsMono-VF.ttf'
    loc = {'opsz': opsz, **({'SCRL': scrl} if scrl is not None else {})}
    out = f'{tmp}/i_{opsz}_{scrl}.ttf'
    instantiateVariableFont(TTFont(path), loc).save(out)
    return out

W, H = 1600, 740
im = Image.new('RGB', (W, H), LCD); d = ImageDraw.Draw(im)
f = lambda opsz, size, scrl=None: ImageFont.truetype(inst(opsz, scrl), size)
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

d.text((64, 676), 'OFL-1.1 · Copyright 2026 David Bowman', font=label, fill=DIM)
os.makedirs('docs', exist_ok=True)
im.save('docs/specimen.png', optimize=True)
for p in os.listdir(tmp): os.remove(f'{tmp}/{p}')
os.rmdir(tmp)
print('docs/specimen.png')
