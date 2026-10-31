# Runbook

When something goes wrong, top to bottom. `BIN` below is your `TILER_BIN_DIR`, default
`~/.local/lib/tiler-tray`.

_Last updated: 2026-10-30T20:00:46+00:00 (paths made install-relative, Reset added)._

**Table K1: Symptoms and fixes**

| Symptom | Check | Fix |
|---|---|---|
| No three-pane icon in the panel | `pgrep -af "^/usr/bin/python3 $BIN/tiler-tray.py"` | Not running: start it, `/usr/bin/python3 $BIN/tiler-tray.py &`, and read any error. Running but invisible: `xfce4-panel -r` |
| Icon gone after it was working | `journalctl --since today \| grep -A3 'python3.*segfault'` | A crash. Restart it, note what you clicked, and report it (SECURITY.md has where) |
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

## Take it out entirely

```bash
./install.sh --remove     # from the clone, with the same TILER_BIN_DIR you installed with
```
