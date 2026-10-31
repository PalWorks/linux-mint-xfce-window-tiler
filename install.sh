#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 PalWorks
#
# Wire the tiler tray into this machine. Safe to run again.
#
#   1. symlink the scripts from src/ into $TILER_BIN_DIR
#   2. install the autostart entry
#   3. bind Super+T to open the pop-up
#   4. start the tray
#
# TILER_BIN_DIR defaults to ~/.local/lib/tiler-tray. Point it at a folder that
# already holds a traykit.py to share that one; it must be the version with
# left_click_menu, or the tray cannot take left clicks.
#
# ./install.sh --remove undoes all of it and stops the tray.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${TILER_BIN_DIR:-$HOME/.local/lib/tiler-tray}"
SHARE_DIR="$HOME/.local/share/tiler-tray"
AUTOSTART="$HOME/.config/autostart/tiler-tray.desktop"
KEY='/commands/custom/<Super>t'
SHOW="/usr/bin/python3 $BIN_DIR/tiler-tray.py --show"
FILES=(tiler-tray.py tiler_engine.py tiler_picker.py)

stop_tray() {
    # anchored, so the pattern cannot match this shell's own command line
    pkill -f "^/usr/bin/python3 $BIN_DIR/tiler-tray.py" || true
}

if [[ "${1:-}" == "--remove" ]]; then
    stop_tray
    for f in "${FILES[@]}" traykit.py; do
        # only our own symlinks, never a real traykit.py shared with other trays
        if [[ -L "$BIN_DIR/$f" && "$(readlink "$BIN_DIR/$f")" == "$HERE/src/$f" ]]; then
            rm "$BIN_DIR/$f"
        fi
    done
    rm -f "$AUTOSTART"
    if [[ "$(xfconf-query -c xfce4-keyboard-shortcuts -p "$KEY" 2>/dev/null || true)" == "$SHOW" ]]; then
        xfconf-query -c xfce4-keyboard-shortcuts -p "$KEY" -r
    fi
    echo "removed: symlinks, autostart entry, Super+T"
    exit 0
fi

for cmd in wmctrl xprop notify-send xfconf-query desktop-file-validate; do
    command -v "$cmd" >/dev/null || { echo "missing: $cmd" >&2; exit 1; }
done
/usr/bin/python3 -c 'import gi; gi.require_version("Wnck", "3.0"); gi.require_version("XApp", "1.0"); import PIL' \
    || { echo "missing: gir1.2-wnck-3.0, gir1.2-xapp-1.0 or python3-pil" >&2; exit 1; }

mkdir -p "$BIN_DIR"
for f in "${FILES[@]}"; do
    chmod +x "$HERE/src/$f"
    ln -sfn "$HERE/src/$f" "$BIN_DIR/$f"
done
if [[ -e "$BIN_DIR/traykit.py" && ! -L "$BIN_DIR/traykit.py" ]]; then
    grep -q left_click_menu "$BIN_DIR/traykit.py" \
        || { echo "$BIN_DIR/traykit.py predates left_click_menu; update it from src/traykit.py" >&2; exit 1; }
    echo "using the existing $BIN_DIR/traykit.py"
else
    ln -sfn "$HERE/src/traykit.py" "$BIN_DIR/traykit.py"
fi
echo "linked into $BIN_DIR"

mkdir -p "$(dirname "$AUTOSTART")"
sed -e "s|@BIN_DIR@|$BIN_DIR|" -e "s|@SHARE_DIR@|$SHARE_DIR|" \
    "$HERE/src/tiler-tray.desktop" > "$AUTOSTART"
desktop-file-validate "$AUTOSTART"
echo "autostart: $AUTOSTART"

existing="$(xfconf-query -c xfce4-keyboard-shortcuts -p "$KEY" 2>/dev/null || true)"
if [[ -n "$existing" && "$existing" != "$SHOW" ]]; then
    echo "Super+T is already bound to: $existing, left alone" >&2
else
    if [[ -z "$existing" ]]; then
        xfconf-query -c xfce4-keyboard-shortcuts -p "$KEY" -n -t string -s "$SHOW"
        # a binding created behind xfsettingsd's back is stored but not grabbed
        # until the daemon reloads
        setsid xfsettingsd --replace >/dev/null 2>&1 < /dev/null &
    fi
    echo "shortcut: Super+T"
fi

if ! pgrep -f "^/usr/bin/python3 $BIN_DIR/tiler-tray.py" >/dev/null; then
    setsid /usr/bin/python3 "$BIN_DIR/tiler-tray.py" >/dev/null 2>&1 < /dev/null &
    echo "started tray"
fi
