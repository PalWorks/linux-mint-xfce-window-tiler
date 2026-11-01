# Runbook

When something goes wrong, top to bottom. `BIN` below is your `TILER_BIN_DIR`, default
`~/.local/lib/tiler-tray`.

_Last updated: 2026-11-01T17:48:27+00:00 (restart after a crash)._

**Table K1: Symptoms and fixes**

| Symptom | Check | Fix |
|---|---|---|
| No three-pane icon in the panel | `pgrep -af "^/usr/bin/python3 $BIN/tiler-tray.py"` | Not running: start it, `/usr/bin/python3 $BIN/tiler-tray.py &`, and read any error. Running but invisible: `xfce4-panel -r` |
| Icon gone after it was working | `journalctl --since today \| grep -A3 'python3.*segfault'` | A crash. Restart it, note what you clicked, and report it (SECURITY.md has where). Check you run 0.2.6 or later, which fixed the known menu crash. To have it come back by itself, see "Restart after a crash" |
| Super+T does nothing | `xfconf-query -c xfce4-keyboard-shortcuts -p '/commands/custom/<Super>t'` | Missing: `./install.sh`. Present: `setsid xfsettingsd --replace >/dev/null 2>&1 &` |
| Super+T does nothing while a tray menu is open | | Expected: an open menu holds the keyboard grab. Close it first |
| Pop-up does not list a window | `$BIN/tiler_engine.py --list --all` | Other workspace: right click, tick "List windows from all workspaces". Not listed at all: it is not a normal window or skips the taskbar, by design |
| A window overlaps its neighbour after tiling | The notification names it | App minimum size. Use Grid or fewer windows, or Undo |
| Windows land a few pixels short | Compare `xwininfo -id <id>` with `tiler_engine.rects(...)` | Terminals snap to whole character cells, expected |
| Undo greyed out | `ls ~/.local/share/tiler-tray/undo.json` | Nothing to undo: deleted once used; a new tile or reset replaces it |
| `ModuleNotFoundError: gi` | Which python ran it | Must be `/usr/bin/python3` |
| `ModuleNotFoundError: traykit` or `tiler_engine` | `ls -la $BIN` | Symlinks missing, or the clone moved: run `./install.sh` again from the clone |

## Restart cleanly

```bash
pkill -f "^/usr/bin/python3 $BIN/tiler-tray.py"
setsid /usr/bin/python3 $BIN/tiler-tray.py >/dev/null 2>&1 &
```

## Restart after a crash (optional)

Not set up by `install.sh` yet (ROADMAP row 27). A systemd user unit brings the tray back
3 seconds after a crash. Save as `~/.config/systemd/user/tiler-tray.service`, with `BIN`
written out in full:

```ini
[Unit]
Description=Window tiler tray
StartLimitIntervalSec=120
StartLimitBurst=5

[Service]
Type=simple
ExecStart=/usr/bin/python3 BIN/tiler-tray.py
# restart after a crash signal, not after Quit (exit 0) or logout (exit 1)
Restart=on-abnormal
RestartSec=3
```

Then point the autostart entry at it, so it starts once the session has a display:

```bash
sed -i 's|^Exec=.*|Exec=/bin/sh -c "systemctl --user import-environment DISPLAY XAUTHORITY DBUS_SESSION_BUS_ADDRESS; systemctl --user start tiler-tray.service"|' \
  ~/.config/autostart/tiler-tray.desktop
systemctl --user daemon-reload
```

Restart it with `systemctl --user restart tiler-tray.service` from then on. Re-running
`./install.sh` rewrites the autostart entry, so repeat the `sed` after it. Tried
2026-11-01: `kill -KILL` on the tray, back with a new pid 3 seconds later, icon on the
panel.

## Take it out entirely

```bash
./install.sh --remove     # from the clone, with the same TILER_BIN_DIR you installed with
```
