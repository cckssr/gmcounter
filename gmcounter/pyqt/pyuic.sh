#!/bin/bash
# Regenerate the ui_<form>.py modules from the Qt Designer .ui files.
#
#   gmcounter/pyqt/pyuic.sh                       # every form
#   gmcounter/pyqt/pyuic.sh connection mainwindow # only these forms (stems without .ui)
#
# First copies the German strings from config.json into the .ui files (see sync_texts.py), then
# runs pyside6-uic and formats the generated modules (ruff if available, else black).
# Exits non-zero on any failure.
set -euo pipefail
cd "$(dirname "$0")/../.."

PYQT_DIR=gmcounter/pyqt

# Prefer the project's virtual environment, fall back to whatever is on PATH.
if [ -x .venv/bin/python ]; then PYTHON=.venv/bin/python; else PYTHON=python; fi
if [ -x .venv/bin/pyside6-uic ]; then UIC=.venv/bin/pyside6-uic; else UIC=pyside6-uic; fi

"$PYTHON" -m gmcounter.pyqt.sync_texts "$@"  # only the named forms, if any

if [ "$#" -gt 0 ]; then
    stems=("$@")
else
    stems=()
    for f in "$PYQT_DIR"/*.ui; do
        stems+=("$(basename "${f%.ui}")")
    done
fi

outputs=()
for stem in "${stems[@]}"; do
    src="$PYQT_DIR/$stem.ui"
    out="$PYQT_DIR/ui_$stem.py"
    if [ ! -f "$src" ]; then
        echo "Error: $src does not exist" >&2
        exit 1
    fi
    "$UIC" "$src" -o "$out"
    outputs+=("$out")
    echo "generated $out"
done

if [ -x .venv/bin/ruff ]; then
    .venv/bin/ruff format "${outputs[@]}"
elif command -v ruff >/dev/null 2>&1; then
    ruff format "${outputs[@]}"
elif [ -x .venv/bin/black ]; then
    .venv/bin/black -q "${outputs[@]}"
elif command -v black >/dev/null 2>&1; then
    black -q "${outputs[@]}"
else
    echo "warning: neither ruff nor black found, generated files are not formatted" >&2
fi
echo "UI files converted successfully"
