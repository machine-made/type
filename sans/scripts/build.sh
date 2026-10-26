#!/usr/bin/env bash
# Build machine-made Sans: variable, static TTF and OTF, and WOFF2.
# Usage: sans/scripts/build.sh
# Needs the packages in sans/requirements.txt (gftools gives
# "gftools builder", fontmake and ttfautohint).
# Output: fonts/sans/{variable,ttf,otf,webfonts}. Temporary files go to build/sans.
set -euo pipefail
cd "$(dirname "$0")/../.."

# Fixed timestamps (head.created and head.modified) for repeatable builds.
# A fixed date, not a commit date: a rebase or a squash merge changes
# commit dates, and then the build would not match the committed fonts.
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1792972800}"  # 2026-10-26 00:00 UTC

rm -rf build/sans
mkdir -p build/sans
# gftools builder writes build.ninja and temporary UFOs next to the sources.
(cd sans/sources && gftools builder config.yaml)
python sans/scripts/finish.py build/sans fonts/sans
rm -rf sans/sources/build.ninja sans/sources/.ninja_log sans/sources/instance_ufos sans/sources/master_ufo
