"""Write the CSS entry points into css/ (run from the repo root after the fonts are built).

css/ans-mono.css                   @font-face by URL (../fonts/web/), for apps that bundle assets
css/ans-mono.embedded.css          same font embedded as a data: URI, so the page needs no font request
css/ans-mono-lcd.css               the LCD colour font (lit dots over unlit cells), by URL (opt-in)
css/ans-mono-lcd.embedded.css      the same, embedded
css/ans-mono-scroll.css            numerals subset with the SCRL axis, by URL (opt-in)
css/ans-mono-scroll.embedded.css   the same, embedded
"""
import base64, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from version import VERSION

FALLBACK = 'ui-monospace, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'
WEB = 'fonts/web'

def size(name):
    return os.path.getsize(f'{WEB}/{name}')

def src(name, embed):
    if embed:
        data = base64.b64encode(open(f'{WEB}/{name}', 'rb').read()).decode()
        return f'url(data:font/woff2;base64,{data}) format("woff2")'
    # ?v= busts browser/CDN caches: file names stay the same between releases
    return f'url("../fonts/web/{name}?v={VERSION}") format("woff2")'

def core(embed):
    return f'''/* Ans Mono: core web font. {size("AnsMono-VF.woff2")} bytes woff2{", embedded" if embed else ""}.
   Axes: opsz (optical size), ELSH (dot shape: 0 square, 50 round, 100 diamond), ELXP (dot size: -100 fine, 0 normal, 100 solid).
   Dot gaps open automatically from ~32px (font-optical-sizing: auto); font-optical-sizing: none keeps it solid.
   Dot shape and size: font-variation-settings: "ELSH" 50, "ELXP" -40 (or .ans-mono-round / .ans-mono-diamond).
   Small caps: font-variant-caps: small-caps | all-small-caps.
   Unlit cells: font-feature-settings: "ss01" (or .ans-mono-unlit / .ans-mono-readout below). */
@font-face {{
  font-family: "Ans Mono";
  src: {src("AnsMono-VF.woff2", embed)};
  font-weight: 400;
  font-style: normal;
  font-display: {"block" if embed else "swap"};
}}

/* A monospace fallback and tabular figures keep number columns aligned even before the font loads. */
.ans-mono {{
  font-family: "Ans Mono", {FALLBACK};
  font-variant-numeric: tabular-nums;
}}

.ans-mono-sc {{
  font-variant-caps: all-small-caps;
}}

/* Dot shape (ELSH). Any value from 0 to 100 works; these are the named ones. */
.ans-mono-round {{
  font-variation-settings: "ELSH" 50;
}}
.ans-mono-diamond {{
  font-variation-settings: "ELSH" 100;
}}

/* Unlit cells (OpenType ss01): every character, spaces included, becomes a block of dots
   exactly as wide as itself. Put a copy of the text behind the real text in a lighter colour. */
.ans-mono-unlit {{
  font-feature-settings: "ss01";
}}

/* LCD readout in one element. The unlit layer is drawn from data-text, so keep it equal to the text:
     <span class="ans-mono ans-mono-readout" data-text="12 480">12 480</span>
   Set the unlit colour with --ans-mono-unlit. */
.ans-mono-readout {{
  position: relative;
  isolation: isolate;
  white-space: pre;
}}
.ans-mono-readout::before {{
  content: attr(data-text);
  content: attr(data-text) / "";          /* hide the copy from screen readers where supported */
  position: absolute;
  inset: 0;
  z-index: -1;
  font-family: "Ans Mono", {FALLBACK};    /* the core font carries ss01, even under .ans-mono-roll */
  font-feature-settings: "ss01";
  font-variation-settings: inherit;       /* same dot shape and size as the lit text; the core font has no SCRL, so the unlit grid never scrolls */
  color: var(--ans-mono-unlit, color-mix(in srgb, currentColor 12%, transparent));
  pointer-events: none;
  user-select: none;
}}
'''

