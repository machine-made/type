#!/usr/bin/env bash
# Make the release files for one family or for the site.
# Usage: .github/scripts/package_release.sh weft|sans|shuttle|site VERSION OUT_DIR
#   VERSION is the version from the tag, for example 0.1.0.
#   OUT_DIR receives the zip file and the single files to attach.
# Run from the repository root, after the build and the checks.
# For weft, OUT_DIR/readability.json must exist already (the release
# workflow writes it with weft/tools/readability.py --gate).
set -euo pipefail

fam="${1:?family: weft, sans, shuttle or site}"
version="${2:?version, for example 0.1.0}"
out="${3:?output folder}"
mkdir -p "$out"
out="$(cd "$out" && pwd)"
# Release notes per minor version: 0.1.0 and 0.1.1 use RELEASE-NOTES-0.1.md.
notes_version="${version%.*}"
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

need() {
  for f in "$@"; do
    if [ ! -s "$f" ]; then
      echo "error: $f is missing or empty." >&2
      exit 1
    fi
  done
}

# Zip with fixed file times and a sorted file list, so the zip is the
# same for the same input files.
make_zip() {
  local dir="$1" zip="$2"
  (cd "$dir" && find . -exec touch -h -d "@${SOURCE_DATE_EPOCH:-1792972800}" {} + \
    && find . -type f | LC_ALL=C sort | sed 's|^\./||' | zip -X -q -@ "$zip")
}

