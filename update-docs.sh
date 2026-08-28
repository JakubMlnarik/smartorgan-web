#!/bin/sh
# update-docs.sh
#
# Updates the RPico-MIDI-projects submodule and copies user manual PDFs
# from each MIDI project app into the doc/ folder with explicit names.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOC_DIR="$SCRIPT_DIR/doc"
SUBMODULE_DIR="$SCRIPT_DIR/RPico-MIDI-projects"

echo "=== Updating RPico-MIDI-projects submodule ==="
git -C "$SCRIPT_DIR" submodule update --remote --init "$SUBMODULE_DIR"

echo ""
echo "=== Copying user manual PDFs ==="

# Map each app directory to a descriptive PDF name
copy_pdf() {
    local app_dir="$1"
    local dest_name="$2"
    local src="$SUBMODULE_DIR/apps/$app_dir/doc/user_manual/user_manual.pdf"
    local dest="$DOC_DIR/$dest_name"

    if [ -f "$src" ]; then
        cp "$src" "$dest"
        echo "  ✓ $dest_name"
    else
        echo "  ✗ $src not found — skipping"
    fi
}

copy_pdf "hall-scanner64"   "hall-scanner64-user-manual.pdf"
copy_pdf "input-module16"   "input-module16-user-manual.pdf"
copy_pdf "matrix-scanner64" "matrix-scanner64-user-manual.pdf"
copy_pdf "output-module16"  "output-module16-user-manual.pdf"

echo ""
echo "=== Done ==="
ls -lh "$DOC_DIR"/*.pdf 2>/dev/null || echo "(no PDFs in doc/)"
