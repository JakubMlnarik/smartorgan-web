#!/bin/sh
# update-docs.sh
#
# Updates submodules and copies user manual PDFs from each project
# into the doc/ folder with explicit names.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOC_DIR="$SCRIPT_DIR/doc"

MIDI_SUBMODULE="$SCRIPT_DIR/RPico-MIDI-projects"
KEYBOARD_SUBMODULE="$SCRIPT_DIR/Keyboard-docs"

echo "=== Updating RPico-MIDI-projects submodule ==="
git -C "$SCRIPT_DIR" submodule update --remote --init "$MIDI_SUBMODULE"

echo ""
echo "=== Updating Keyboard-docs submodule ==="
git -C "$SCRIPT_DIR" submodule update --remote --init "$KEYBOARD_SUBMODULE"

echo ""
echo "=== Copying user manual PDFs ==="

# Map each app directory to a descriptive PDF name
copy_pdf() {
    local app_dir="$1"
    local dest_name="$2"
    local src="$MIDI_SUBMODULE/apps/$app_dir/doc/user_manual/user_manual.pdf"
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

# Keyboard-docs — single PDF at the repo root
KEYBOARD_SRC="$KEYBOARD_SUBMODULE/user_manual/user_manual.pdf"
KEYBOARD_DEST="$DOC_DIR/kinetic-keyboard-user-manual.pdf"
if [ -f "$KEYBOARD_SRC" ]; then
    cp "$KEYBOARD_SRC" "$KEYBOARD_DEST"
    echo "  ✓ kinetic-keyboard-user-manual.pdf"
else
    echo "  ✗ $KEYBOARD_SRC not found — skipping"
fi

echo ""
echo "=== Done ==="
ls -lh "$DOC_DIR"/*.pdf 2>/dev/null || echo "(no PDFs in doc/)"
