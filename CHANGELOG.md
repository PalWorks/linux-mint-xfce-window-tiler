# Changelog

Timestamps ISO 8601 in UTC (`+00:00`).

## 0.2.6, 2026-11-01T17:19:41+00:00

### Fixed
- A sibling traykit tray segfaulted again on 2026-11-01, after the 0.2.4 guard: a new
  menu was still swapped in on every poll, and GDK could still hold events for the old
  one. traykit now hands the panel one menu for the life of the process and edits its
  rows in place on each rebuild (labels, action callbacks, sensitivity, submenus). Rows
  that cannot be edited in place, such as check and radio items, are swapped inside the
  same menu, kept alive one more rebuild, then destroyed. The `render()` hook is
  unchanged, so existing trays need no edits.

## 0.2.5, 2026-10-31T05:26:41+00:00

### Changed
- The panel icon no longer has a divider line drawn into its left edge, and the pop-up
  header uses space instead of a vertical line between Select all / Clear and Reset all.
  Separators are left to the panel's own Separator item (DECISIONS D16).

## 0.2.4, 2026-10-31T05:15:42+00:00

### Fixed
- A traykit tray could segfault if its periodic refresh landed while its dropdown was
  open: the menu was replaced mid-use and GDK delivered events to the freed one. Seen in
  a sibling tray on 4 dates, the last on 2026-10-31. traykit now postpones a rebuild until
  the menu hides, and keeps the previous menu alive one more generation.

## 0.2.3, 2026-10-31T04:31:24+00:00

### Fixed
- The "would not shrink" notification named windows by their full titles, which run long
  and can hold email addresses or project names. It now names the app, once each, in a
  readable sentence, and points to Main + side, Grid or Undo.

### Verified
- All four layouts on real windows: Grid on 7 (maintainer); Side by side, Stacked and
  Main + side on 4 real windows (Edge, Chrome, Sublime Text, an Electron IDE), each undone.
  Main + side and Stacked fitted to the pixel apart from one IDE's minimum height; Side by
  side at 480px each overlapped where three apps have minimum widths above 480px, and all
  three were reported.
- Clicking next to a tiled browser on every side does not hit its invisible shadow.

## 0.2.2, 2026-10-31T04:22:28+00:00

Documentation and privacy release; no behaviour change. Git history squashed into one
commit and every timestamp converted to UTC, so nothing public carries a local offset.

### Added
- ARCHITECTURE.md (components, data flow, placement arithmetic, process model, files),
  DOMAIN.md (terms and rules), LIMITATIONS.md, PLAYBOOK.md (feature, layout, debug,
  release, roll back).
- `tests/test_roadmap.py`: ROADMAP.md consistency checks from the roadmap guide. It found
  a cited §8 with no heading, now added.
- README: Deployment and upgrades, Security and performance sections.
- ROADMAP: recurring pre-push privacy scan (row 21), timestamp offset decision (row 22),
  §4 Deferred table.

### Changed
- Environment details generalised to "Linux Mint 22 XFCE, X11, one 1080p monitor"; exact
  package versions removed from the docs.

## 0.2.1, 2026-10-30T20:10:41+00:00

### Fixed
- Chromium-based browsers (Edge, Chrome) and GTK header bar apps came out visibly smaller
  than their slot, about 20px short on every side. They draw an invisible shadow inside
  their own window and advertise it in `_GTK_FRAME_EXTENTS`, which xfwm4 ignores. The
  engine now grows each slot by that shadow, and places again if the shadow only appears
  after unmaximizing.

### Changed
- `xprop` (`x11-utils`) is now a dependency, checked by `install.sh`.

## 0.2.0, 2026-10-30T20:00:46+00:00

### Added
- **Reset all** in the pop-up header: maximize every listed window, then minimize them all.
  Undoable; `tiler_engine.py --reset <xid>...` on the command line.
- Select all, Clear and Reset all are icon-only buttons with a title and description in the
  tooltip, at least 40px square.
- `TILER_BIN_DIR` for `install.sh` (default `~/.local/lib/tiler-tray`), dependency checks,
  autostart entry generated from a template, `--remove` touches only its own symlinks and
  binding.
- `src/traykit.py` shipped in the repo.
- LICENSE (AGPL 3.0), COMMERCIAL-LICENSE.md, CONTRIBUTING.md, SECURITY.md, SPDX headers.

### Fixed
- The pop-up flashed full height in the wrong place before jumping into position on every
  click. It now settles size and position before it maps.
- Too much space between checkbox and app icon: the position number moved to the right end
  of the row.
- Undo now clears maximized, full screen and minimized state first, so it also reverses a
  Reset.

### Changed
- Right-click menu item renamed to "Undo last tile or reset".

## 0.1.0, 2026-10-30T19:44:13+00:00

First build.

### Added
- `src/tiler_engine.py`: four layouts (Side by side, Stacked, Grid, Main + side), gaps,
  tile with unmaximize, restore, workspace move and frame allowance, one-level undo, CLI.
- `src/tiler_picker.py`: pop-up with numbered ticks, search at 9 or more windows, layout
  bar with live pictures, keyboard control.
- `src/tiler-tray.py`: panel icon, right-click menu (Undo, gap, all workspaces, Quit),
  notifications, `--show` over SIGUSR1.
- `traykit.py` extended: `poll_seconds = 0`, `show_refresh`, `left_click_menu` and
  `primary_click()`; no doubled separator. Backwards compatible.
- `install.sh`, autostart entry, Super+T.
- `tests/test_layouts.py`, 9 tests. Docs.

### Fixed during the build
- Segfault after Undo from the tray menu: rebuild deferred out of the menu handler.
