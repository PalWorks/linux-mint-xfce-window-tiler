# Testing

_Last updated: 2026-10-31T04:22:28+00:00 (roadmap tests added)._

## Automated

```bash
/usr/bin/python3 -m unittest discover -s tests -v
```

`tests/test_layouts.py`, 9 tests, no X needed. For every layout, 2 to 9 windows, gap 0
and 8: the right number of rectangles, all inside the area, no overlaps, and with gap 0 the
rectangles cover the area exactly. Plus fixed expectations for side by side 3, stacked 2,
grid 3 and main + side 3 on a `(0, 33, 1920, 1047)` work area (1080p under a 33px top
panel).

`tests/test_roadmap.py`, 8 tests: every ledger state is in the legend, numbers 1 to N each
once, pending rows above Done rows, every cited § has a heading, §0 matches the ledger on
rows, states and sections, priorities come from a contiguous legend, no empty Problem or
next-step cell, every linked document exists.

Result on 2026-10-31: 17 passed.

## Live, on throwaway windows

Test windows are plain `Gtk.Window`s titled `tilertest1` and so on, plus one
`xfce4-terminal --disable-server --title tilertest4`. Environment: Linux Mint 22 XFCE
(Xfce 4.18, xfwm4), X11, one 1080p monitor, panel at the top.

**Table T1: Live checks, 2026-10-31**

| Check | Result |
|---|---|
| All four layouts from the CLI, 4 windows, some maximized, one minimized | Gtk windows exact to the pixel; the terminal snapped to character cells, smaller than its slot |
| Undo after a tile from maximized and minimized | All maximized again; the minimized one minimized again |
| Window with minimum width 800 in a 384px slot | Reported in `stuck` |
| Pop-up through `--show` | Opens centred near the top, takes focus |
| Pop-up through a left click on the icon | Opens under the icon, takes focus |
| Second click on the icon | Closes the pop-up |
| Focusing another window | Closes the pop-up |
| Keys 1, 3, 2 then Enter | Windows landed left to right in tick order; window 1 focused; `last_layout` saved |
| Right-click menu | Tile windows…, Undo last tile or reset, Gap submenu, all workspaces toggle, Quit |
| Undo from the menu | Restored; `undo.json` deleted |
| 5 tile and undo cycles through the real UI | Tray alive after every cycle |
| Super+T | Opens the pop-up, after `xfsettingsd --replace` |
| Other traykit trays restarted on the extended traykit | Both icons back |
| Pop-up geometry polled from the first frame it exists (0.2.0) | One geometry only, `1049,37 360x427`: no flash |
| Reset of 2 side-by-side windows (0.2.0) | Both maximized, then minimized (unmapped, `HIDDEN`) |
| Undo after Reset (0.2.0) | Both visible again at their side-by-side positions, not maximized |
| GTK header bar window, shadow 26, 26, 23, 29, beside a plain window, side by side, both starting maximized (0.2.1) | X window `934,10 1012x1099`, so the visible part is exactly `960,33 960x1047`; plain window unchanged |

## Found and fixed during testing

| Defect | Fix |
|---|---|
| Tray segfaulted in `gdk_display_get_event` right after Undo from the menu | Rebuild deferred 300ms out of the menu handler, `_rebuild_soon()`; 5 cycles clean after |
| Pop-up flashed full height at the wrong spot, then jumped into place (user report) | Children shown and size and position settled before the window maps |
| Wide empty gap between checkbox and app icon (user report) | Position number moved to the right end of the row; row spacing 8 to 6 |
| Tick badges stretched to ovals | `set_valign(CENTER)` |
| Two separators before Quit when a tray has no extra actions | traykit adds the second only when something sits between |
| Super+T did nothing after binding | `xfsettingsd` needs a reload; added to `install.sh` |
| Undo could not bring back windows that a later step minimized | Undo now unmaximizes, leaves full screen and unminimizes before restoring |
| A Chromium-based browser looked about 20px smaller on each side than its neighbours (maintainer report, 0.2.1) | Slot grown by the window's `_GTK_FRAME_EXTENTS` shadow (DECISIONS D15) |

## Not yet tested

| Gap | Next step |
|---|---|
| Electron and Chromium-based app windows, which often have minimum sizes | Maintainer trial; Undo puts everything back (ROADMAP row 9) |
| Autostart after a real login | Check at the next login (ROADMAP row 10) |
| Second monitor, HiDPI scaling, Wayland | No hardware or session for it yet (ROADMAP rows 11, 12) |

## Re-running the live checks

```bash
BIN=~/.local/lib/tiler-tray
S=$(mktemp -d)
cat > "$S/testwin.py" <<'EOF'
import sys, gi; gi.require_version('Gtk','3.0'); from gi.repository import Gtk
w = Gtk.Window(title=sys.argv[1]); w.set_default_size(500, 400)
w.connect('destroy', Gtk.main_quit); w.show_all(); Gtk.main()
EOF
for i in 1 2 3; do /usr/bin/python3 "$S/testwin.py" tilertest$i & done; sleep 1.5
ids=$(wmctrl -l | awk '/tilertest/{print $1}')
/usr/bin/python3 $BIN/tiler_engine.py --layout grid $ids
/usr/bin/python3 $BIN/tiler_engine.py --reset $ids
/usr/bin/python3 $BIN/tiler_engine.py --undo
for id in $ids; do wmctrl -i -c $id; done
```