def lcd(embed):
    return f'''/* Ans Mono LCD: the core font with colour layers. {size("AnsMono-LCD-VF.woff2")} bytes woff2{", embedded" if embed else ""}.
   Every character is its lit dots (the text colour) over its unlit cell, so one run of text is a
   whole LCD readout, spaces included. Same axes as the core font: opsz, ELSH (dot shape), ELXP (dot size).
   Browsers without colour-font support draw the lit dots only.
   Unlit colour: font-palette: light (black at 12%, the default) or dark (white at 14%, .ans-mono-lcd-dark),
   or your own:
     @font-palette-values --my-lcd {{ font-family: "Ans Mono LCD"; override-colors: 0 #B1BB9F; }}
     .my-readout {{ font-palette: --my-lcd; }}
   Spaces carry unlit cells too: use white-space: pre (or pre-wrap) so runs of spaces aren't collapsed. */
@font-face {{
  font-family: "Ans Mono LCD";
  src: {src("AnsMono-LCD-VF.woff2", embed)};
  font-weight: 400;
  font-style: normal;
  font-display: {"block" if embed else "swap"};
}}

.ans-mono-lcd {{
  font-family: "Ans Mono LCD", {FALLBACK};
  font-variant-numeric: tabular-nums;
  font-palette: light;
}}

.ans-mono-lcd-dark {{
  font-palette: dark;
}}
'''

def scroll(embed):
    return f'''/* Ans Mono Scroll: numerals subset with the SCRL axis (row-by-row roll). {size("AnsMono-Numerals-Scroll-VF.woff2")} bytes woff2{", embedded" if embed else ""}.
   Opt-in: load only where numbers animate. Covers 0-9 . , : % + − – - ( ) / # × $ € £ ¥ ¢ k K M B b and space;
   anything else falls through to "Ans Mono", so load ans-mono{".embedded" if embed else ""}.css as well.
   The full scroll font with every glyph is fonts/web/AnsMono-Scroll-VF.woff2.
   Rolling readout: class="ans-mono-roll ans-mono-readout" data-text="…" keeps the unlit grid still
   while the digits roll (the unlit layer is set in the core font). */
@font-face {{
  font-family: "Ans Mono Scroll";
  src: {src("AnsMono-Numerals-Scroll-VF.woff2", embed)};
  font-weight: 400;
  font-style: normal;
  font-display: {"block" if embed else "swap"};
}}

.ans-mono-roll {{
  font-family: "Ans Mono Scroll", "Ans Mono", {FALLBACK};
  font-variant-numeric: tabular-nums;
}}

/* SCRL: -8..0 rises in from below, 8..0 drops in from above. Values snap to whole dot rows,
   so a linear animation steps one row at a time (8 steps).
   Per character:  animation: ans-mono-rise .8s linear both; animation-delay: calc(var(--i) * 60ms); */
@keyframes ans-mono-rise {{ from {{ font-variation-settings: "SCRL" -8; }} to {{ font-variation-settings: "SCRL" 0; }} }}
@keyframes ans-mono-drop {{ from {{ font-variation-settings: "SCRL" 8; }}  to {{ font-variation-settings: "SCRL" 0; }} }}

@media (prefers-reduced-motion: reduce) {{
  .ans-mono-roll {{ animation: none !important; font-variation-settings: "SCRL" 0; }}
}}
'''

os.makedirs('css', exist_ok=True)
for name, text in [('ans-mono.css', core(False)), ('ans-mono.embedded.css', core(True)),
                   ('ans-mono-lcd.css', lcd(False)), ('ans-mono-lcd.embedded.css', lcd(True)),
                   ('ans-mono-scroll.css', scroll(False)), ('ans-mono-scroll.embedded.css', scroll(True))]:
    open(f'css/{name}', 'w').write(text)
    print(f'css/{name}', os.path.getsize(f'css/{name}'), 'bytes')
