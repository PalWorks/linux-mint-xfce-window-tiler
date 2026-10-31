#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 PalWorks
"""tiler_engine: layout maths and window moves behind the tiler tray.

Two halves:

  - rects(): pure maths, window count plus screen area to rectangles. No X,
    no Gtk, unit tested on its own.
  - list_windows() / tile() / undo(): talk to the window manager. Windows are
    read through Wnck, but moved with wmctrl, because under xfwm4
    Wnck.Window.set_geometry lands every window offset by its own frame
    extents with either gravity. wmctrl -e with gravity 0 takes the frame's
    top left plus the client size, and lands to the pixel. See DECISIONS.md.

Also runs on its own for testing:

  tiler_engine.py --list
  tiler_engine.py --layout side 0x4400003 0x4600003
  tiler_engine.py --reset 0x4400003 0x4600003
  tiler_engine.py --undo

Must run under /usr/bin/python3, which is where the gi bindings live.
"""

import os
import sys
import json
import math
import re
import time
import subprocess

HOME = os.path.expanduser("~")
UNDO_FILE = os.path.join(HOME, ".local/share/tiler-tray/undo.json")

LAYOUTS = ("side", "stacked", "grid", "main")
LAYOUT_NAMES = {
    "side": "Side by side",
    "stacked": "Stacked",
    "grid": "Grid",
    "main": "Main + side",
}
MAIN_SHARE = 0.6          # window 1's share of the width in "main"
SHRINK_SLACK = 2          # px a window may overshoot its slot before we call it stuck


# --- maths -------------------------------------------------------------------
def split(start, length, k, gap):
    """Cut `length` into k runs with `gap` between and around them.

    Returns [(offset, size)]. Leftover pixels go to the first runs, so the
    pieces always add up to exactly the space available.
    """
    usable = length - gap * (k + 1)
    base, extra = divmod(usable, k)
    out, pos = [], start + gap
    for i in range(k):
        size = base + (1 if i < extra else 0)
        out.append((pos, size))
        pos += size + gap
    return out


def grid_shape(n):
    """Columns and rows for n windows: at least as wide as tall, landscape first."""
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    return cols, rows


def available(layout, n):
    """Whether a layout means something for n windows."""
    if n < 2:
        return False
    if layout == "grid":
        return n >= 3     # two windows in a grid is just side by side
    return layout in LAYOUTS


def rects(layout, n, area, gap=0):
    """Target frame rectangles (x, y, w, h) for n windows, in placement order.

    `area` is (x, y, w, h), normally the monitor's work area, which already
    excludes the panel.
    """
    ax, ay, aw, ah = area
    if n <= 0:
        return []
    if n == 1:
        return [(ax + gap, ay + gap, aw - 2 * gap, ah - 2 * gap)]
    if layout == "side":
        ys = split(ay, ah, 1, gap)[0]
        return [(x, ys[0], w, ys[1]) for x, w in split(ax, aw, n, gap)]
    if layout == "stacked":
        xs = split(ax, aw, 1, gap)[0]
        return [(xs[0], y, xs[1], h) for y, h in split(ay, ah, n, gap)]
    if layout == "grid":
        cols, rows = grid_shape(n)
        out = []
        row_spans = split(ay, ah, rows, gap)
        left = n
        for y, h in row_spans:
            # the last row takes whatever is left and stretches across
            in_row = min(cols, left)
            for x, w in split(ax, aw, in_row, gap):
                out.append((x, y, w, h))
            left -= in_row
        return out
    if layout == "main":
        inner = aw - 3 * gap
        main_w = int(round(inner * MAIN_SHARE))
        side_x = ax + 2 * gap + main_w
        side_w = inner - main_w
        y0, h0 = split(ay, ah, 1, gap)[0]
        out = [(ax + gap, y0, main_w, h0)]
        for y, h in split(ay, ah, n - 1, gap):
            out.append((side_x, y, side_w, h))
        return out
    raise ValueError("unknown layout %r" % layout)


# --- window manager ----------------------------------------------------------
def _gi():
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    gi.require_version("Wnck", "3.0")
    from gi.repository import Gtk, Gdk, Wnck
    return Gtk, Gdk, Wnck


def pump(seconds=0.0):
    """Let Wnck catch up with the window manager for up to `seconds`."""
    Gtk, _Gdk, _Wnck = _gi()
    end = time.time() + seconds
    while True:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        if time.time() >= end:
            return
        time.sleep(0.01)


