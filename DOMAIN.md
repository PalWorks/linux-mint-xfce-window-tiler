# Domain

The words this project uses and the rules they follow. Read this before changing the
engine: most bugs here come from mixing up two of these terms.

_Last updated: 2026-10-31T04:22:28+00:00 (first version)._

## Terms

| Term | Means |
|---|---|
| **Window** | A top-level application window the window manager manages. Only Wnck `NORMAL` windows that do not skip the taskbar are listed |
| **xid** | The X11 id of a window, for example `0x04400003`. Stable for the window's life, reused after it closes |
| **Client window** | The application's own X window, what the app draws into |
| **Frame** | The window manager's decoration around the client: title bar and borders, drawn by xfwm4 |
| **Frame extents** | Frame thickness on each side, frame geometry minus client geometry. Changes with state: a maximized terminal has `0,0,36,0`, the same window normal `2,36,2,2` |
| **Drawn shadow** | A transparent margin some apps paint inside their own client window (Chromium browsers, GTK header bar apps), advertised in `_GTK_FRAME_EXTENTS` as left, right, top, bottom. Invisible, but part of the window's size |
| **Work area** | The part of a monitor not reserved by panels, from Gdk. For a 1080p screen under a 33px top panel: `(0, 33, 1920, 1047)` |
| **Slot** | One rectangle `rects()` hands to one window. The visible part of the window should fill it |
| **Layout** | A rule for cutting the work area into slots: Side by side, Stacked, Grid, Main + side |
| **Gap** | Pixels left between slots and around the edge; 0, 4, 8 or 16 |
| **Tick order** | The order windows were ticked in the pop-up. It is the placement order |
| **Tile** | Apply a layout to the ticked windows |
| **Reset all** | Maximize every listed window, then minimize them all |
| **Snapshot** | What undo needs per window: xid, title, frame position, client size, maximized, minimized and full screen state, workspace |
| **Undo** | Restore the last snapshot, then delete it |
| **Stuck** | A window whose frame stayed bigger than its slot after tiling, usually an app minimum size |
| **Gone** | A window ticked in the pop-up that closed before the tile ran |
| **Settle** | Waiting, with a timeout, until the window manager has applied a state change |
| **Status icon** | The panel icon, an XApp status icon shown by `xapp-status-plugin` |
| **traykit** | The small scaffolding module behind the tray: icon, lock, menu |

## Rules

1. **Tick order is placement order.** Window 1 goes left or top, gets the large slot in
   Main + side, and ends up focused.
2. **Layouts need 2 or more windows; Grid needs 3.** `available()` decides what the pop-up
   shows.
3. **Slots fill the work area exactly when the gap is 0.** Leftover pixels go to the first
   slots. Tested in `tests/test_layouts.py`.
4. **Grid is never taller than wide**: columns are `ceil(sqrt(n))`, and the last row
   stretches across.
5. **Main + side gives window 1 60% of the width** (`MAIN_SHARE`).
6. **The target monitor is window 1's**, the one holding its centre.
7. **Windows are unmaximized and settled before frame extents are read**, because the
   extents change with state.
8. **A slot is grown by the window's drawn shadow**, so the visible part, not the X window,
   fills the slot.
9. **Reset all applies to every listed window**, not just ticked ones. Listed means the
   current workspace, or all workspaces when that setting is on.
10. **Undo is one level.** A new tile or reset replaces the snapshot; using it deletes it.
11. **Nothing is polled.** The window list is read once each time the pop-up opens.
