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
# ./install.sh --service also runs the tray as a systemd user service that
# restarts it after a crash. Later plain runs keep the service; --no-service
# goes back to a plain autostart launch.
#
# ./install.sh --remove undoes all of it and stops the tray.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${TILER_BIN_DIR:-$HOME/.local/lib/tiler-tray}"
SHARE_DIR="$HOME/.local/share/tiler-tray"
AUTOSTART="$HOME/.config/autostart/tiler-tray.desktop"
UNIT_NAME=tiler-tray.service
UNIT="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/$UNIT_NAME"
KEY='/commands/custom/<Super>t'
SHOW="/usr/bin/python3 $BIN_DIR/tiler-tray.py --show"
FILES=(tiler-tray.py tiler_engine.py tiler_picker.py)
SESSION_VARS="DISPLAY XAUTHORITY DBUS_SESSION_BUS_ADDRESS"

case "${1:-}" in
    ""|--service|--no-service|--remove) ;;
    *) echo "usage: $0 [--service | --no-service | --remove]" >&2; exit 2 ;;
esac

stop_tray() {
    if [[ -f "$UNIT" ]] && command -v systemctl >/dev/null; then
        systemctl --user stop "$UNIT_NAME" 2>/dev/null || true
    fi
    # anchored, so the pattern cannot match this shell's own command line
    pkill -f "^/usr/bin/python3 $BIN_DIR/tiler-tray.py" || true
}

remove_unit() {
    # only a unit this script wrote
    if [[ -f "$UNIT" ]] && grep -q "install.sh --service" "$UNIT"; then
        systemctl --user stop "$UNIT_NAME" 2>/dev/null || true
        rm "$UNIT"
        systemctl --user daemon-reload 2>/dev/null || true
        echo "removed: $UNIT"
    fi
}

if [[ "${1:-}" == "--remove" ]]; then
    stop_tray
    remove_unit
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

# --service turns the service on, --no-service off; otherwise keep what an
# earlier run set up, so a plain re-run never undoes --service
service=0
case "${1:-}" in
    --service) service=1 ;;
    --no-service) stop_tray; remove_unit ;;
    *) [[ -f "$UNIT" ]] && service=1 ;;
esac

for cmd in wmctrl xprop notify-send xfconf-query desktop-file-validate; do
    command -v "$cmd" >/dev/null || { echo "missing: $cmd" >&2; exit 1; }
done
/usr/bin/python3 -c 'import gi; gi.require_version("Wnck", "3.0"); gi.require_version("XApp", "1.0"); import PIL' \
    || { echo "missing: gir1.2-wnck-3.0, gir1.2-xapp-1.0 or python3-pil" >&2; exit 1; }
if (( service )); then
    systemctl --user show-environment >/dev/null 2>&1 \
        || { echo "--service needs a systemd user session (systemctl --user)" >&2; exit 1; }
fi

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
if (( service )); then
    # start the unit at login, once the session's display is known to systemd
    sed -i "s|^Exec=.*|Exec=/bin/sh -c \"systemctl --user import-environment $SESSION_VARS; systemctl --user start $UNIT_NAME\"|" \
        "$AUTOSTART"
fi
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

if (( service )); then
    mkdir -p "$(dirname "$UNIT")"
    sed -e "s|@BIN_DIR@|$BIN_DIR|" "$HERE/src/$UNIT_NAME" > "$UNIT"
    systemctl --user daemon-reload
    # shellcheck disable=SC2086
    systemctl --user import-environment $SESSION_VARS
    if ! systemctl --user is-active --quiet "$UNIT_NAME"; then
        # a tray started by hand holds the lock and would make the unit exit
        pkill -f "^/usr/bin/python3 $BIN_DIR/tiler-tray.py" || true
        for _ in 1 2 3 4 5 6 7 8 9 10; do
            pgrep -f "^/usr/bin/python3 $BIN_DIR/tiler-tray.py" >/dev/null || break
            sleep 0.3
        done
        systemctl --user start "$UNIT_NAME"
        echo "started tray as $UNIT_NAME"
    fi
    echo "service: $UNIT, restarts the tray after a crash"
elif ! pgrep -f "^/usr/bin/python3 $BIN_DIR/tiler-tray.py" >/dev/null; then
    setsid /usr/bin/python3 "$BIN_DIR/tiler-tray.py" >/dev/null 2>&1 < /dev/null &
    echo "started tray"
fi
