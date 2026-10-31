# Requirements

Agreed with the maintainer on 2026-10-31: custom tray (D1), one pop-up with the layout bar
(D3), Super+T (D6); Reset all added the same day (D11). Status is what was verified, not
what was intended.

_Last updated: 2026-10-30T20:00:46+00:00 (R12 Reset all; R2 flash fixed; R4 spacing)._

**Table R1: Requirements and status**

| ID | Requirement | Status | Where |
|---|---|---|---|
| R1 | Panel icon: light three-pane icon, no text, tooltip naming Super+T. Left click opens the pop-up, right click opens Undo, Settings, Quit | Verified on screen | `tiler-tray.py` `draw_icon`, `render` |
| R2 | Pop-up 360px wide, under the icon, no flash or jump while opening; closes on Esc, second icon click, or click elsewhere | Verified: single geometry from first frame; all three close paths | `tiler_picker.py` `__init__`, `_place`, `_on_key`, `_on_focus_out` |
| R3 | List normal windows on the current workspace, most recent first; icon, title, app; minimized dimmed but selectable | Verified; panel, desktop and the pop-up itself excluded | `tiler_engine.list_windows` |
| R4 | Tick order sets position, shown as numbers at the row's right end; checkbox sits next to the app icon; whole row toggles; rows at least 40px | Verified | `tiler_picker.py` `_row` |
| R5 | Search box at 9 or more windows; Select all and Clear as icon-only buttons, title and description in the tooltip, at least 40px | Verified on screen | `SEARCH_FROM`, `_icon_button` |
| R6 | Layout bar after 2 ticks: Side by side, Stacked, Grid (3 or more), Main + side; one click applies; nonsensical layouts hidden | Verified | `tiler_engine.available`, `rects` |
| R7 | Leave full screen, unmaximize, restore minimized, move to current workspace, fit inside the work area, allow for title bars and drawn shadows (`_GTK_FRAME_EXTENTS`), optional gap, raise and focus window 1 | Verified on test windows, including maximized and minimized. **Not yet tried on Electron or Chromium-based apps** | `tiler_engine.tile` |
| R8 | Undo restores position, size, maximized, minimized, full screen state, workspace | Verified, 5 cycles through the UI, and after Reset | `tiler_engine.undo` |
| R9 | Super+T; Up/Down, Space, 1 to 9, Enter (last layout), Esc | Verified | `install.sh`, `_on_key` |
| R10 | Closed windows skipped; windows that will not shrink reported; full screen handled | "Would not shrink" verified. Closed-window path not triggered in a test | `tile()` returns `stuck`, `gone` |
| R11 | No polling, one instance, autostart, no network, no new packages beyond the listed dependencies | Verified except autostart through a real login (ROADMAP row 10) | `poll_seconds = 0`, lock, `tiler-tray.desktop` |
| R12 | **Reset all**: one icon-only header button, set apart from Select all and Clear, maximizes every listed window, then minimizes them all; undoable; notification says how to undo | Verified on test windows, including Undo | `tiler_engine.reset`, `tiler_picker._reset`, `TilerTray._reset` |
