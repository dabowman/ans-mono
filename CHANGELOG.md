# Changelog

All notable changes to Ans Mono. Versions follow [Semantic Versioning](https://semver.org); the font files carry the same version in their name table (`Version 1.400` = 1.4.0, `Version 1.501` = 1.5.1).

## [1.6.0] - 2026-10-15

### Added
- **Dot shape** axis (`ELSH`, 0–100): square (0), round (50), diamond (100), and blends in between.
- **Dot size** axis (`ELXP`, −100 to 100): from fine pinpoints at half the dot pitch (−100), through the optical-size gap (0), to dots grown to fill the cell (100).
- **Ans Mono LCD** (`AnsMono-LCD-VF`, `css/ans-mono-lcd.css`): the core font with COLR colour layers, like Bitcount Ink. Every character draws its unlit cell under its lit dots, so one run of text is a whole LCD readout. Two palettes, light (black at 12%) and dark (white at 14%), selected with CSS `font-palette`. Where colour fonts aren't supported, it draws the lit dots only.
- Named styles Round and Diamond for each optical size in the variable fonts (Text Round, Display Diamond, …).
- CSS helpers `.ans-mono-round`, `.ans-mono-diamond`, `.ans-mono-lcd`, `.ans-mono-lcd-dark`.

### Changed
- The core variable font is built from components, like Bitcount: one `_dot` glyph carries every master, and every character is a composite of `_dot` at its lit cells. At the default shape and size, outlines are unchanged at every optical size, and unhinted rendering is pixel-identical to 1.5.2. Hinted FreeType rendering can differ by sub-pixel edge rounding. With all three axes, the core web font is smaller than 1.5.2's single-axis font: 6.2 → 5.0 KB.
- The `.ans-mono-readout` unlit copy inherits the element's `font-variation-settings`, so it matches the lit dots' shape and size.
- The build checks the core and LCD fonts' structure and colour layers (`source/verify_core.py`).

## [1.5.2] - 2026-10-14

### Fixed
- The named optical sizes (Small Display, Display) now match the optical-size slider in Figma. The gap curve lived in the `avar` map, which Figma applies to the slider but not to named styles, so Display (72) drew about half the gap the slider drew at 71 or 73, and Small Display (32) drew almost none. The curve now lives in masters at 8, 16, 32, 72 and 144, and the core font has no `avar`. Outlines are unchanged at every optical size in apps that applied `avar` already.

### Changed
- The variable fonts are larger for the extra masters: core web font 5.6 → 6.2 KB, numerals scroll subset 14.5 → 23.7 KB, full scroll font 57 → 97 KB.

## [1.5.1] - 2026-10-14

### Fixed
- Stylesheets now request fonts with a version query (`AnsMono-VF.woff2?v=1.5.1`). File names stay the same between releases, so browsers and CDNs could keep serving a cached older font (for example the 5×7 █ from 1.4 instead of the full 6×8 cell).

## [1.5.0] - 2026-10-14

### Added
- **Unlit cells** (OpenType `ss01`, CSS `font-feature-settings: "ss01"`): every character, spaces included, becomes a block of unlit dots exactly as wide as itself, for LCD-style readouts with a lit layer over an unlit one.
- CSS helpers `.ans-mono-unlit` and `.ans-mono-readout` (one-element readout drawn from `data-text`; works with `.ans-mono-roll`, where the unlit grid stays still while digits roll).
- Spaces at whole-dot widths: hair U+200A (1), six-per-em U+2006 (1), thin U+2009 (2), narrow no-break U+202F (2), four-per-em U+2005 (2), medium math U+205F (2), three-per-em U+2004 (3), en U+2002 (4), figure U+2007 (6), punctuation U+2008 (6), no-break U+00A0 (6), em U+2003 (8).
- Cell graphics on the full 6×8 cell: lower fills ▁–▇, upper fills (▔ ▀ and U+1FB82–1FB86), single dot rows (U+1FB76–1FB7B), single dot columns (▏ ▕ and U+1FB70–1FB75), left and right fills (▎–▉, ▐, U+1FB87–1FB8B), quadrants ▖–▟, shades ░ ▒ ▓ as dot patterns.
- Numerals scroll subset includes the new spaces.

### Changed
- █ (U+2588) now fills the whole 6×8 cell instead of the 5×7 glyph area, so runs of blocks tile into one continuous dot field.

## [1.4.0] - 2026-10-13

First release in this repository.

### Added
- Small caps for A–Z (OpenType `smcp`, `c2sc`; CSS `font-variant-caps`).
- Middle dot `·`.
- Desktop fonts: static CFF `.otf` in four optical sizes (Text, Small Display, Display, Poster); named instances in the variable fonts.
- Embedded-CSS builds (`*.embedded.css`) so pages need no font request.
- SIL Open Font License 1.1; licence and copyright in every font's name table.
- Reproducible build (`build.sh`) with an automated scroll-axis check (`verify.py`).

## [1.3.0] - 2026-10-08

### Added
- En dash `–`, minus `−`, `€ £ ¥ ¢`.
- Numerals-only scroll subset (14 KB).

### Changed
- Scroll axis moved into its own opt-in file; core web font is ~4 KB.
- Hyphen narrowed to 3 dots so it differs from the en dash and minus.

### Fixed
- Glyphs with an empty first column (I, l, 1, i) were drawn one dot to the left in the variable font, so "VISITORS" read as "VI SI TORS".
- Faint specks at some scroll steps (dots rounding to sub-unit squares instead of zero).

## [1.2.0] - 2026-10-08

### Added
- Scroll axis `SCRL` (−8…8, whole dot rows).

## [1.1.0] - 2026-10-08

### Added
- Optical size axis `opsz` (8–144): dot grid opens at display sizes.

## [1.0.0] - 2026-10-08

### Added
- 120 glyphs: ASCII, calculator symbols (→ ≠ ≤ ≥ π θ √ Σ ∫ …).
