# Limitations

Known limits, edge cases and debt, so nobody rediscovers them. Each says what to do about
it. Open work for any of them is tracked in [ROADMAP.md](ROADMAP.md).

_Last updated: 2026-10-31T04:22:28+00:00 (first version)._

**Table L1: Known limitations**

| Limitation | Effect | What to do |
|---|---|---|
| X11 only | `wmctrl`, `xprop` and Wnck's window control do not work on Wayland | Use an X11 session. Wayland is ROADMAP row 12 |
| Tested only with xfwm4 | Other window managers may treat `wmctrl -e` gravity or frame extents differently | Reports welcome; check DECISIONS D2's measurement on your window manager first |
| One monitor tested | Two-monitor placement is coded (window 1's monitor) but unverified | ROADMAP row 11 |
| HiDPI scaling untested | Gdk work areas are logical pixels, `wmctrl` takes device pixels; at scale 2 windows may land at half size [Unverified] | ROADMAP row 12. Leave display scaling at 1 for now |
| Terminals snap to character cells | A terminal ends up a few pixels short of its slot | Expected, not fixed on purpose (ROADMAP §5) |
| App minimum sizes | Many windows side by side can overlap when an app refuses to shrink | The tiler names the window in a notification. Use Grid, fewer windows, or Undo |
| A drawn shadow overlaps the neighbour | After the fix for drawn shadows, a browser's invisible shadow covers about 20px of the next slot. Not seen to misbehave so far | ROADMAP row 20 |
| Undo is one level | A second tile or reset replaces the snapshot | Undo before tiling again if you may want the old layout |
| Undo of a maximized window loses its pre-maximize size | After Undo it is maximized again, but un-maximizing it gives a near full-screen window | xfwm4 does not expose that size. ROADMAP row 13 |
| The tray blocks for up to about 1.3s while tiling | The pop-up is closed by then, but the icon does not respond during that time | Acceptable for now; would move to a worker if it ever shows |
| Super+T cannot fire while any tray menu is open | An open menu holds the keyboard grab | Close the menu first |
| `undo.json` contains window titles | Titles can hold email addresses or document names | It stays in your home folder and is deleted once used; never attach it to a bug report |
| Needs the XApp status icon plugin | Without `xapp-status-plugin` in the panel there is no icon to click | Linux Mint XFCE ships it. Elsewhere, Super+T should still open the pop-up [Unverified] |
