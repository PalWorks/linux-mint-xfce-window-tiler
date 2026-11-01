# Decisions

Why things are the way they are. Newest last. Timestamps ISO 8601 in UTC (`+00:00`).

_Last updated: 2026-11-01T18:07:35+00:00 (D18 added)._

## D1. A custom tray, not X-Tile's own tray mode (maintainer, 2026-10-31)

| Option | Verdict |
|---|---|
| A. Enable X-Tile's tray icon | Rejected: opens a full app window, not a pop-up; its icon goes to the XEmbed systray, apart from the XApp status icons; "vertically/horizontally" read both ways |
| **B. Custom tray with its own engine** | **Chosen** |
| C. Custom pop-up calling X-Tile's internal `tilings.py` | Rejected: X-Tile's CLI tiles only all windows, and importing package internals breaks on any update |

## D2. Read windows with Wnck, move them with `wmctrl -e`

Measured on 2026-10-31, target frame `(0, 33, 640, 1047)`:

| Method | Result |
|---|---|
| `Wnck.Window.set_geometry`, NORTHWEST gravity | frame at `(2, 69)`, offset by the frame extents `2, 36` |
| `Wnck.Window.set_geometry`, STATIC gravity, client coordinates | frame again offset by the extents |
| **`wmctrl -i -r <id> -e 0,<frame x>,<frame y>,<client w>,<client h>`** | **frame exactly `(0, 33, 640, 1047)`** |

xfce4-terminal snaps down to whole character cells (for example `957x514` in a
`960x524` slot). That is the terminal's size hints, accepted, not corrected.

## D3. One pop-up, layout bar appears after two ticks (maintainer, 2026-10-31)

The first draft had two screens: pick windows, then pick a layout. Merged: the layout bar
is hidden until 2 windows are ticked, so the first screen still shows one thing to do, and
tiling takes one click less.

## D4. Plain layout names

"Side by side" and "Stacked" instead of "vertical" and "horizontal", which people read
both ways. Each button also draws the result for the current number of ticked windows.

## D5. Tick order is placement order

Window 1 goes left or top, gets the large slot in Main + side, and ends up focused. The
position number shows at the right end of each ticked row (moved there in 0.2.0 so an
unticked row has no empty slot beside its checkbox).

## D6. Super+T opens the pop-up (maintainer, 2026-10-31)

The key runs `tiler-tray.py --show`, which sends SIGUSR1 to the pid in the lock file, so
the running tray opens the pop-up. If no tray is running, it starts one that opens it.

## D7. Source in the clone, symlinked into an install folder

`install.sh` symlinks `src/` into `TILER_BIN_DIR` (default `~/.local/lib/tiler-tray`).
The scripts put `dirname(abspath(__file__))` on `sys.path`, and `abspath` does not resolve
symlinks, so imports resolve in the install folder. That lets several traykit-based trays
share one `traykit.py` by installing into the same folder.

## D8. Extend traykit rather than fork it

Three optional class attributes, all defaulting to the old behaviour: `poll_seconds = 0`
(no timer), `show_refresh` (Refresh now item) and `left_click_menu` (when `False`, left
click calls `primary_click(x, y, time)`; XApp then gets no primary menu and hands the click
over). Two existing traykit trays were restarted on the extended file and came back.

## D9. No polling

Nothing about windows needs watching while the pop-up is closed. The list is read on open.

## D10. Undo is one level, stored on disk

`undo.json` lets the command line and the tray share one snapshot and survives a tray
restart. A second tile or reset replaces it; it is deleted once used.

## D11. Reset all maximizes, then minimizes, every listed window (maintainer, 2026-10-31)

A one-click clean desk. It applies to every window the pop-up lists (current workspace, or
all workspaces when that setting is on), not only ticked ones, because it is a whole-desk
action. No confirmation dialog: it is fully undoable, and a notification says how to undo.
It is the right-most header icon, set apart from Select all and Clear by extra space, so it
is not mistaken for clearing the ticks.

## D12. Licence: AGPL 3.0 or a paid commercial licence (maintainer, 2026-10-31)

