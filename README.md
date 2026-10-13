# Ans Mono

A pixel monospace in the style of graphing-calculator LCD type: five cells by seven in an em of eight. Version 1.300.

- **Ans Mono** (`fonts/AnsMono-VF.woff2`, 153 glyphs): one axis, `opsz` from 8 to 144. At 8 a pixel fills its cell; above about 16px the gaps between the dots open. Small caps through `font-variant-caps`.
- **Ans Mono Scroll** (`fonts/AnsMonoScroll-VF.woff2`, 35 glyphs): the numerals and their signs (`0–9 . , : % + − – - ( ) / # × $ € £ ¥ ¢ k K M B b` and space), with `opsz` and a second axis, `SCRL` from -8 to 8, that rolls a glyph a dot row at a time.

## Use

`css/ans-mono.css` and `css/ans-mono-scroll.css` each embed their font as a data URI, so a page that loads one makes no font request. They are the same bytes as the files in `fonts/`.

```css
@import 'css/ans-mono.css';
@import 'css/ans-mono-scroll.css'; /* only where numbers animate */

.figure { font-family: "Ans Mono", ui-monospace, monospace; font-variant-numeric: tabular-nums; }
```

Set `font-optical-sizing: none` to keep the pixels solid at every size. The classes and the `ans-mono-rise` and `ans-mono-drop` keyframes are described in the stylesheets' comments.

## License

Copyright 2026 David Bowman. Licensed under the [SIL Open Font License, Version 1.1](OFL.txt).
