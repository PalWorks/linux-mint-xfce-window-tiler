# Testing

_Last updated: 2026-11-01T18:07:35+00:00 (installer --service modes)._

## Automated

```bash
/usr/bin/python3 -m unittest discover -s tests -v
```

`tests/test_layouts.py`, 9 tests, no X needed. For every layout, 2 to 9 windows, gap 0
and 8: the right number of rectangles, all inside the area, no overlaps, and with gap 0 the
rectangles cover the area exactly. Plus fixed expectations for side by side 3, stacked 2,
grid 3 and main + side 3 on a `(0, 33, 1920, 1047)` work area (1080p under a 33px top
panel).

`tests/test_roadmap.py`, 8 tests: the State legend is exactly the guide's vocabulary and
every ledger state is in it, numbers 1 to N each
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

**Table T2: Real windows, 2026-10-31**

Four real windows: Edge, Chrome, Sublime Text and an Electron IDE, from a 7-window grid,
each layout undone straight after. Visible area is the X window minus any drawn shadow.

| Layout | Result |
|---|---|
| Grid, 7 windows (maintainer) | Every window fills its slot, browsers included |
| Clicks next to a tiled browser, all sides (maintainer) | Nothing triggered; the shadow does not take clicks |
| Side by side, 480px slots | Edge 574, Chrome 500 and Sublime 518 px wide at minimum, so they overlap; all three reported as stuck. The IDE fitted exactly |
| Stacked, 262px slots | Three fitted to the pixel; the IDE's minimum height is 270, 9px over, reported as stuck |
| Main + side | All four exact to the pixel |
| Undo after each | Windows returned to the state they were in before the test |

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
| The overlap notification listed whole window titles (0.2.3) | Names the app instead, once each |
| A sibling traykit tray segfaulted again with the menu closed (0.2.6) | One live menu, rows edited in place. Self-test against all three real trays' `render()`, status icon stubbed: same widgets reused when the row count holds, labels and callbacks updated, submenus kept, extra rows retired then destroyed a rebuild later, open menu untouched; tiler menu stable over repeated rebuilds |
| A sibling traykit tray segfaulted when its 5-minute refresh hit while its dropdown was open (0.2.4) | `rebuild()` postponed while the menu is open. Self-test: a rebuild called with the menu open did not swap it and set a pending flag; after the menu hid, it swapped and kept the old menu alive |

## Installer, `--service` (2026-11-01)

Run on the maintainer's machine with an existing shared `traykit.py`:

**Table T3: install.sh modes**

| Step | Result |
|---|---|
| `--service` over a hand-written unit | Unit rewritten with the marker, service active, one tray process, autostart starts the unit |
| `--no-service` | Unit removed, tray restarted by plain launch, autostart back to a plain launch |
| Plain run after that | Stays plain |
| `--service` again with a tray started by hand | Hand-started tray stopped, service started, one process |
| Plain run with the unit present | Service kept |
| `kill -KILL` on the tray | New pid 3 seconds later |
| `--remove`, in a scratch `HOME` with `systemctl`, `xfconf-query` and `pkill` stubbed | Unit, symlinks and autostart entry removed; service stopped and daemon reloaded |
| Unknown flag | Usage message, exit 2 |

## Not yet tested

| Gap | Next step |
|---|---|
| Autostart after a real login | Check at the next login (ROADMAP row 10), with and without `--service` |
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