Open source that Linux users and distributions accept, with a commercial licence for anyone
who cannot meet the AGPL's obligations. Contributions need a licence grant to the
maintainer (CONTRIBUTING.md), or the commercial option could not cover them.

## D13. Ship `traykit.py` in the repo

The tray cannot run without it. It is generic scaffolding with nothing machine-specific, so
it ships in `src/`. The installer reuses an existing real `traykit.py` in the install
folder instead, if it is new enough.

## D14. Icon-only header buttons (maintainer, 2026-10-31)

Select all, Clear and Reset all are icons with the name in bold and a one-line description
in the tooltip, at the maintainer's request, to keep the header uncluttered. Each is at
least 40px square and carries an accessible name, so keyboard and screen reader use still
work. The layout buttons keep their text labels: they are the main action.

## D15. Allow for client-side shadows (`_GTK_FRAME_EXTENTS`)

Seen 2026-10-31 in a real 6-window grid: Edge looked smaller than its neighbours. Its X
window filled the 640x524 slot exactly, but Edge draws a transparent shadow of 22, 22,
19, 25 px (left, right, top, bottom) inside that window, so the visible part was about
600x480. xfwm4 reports `_NET_FRAME_EXTENTS` 0 for it and ignores `_GTK_FRAME_EXTENTS`.

The engine reads `_GTK_FRAME_EXTENTS` with `xprop` and enlarges the X window by it, so the
visible part fills the slot. Verified on a GTK header bar test window (shadow 26, 26, 23,
29): visible area landed exactly on `(960, 33, 960, 1047)`. The invisible shadow then
overlaps the neighbouring slot, which is how every CSD-aware tiler behaves.

## D16. No separator lines drawn by code (maintainer, 2026-10-31)

Earlier the panel icon carried a thin divider drawn into its left edge, because every XApp
status icon shares one panel plugin and a panel separator cannot sit between two of them.
The maintainer prefers the panel's own separators, added in Panel Preferences, and no
other kind of line. So the icon is drawn without one, and the pop-up header separates
Reset all from Select all and Clear by space, not a line. Any future separator goes through
the panel's Separator item only.

## D17. One tray menu for the life of the process (2026-11-01)

0.2.4 stopped traykit from swapping the menu while it was open, and kept the previous menu
alive one generation. A sibling tray still segfaulted inside GTK on 2026-11-01 with its
menu closed: every rebuild still handed the panel a new menu and let an older one go while
GDK could hold events for it.

traykit now creates one `Gtk.Menu` when the tray starts and hands it to the status icon
once. `rebuild()` lets the tray's `render()` fill a scratch menu that is never shown, then
`_sync()` copies it onto the live menu row by row: rows made with `label_item()` and
`action_item()`, separators and submenus are edited in place (text, click handler,
sensitivity); any other widget, such as a check or radio item, is swapped within the same
menu, kept one more rebuild, then destroyed. The `render()` hook did not change, so trays
built on traykit need no edits. Rejected: keeping every old menu alive forever (leaks one
menu per poll) and a full rewrite of the hooks around row objects (breaks every tray).

## D18. Restart after a crash is opt-in, and sticky (maintainer, 2026-11-01)

`install.sh --service` writes a systemd user unit and points the autostart entry at it,
instead of launching the tray directly. The default install is unchanged: not every XFCE
setup runs a systemd user session, and a plain launch keeps the tray easy to reason about.

- `Restart=on-abnormal`, not `on-failure`: a crash signal restarts the tray, but Quit
  (exit 0) does not bring back a tray the user closed, and losing the display at logout
  (exit 1) does not loop. `StartLimitBurst=5` in 120 seconds stops a crash loop.
- The autostart entry starts the unit, with `systemctl --user import-environment` first,
  rather than enabling it under `graphical-session.target`: xfce4-session does not
  activate that target, so the unit would never start at login.
- Sticky: once the unit exists, a plain `./install.sh` keeps it, so an upgrade never
  silently drops the restart. `--no-service` is the way back. `--remove` deletes the unit
  only if it carries the installer's marker comment.