def screen():
    _Gtk, _Gdk, Wnck = _gi()
    scr = Wnck.Screen.get_default()
    scr.force_update()
    return scr


def wmctrl(*args):
    subprocess.run(["wmctrl"] + list(args), stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=5)


def _xid(w):
    return "0x%08x" % w.get_xid()


def _extents(w):
    """Frame extents (left, top, right, bottom) worked out from Wnck's two
    geometries. Differs between maximized and normal states, so only trust it
    once the window has settled."""
    fx, fy, fw, fh = w.get_geometry()
    cx, cy, cw, ch = w.get_client_window_geometry()
    return (cx - fx, cy - fy, (fx + fw) - (cx + cw), (fy + fh) - (cy + ch))


def _csd_extents(xid):
    """The invisible shadow a client-side decorated window draws inside its
    own X window, as (left, right, top, bottom); zeros when there is none.

    Chromium browsers (Chrome, Edge) and GTK header bar apps do this and
    advertise it in _GTK_FRAME_EXTENTS. xfwm4 ignores it, so a window placed
    by its X geometry shows up that much smaller than its slot. Edge measured
    22, 22, 19, 25 on 2026-10-31.
    """
    try:
        out = subprocess.run(["xprop", "-id", "0x%08x" % xid, "_GTK_FRAME_EXTENTS"],
                             capture_output=True, text=True, timeout=2).stdout
    except (OSError, subprocess.SubprocessError):
        return (0, 0, 0, 0)
    m = re.search(r"=\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)", out)
    return tuple(int(v) for v in m.groups()) if m else (0, 0, 0, 0)


def _grow(rect, csd):
    """Enlarge a slot by a window's shadow, so its visible part fills the slot."""
    x, y, w, h = rect
    left, right, top, bottom = csd
    return (x - left, y - top, w + left + right, h + top + bottom)


def list_windows(all_workspaces=False, exclude_xids=()):
    """Normal windows, most recently stacked first.

    Each entry: xid, title, app, minimized, workspace number (None when the
    window is on every workspace), and the Wnck window for callers that want
    its icon.
    """
    _Gtk, _Gdk, Wnck = _gi()
    scr = screen()
    pump()
    active = scr.get_active_workspace()
    out = []
    for w in reversed(scr.get_windows_stacked() or []):
        if w.get_window_type() != Wnck.WindowType.NORMAL:
            continue
        if w.is_skip_tasklist() or w.get_xid() in exclude_xids:
            continue
        ws = w.get_workspace()
        if not all_workspaces and ws is not None and active is not None \
                and ws.get_number() != active.get_number():
            continue
        app = w.get_application()
        out.append({
            "xid": w.get_xid(),
            "title": w.get_name() or "",
            "app": (w.get_class_group_name() or (app.get_name() if app else "") or ""),
            "minimized": w.is_minimized(),
            "workspace": ws.get_number() if ws else None,
            "window": w,
        })
    return out


def _by_xid(scr, xids):
    found = {w.get_xid(): w for w in (scr.get_windows() or [])}
    return [found.get(x) for x in xids]


