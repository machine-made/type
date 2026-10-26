#!/usr/bin/env bash
# Build machine-made Sans: variable, static TTF and OTF, and WOFF2.
# Usage: sans/scripts/build.sh
# Needs the packages in sans/requirements.txt (gftools gives
# "gftools builder", fontmake and ttfautohint).
# Output: fonts/sans/{variable,ttf,otf,webfonts}. Temporary files go to build/sans.
set -euo pipefail
cd "$(dirname "$0")/../.."

# Fixed timestamps (head.created and head.modified) for repeatable builds:
# the date of the last commit that changed the sources.
SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-$(git log -1 --format=%ct -- sans/sources 2>/dev/null || echo 1792972800)}"
export SOURCE_DATE_EPOCH

rm -rf build/sans
mkdir -p build/sans
# gftools builder writes build.ninja and temporary UFOs next to the sources.
(cd sans/sources && gftools builder config.yaml)
python sans/scripts/finish.py build/sans fonts/sans
rm -rf sans/sources/build.ninja sans/sources/.ninja_log sans/sources/instance_ufos sans/sources/master_ufo