case "$fam" in
  weft)
    name="machine-made-weft-${version}"
    need "fonts/weft/variable/MachineMadeWeft[FRAG,wght].ttf" \
         "fonts/weft/webfonts/MachineMadeWeft[FRAG,wght].woff2" \
         "fonts/weft/webfonts/MachineMadeWeft-Regular.woff2" \
         "fonts/weft/webfonts/MachineMadeWeft-Bold.woff2" \
         weft/OFL.txt "weft/RELEASE-NOTES-${notes_version}.md" "$out/readability.json"
    mkdir -p "$stage/$name"
    cp -r fonts/weft/variable fonts/weft/ttf fonts/weft/otf fonts/weft/webfonts "$stage/$name/"
    cp weft/OFL.txt "$stage/$name/OFL.txt"
    cp "weft/RELEASE-NOTES-${notes_version}.md" "$stage/$name/RELEASE-NOTES.md"
    cp "$out/readability.json" "$stage/$name/readability.json"
    {
      echo "# machine-made Weft ${version}"
      echo
      echo "A grid-built monospace made by code. Axes: wght 100 to 900, FRAG 0 to 100."
      echo
      echo "- variable/: the variable font (TTF)"
      echo "- ttf/, otf/: nine static weights at FRAG 0"
      echo "- webfonts/: WOFF2 for the web (variable, Regular, Bold)"
      echo "- readability.json: the OCR readability report of this release"
      echo "- RELEASE-NOTES.md: what is in this release"
      echo
      echo "Licence: SIL Open Font License 1.1, Reserved Font Name \"machine-made\" (OFL.txt)."
      echo "Source: https://github.com/machine-made/type"
      echo "Specimen: https://machine-made.github.io/type/weft/"
    } > "$stage/$name/README.md"
    make_zip "$stage" "$out/$name.zip"
    cp "fonts/weft/webfonts/MachineMadeWeft[FRAG,wght].woff2" \
       fonts/weft/webfonts/MachineMadeWeft-Regular.woff2 \
       fonts/weft/webfonts/MachineMadeWeft-Bold.woff2 \
       "fonts/weft/variable/MachineMadeWeft[FRAG,wght].ttf" "$out/"
    ;;
  sans)
    name="machine-made-sans-${version}"
    need "fonts/sans/variable/MachineMadeSans[wght].ttf" \
         "fonts/sans/variable/MachineMadeSans-Italic[wght].ttf" \
         "fonts/sans/webfonts/MachineMadeSans[wght].woff2" \
         "fonts/sans/webfonts/MachineMadeSans-Italic[wght].woff2" \
         sans/OFL.txt "sans/RELEASE-NOTES-${notes_version}.md"
    mkdir -p "$stage/$name"
    cp -r fonts/sans/variable fonts/sans/ttf fonts/sans/otf fonts/sans/webfonts "$stage/$name/"
    cp sans/OFL.txt "$stage/$name/OFL.txt"
    # The release notes link to a proof image in the repository. In the zip
    # the link has no target, so point it to GitHub.
    sed 's|(\.\./proofs/|(https://github.com/machine-made/type/blob/main/proofs/|g' \
      "sans/RELEASE-NOTES-${notes_version}.md" > "$stage/$name/RELEASE-NOTES.md"
    {
      echo "# machine-made Sans ${version}"
      echo
      echo "A reading sans, upright and italic, wght 200 to 800."
      echo "machine-made Sans is based on Plus Jakarta Sans by Gumpita Rahayu, Tokotype."
      echo
      echo "- variable/: the two variable fonts (TTF)"
      echo "- ttf/, otf/: seven static weights per style"
      echo "- webfonts/: WOFF2 of the variable fonts"
      echo "- RELEASE-NOTES.md: what is in this release"
      echo
      echo "Licence: SIL Open Font License 1.1, Reserved Font Name \"machine-made\" (OFL.txt)."
      echo "Source: https://github.com/machine-made/type"
      echo "Specimen: https://machine-made.github.io/type/sans/"
    } > "$stage/$name/README.md"
    make_zip "$stage" "$out/$name.zip"
    cp "fonts/sans/webfonts/MachineMadeSans[wght].woff2" \
       "fonts/sans/webfonts/MachineMadeSans-Italic[wght].woff2" \
       "fonts/sans/variable/MachineMadeSans[wght].ttf" \
       "fonts/sans/variable/MachineMadeSans-Italic[wght].ttf" "$out/"
    ;;
  shuttle)
    name="machine-made-shuttle-${version}"
    need "fonts/shuttle/variable/MachineMadeShuttle[wdth,wght].ttf" \
         "fonts/shuttle/webfonts/MachineMadeShuttle[wdth,wght].woff2" \
         "fonts/shuttle/webfonts/MachineMadeShuttle-Regular.woff2" \
         "fonts/shuttle/webfonts/MachineMadeShuttle-Bold.woff2" \
         shuttle/OFL.txt "shuttle/RELEASE-NOTES-${notes_version}.md"
    mkdir -p "$stage/$name"
    cp -r fonts/shuttle/variable fonts/shuttle/ttf fonts/shuttle/webfonts "$stage/$name/"
    cp shuttle/OFL.txt "$stage/$name/OFL.txt"
    cp "shuttle/RELEASE-NOTES-${notes_version}.md" "$stage/$name/RELEASE-NOTES.md"
    {
      echo "# machine-made Shuttle ${version}"
      echo
      echo "A Swiss display grotesk made by code. Axes: wght 100 to 900, wdth 70 to 140."
      echo
      echo "- variable/: the variable font (TTF)"
      echo "- ttf/: nine static weights at width 100, Compressed Bold and Extended Bold"
      echo "- webfonts/: WOFF2 for the web (variable, Regular, Bold)"
      echo "- RELEASE-NOTES.md: what is in this release"
      echo
      echo "Licence: SIL Open Font License 1.1, Reserved Font Name \"machine-made\" (OFL.txt)."
      echo "Source: https://github.com/machine-made/type"
      echo "Specimen: https://machine-made.github.io/type/shuttle/"
    } > "$stage/$name/README.md"
    make_zip "$stage" "$out/$name.zip"
    cp "fonts/shuttle/webfonts/MachineMadeShuttle[wdth,wght].woff2" \
       fonts/shuttle/webfonts/MachineMadeShuttle-Regular.woff2 \
       fonts/shuttle/webfonts/MachineMadeShuttle-Bold.woff2 \
       "fonts/shuttle/variable/MachineMadeShuttle[wdth,wght].ttf" "$out/"
    ;;
  site)
    name="machine-made-type-site-${version}"
    need site/_site/index.html site/_site/data/readability.json
    mkdir -p "$stage/$name"
    cp -r site/_site/. "$stage/$name/"
    make_zip "$stage" "$out/$name.zip"
    ;;
  *)
    echo "error: unknown family $fam (use weft, sans, shuttle or site)." >&2
    exit 1
    ;;
esac

(cd "$out" && sha256sum -- * | LC_ALL=C sort -k2 > "$stage/SHA256SUMS" && mv "$stage/SHA256SUMS" SHA256SUMS)
echo "Release files in $out:"
ls -l "$out"