def monitor_area(window=None):
    """Work area of the monitor holding the centre of `window`, else the
    monitor under the pointer."""
    _Gtk, Gdk, _Wnck = _gi()
    disp = Gdk.Display.get_default()
    mon = None
    if window is not None:
        x, y, w, h = window.get_geometry()
        mon = disp.get_monitor_at_point(x + w // 2, y + h // 2)
    if mon is None:
        seat = disp.get_default_seat()
        _s, px, py = seat.get_pointer().get_position()
        mon = disp.get_monitor_at_point(px, py)
    wa = mon.get_workarea()
    return (wa.x, wa.y, wa.width, wa.height)


def snapshot(windows):
    """Everything undo needs to put each window back."""
    out = []
    for w in windows:
        fx, fy, _fw, _fh = w.get_geometry()
        _cx, _cy, cw, ch = w.get_client_window_geometry()
        ws = w.get_workspace()
        out.append({
            "xid": w.get_xid(),
            "title": w.get_name() or "",
            "frame_xy": [fx, fy],
            "client_wh": [cw, ch],
            "max_h": w.is_maximized_horizontally(),
            "max_v": w.is_maximized_vertically(),
            "minimized": w.is_minimized(),
            "fullscreen": w.is_fullscreen(),
            "workspace": ws.get_number() if ws else None,
        })
    return out


def _save_undo(snap):
    os.makedirs(os.path.dirname(UNDO_FILE), exist_ok=True)
    tmp = UNDO_FILE + ".tmp"
    with open(tmp, "w") as fh:
        json.dump({"saved": time.time(), "windows": snap}, fh)
    os.replace(tmp, UNDO_FILE)


def load_undo():
    try:
        with open(UNDO_FILE) as fh:
            return json.load(fh).get("windows") or None
    except (OSError, ValueError):
        return None


def _settle(windows, test, timeout=0.5):
    """Wait until test(w) holds for every window, or the timeout passes.
    xfwm4 applies state changes asynchronously, and a move sent before an
    unmaximize has landed gets overridden."""
    end = time.time() + timeout
    while time.time() < end:
        pump()
        if all(test(w) for w in windows):
            return True
        time.sleep(0.015)
    return False


def _place(xid, frame_x, frame_y, client_w, client_h):
    # gravity 0 = the window's own, NorthWest for every window seen here:
    # x, y place the frame's top left, w, h size the client
    wmctrl("-i", "-r", "0x%08x" % xid, "-e",
           "0,%d,%d,%d,%d" % (frame_x, frame_y, max(client_w, 1), max(client_h, 1)))


def tile(xids, layout, gap=0, workspace=None):
    """Tile the windows in `xids`, in that order, using `layout`.

    Returns {"tiled": [title], "stuck": [title], "gone": int}. `stuck` lists
    windows that would not shrink to their slot, usually an app minimum size.
    The pre-tile state is saved for undo() before anything moves.
    """
    scr = screen()
    pump()
    found = _by_xid(scr, xids)
    wins = [w for w in found if w is not None]
    gone = len(found) - len(wins)
    if len(wins) < 2:
        return {"tiled": [], "stuck": [], "gone": gone}

    _save_undo(snapshot(wins))

    active = scr.get_active_workspace()
    if workspace is None and active is not None:
        workspace = active.get_number()

    for w in wins:
        x = _xid(w)
        if w.is_fullscreen():
            wmctrl("-i", "-r", x, "-b", "remove,fullscreen")
        if w.is_maximized_horizontally() or w.is_maximized_vertically():
            wmctrl("-i", "-r", x, "-b", "remove,maximized_vert,maximized_horz")
        ws = w.get_workspace()
        if workspace is not None and ws is not None and ws.get_number() != workspace:
            wmctrl("-i", "-r", x, "-t", str(workspace))
        if w.is_minimized():
            w.unminimize(int(time.time()))
    _settle(wins, lambda w: not (w.is_maximized_horizontally() or w.is_maximized_vertically()
                                 or w.is_minimized() or w.is_fullscreen()))

    area = monitor_area(wins[0])
    targets = rects(layout, len(wins), area, gap)

    def place_all():
        placed = []
        for w, t in zip(wins, targets):
            x, y, tw, th = _grow(t, _csd_extents(w.get_xid()))
            left, top, right, bottom = _extents(w)
            _place(w.get_xid(), x, y, tw - left - right, th - top - bottom)
            placed.append((x, y, tw, th))
        return placed

    def landed(w, t):
        fx, fy, _fw, _fh = w.get_geometry()
        return abs(fx - t[0]) <= SHRINK_SLACK and abs(fy - t[1]) <= SHRINK_SLACK

    before = [_csd_extents(w.get_xid()) for w in wins]
    placed = place_all()
    # raise in reverse so window 1 ends up on top with the focus
    for w in reversed(wins):
        wmctrl("-i", "-a", _xid(w))
    _settle(wins, lambda w: landed(w, placed[wins.index(w)]), timeout=0.4)
    # Chromium only draws its shadow once it is no longer maximized, and says so
    # a moment later; place again if any shadow appeared or changed meanwhile
    if [_csd_extents(w.get_xid()) for w in wins] != before:
        placed = place_all()
        _settle(wins, lambda w: landed(w, placed[wins.index(w)]), timeout=0.4)

    stuck = []
    for w, (x, y, tw, th) in zip(wins, placed):
        _fx, _fy, fw, fh = w.get_geometry()
        # terminals snap down to whole character cells, which is fine; a frame
        # bigger than its slot means the app refused to shrink
        if fw > tw + SHRINK_SLACK or fh > th + SHRINK_SLACK:
            stuck.append(w.get_name() or _xid(w))
    return {"tiled": [w.get_name() or "" for w in wins], "stuck": stuck, "gone": gone}


def reset(xids):
    """Maximize every window in `xids`, then minimize them all: a clean desk.

    Saved for undo() first, like a tile. Returns how many were reset.
    """
    scr = screen()
    pump()
    wins = [w for w in _by_xid(scr, xids) if w is not None]
    if not wins:
        return 0
    _save_undo(snapshot(wins))
    for w in wins:
        x = _xid(w)
        if w.is_fullscreen():
            wmctrl("-i", "-r", x, "-b", "remove,fullscreen")
        wmctrl("-i", "-r", x, "-b", "add,maximized_vert,maximized_horz")
    _settle(wins, lambda w: w.is_maximized_horizontally() and w.is_maximized_vertically())
    for w in wins:
        if not w.is_minimized():
            w.minimize()
    pump(0.05)
    return len(wins)


def undo():
    """Put the windows from the last tile or reset back. Returns how many came back."""
    snap = load_undo()
    if not snap:
        return 0
    scr = screen()
    pump()
    found = _by_xid(scr, [s["xid"] for s in snap])
    back = 0
    live = [w for w in found if w is not None]
    for s, w in zip(snap, found):
        if w is None:
            continue
        x = _xid(w)
        # clear whatever the tile or reset left behind, or the move is ignored
        if w.is_fullscreen():
            wmctrl("-i", "-r", x, "-b", "remove,fullscreen")
        if w.is_maximized_horizontally() or w.is_maximized_vertically():
            wmctrl("-i", "-r", x, "-b", "remove,maximized_vert,maximized_horz")
        if w.is_minimized() and not s["minimized"]:
            w.unminimize(int(time.time()))
        if s["workspace"] is not None:
            wmctrl("-i", "-r", x, "-t", str(s["workspace"]))
    _settle(live, lambda w: not (w.is_maximized_horizontally() or w.is_maximized_vertically()
                                 or w.is_fullscreen()))
    for s, w in zip(snap, found):
        if w is None:
            continue
        _place(s["xid"], s["frame_xy"][0], s["frame_xy"][1],
               s["client_wh"][0], s["client_wh"][1])
        back += 1
    pump(0.15)
    for s, w in zip(snap, found):
        if w is None:
            continue
        x = _xid(w)
        if s["max_h"] or s["max_v"]:
            props = ",".join(p for p, on in (("maximized_horz", s["max_h"]),
                                             ("maximized_vert", s["max_v"])) if on)
            wmctrl("-i", "-r", x, "-b", "add," + props)
        if s["fullscreen"]:
            wmctrl("-i", "-r", x, "-b", "add,fullscreen")
        if s["minimized"]:
            w.minimize()
    pump(0.05)
    try:
        os.remove(UNDO_FILE)
    except OSError:
        pass
    return back


# --- command line ------------------------------------------------------------
def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    if argv[0] == "--list":
        for w in list_windows(all_workspaces="--all" in argv):
            print("0x%08x  %-20s  %s%s" % (w["xid"], w["app"][:20], w["title"][:70],
                                           "  (minimized)" if w["minimized"] else ""))
        return 0
    if argv[0] == "--reset" and len(argv) >= 2:
        print("reset %d window(s)" % reset([int(a, 16) for a in argv[1:]]))
        return 0
    if argv[0] == "--undo":
        print("restored %d window(s)" % undo())
        return 0
    if argv[0] == "--layout" and len(argv) >= 4:
        layout = argv[1]
        if layout not in LAYOUTS:
            print("layout must be one of %s" % ", ".join(LAYOUTS), file=sys.stderr)
            return 2
        gap = 0
        ids = []
        for a in argv[2:]:
            if a.startswith("--gap="):
                gap = int(a.split("=", 1)[1])
            else:
                ids.append(int(a, 16))
        print(json.dumps(tile(ids, layout, gap)))
        return 0
    print("usage: --list [--all] | --layout <side|stacked|grid|main> [--gap=N] <xid> <xid>... | --reset <xid>... | --undo",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
