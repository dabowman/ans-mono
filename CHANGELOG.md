# Changelog

All notable changes to Ans Mono. Versions follow [Semantic Versioning](https://semver.org); the font files carry the same version in their name table (`Version 1.400` = 1.4.0).

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
