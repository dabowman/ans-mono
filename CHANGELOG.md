# Changelog

All notable changes to Ans Mono. Versions follow [Semantic Versioning](https://semver.org); the font files carry the same version in their name table (`Version 1.400` = 1.4.0).

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
