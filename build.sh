#!/usr/bin/env bash
# Rebuild every font and CSS file from source/glyphs.py.
#   pip install -r requirements.txt && ./build.sh
set -euo pipefail
cd "$(dirname "$0")"

# Fixed timestamp so rebuilding unchanged sources gives byte-identical files.
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1791849600}"   # 2026-10-13T00:00:00Z

B=build
rm -rf "$B" fonts css
mkdir -p "$B" fonts/web fonts/variable fonts/otf

echo "→ static"
python3 source/build.py "$B/AnsMono-Regular" glyphs "Ans Mono"
echo "→ variable: opsz"
python3 source/build_vf.py "$B/AnsMono-VF" glyphs "Ans Mono"
echo "→ variable: opsz + SCRL"
python3 source/build_vf.py "$B/AnsMono-Scroll-VF" glyphs "Ans Mono" --scroll
echo "→ verifying scroll axis (every dot, 9 sizes × 13 scroll values)"
python3 source/verify.py "$B/AnsMono-Scroll-VF.ttf" glyphs
echo "→ numerals subset"
pyftsubset "$B/AnsMono-Scroll-VF.ttf" \
  --text=" 0123456789.,:%+-−–()/\$€£¥¢#×kKMBb" \
  --layout-features='' --no-hinting --name-IDs='*' --name-languages='*' --flavor=woff2 \
  --output-file="$B/AnsMono-Numerals-Scroll-VF.woff2"
echo "→ desktop OTF"
python3 source/build_otf.py "$B/AnsMono-VF.ttf" "Ans Mono" AnsMono fonts/otf

cp "$B/AnsMono-VF.woff2" "$B/AnsMono-Scroll-VF.woff2" "$B/AnsMono-Numerals-Scroll-VF.woff2" \
   "$B/AnsMono-Regular.woff2" fonts/web/
cp "$B/AnsMono-VF.ttf" "$B/AnsMono-Scroll-VF.ttf" fonts/variable/

echo "→ css"
python3 source/make_css.py
rm -rf "$B"
echo "done"
