#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 PalWorks
"""Window tiler tray: tick windows in a pop-up, then pick a layout.

Left click the panel icon for the pop-up. Right click for Undo last tile
or reset, Settings and Quit. Super+T runs `tiler-tray.py --show`, which signals the
running tray to open the pop-up, or starts the tray if it is not running.

Nothing polls: the window list is read each time the pop-up opens.

Scaffolding lives in traykit.py. Must run under /usr/bin/python3.
"""

import os
import sys
import json
import signal
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # noqa: E402

from PIL import Image, ImageDraw  # noqa: E402

from traykit import TrayApp, HOME  # noqa: E402
import tiler_engine as engine  # noqa: E402
from tiler_picker import Picker  # noqa: E402

NAME = "tiler"
SHARE = os.path.join(HOME, ".local/share/tiler-tray")
SETTINGS = os.path.join(HOME, ".config/tiler-tray/settings.json")
ICON = os.path.join(SHARE, "tiles.png")
INK = "#e8e8e8"           # matches the other white panel icons
RULE = "#6a6a6a"          # the panel's own separator tone
GAPS = (0, 4, 8, 16)
DEFAULTS = {"gap": 0, "all_workspaces": False, "last_layout": "side"}


def draw_icon(path):
    """Three panes, one tall on the left and two stacked on the right.

    Same canvas as the network glyph: 96px tall at 4x panel height, with the
    divider rule drawn into the left padding because every status icon shares
    one panel plugin and no separator plugin can sit between them.
    """
    h = 96
    pad = 16
    w = h + pad
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def rgb(hx):
        return tuple(int(hx[i:i + 2], 16) for i in (1, 3, 5)) + (255,)

    d.rectangle([2, int(h * 0.18), 5, int(h * 0.82)], fill=rgb(RULE))
    ink = rgb(INK)
    stroke = 6
    bw, bh = 64, 52                     # light and small, reads like text
    x0 = pad + (h - bw) // 2
    y0 = (h - bh) // 2
    x1, y1 = x0 + bw, y0 + bh
    d.rounded_rectangle([x0, y0, x1, y1], radius=6, outline=ink, width=stroke)
    mid_x = x0 + int(bw * 0.55)
    d.rectangle([mid_x - stroke // 2, y0, mid_x + stroke // 2 - 1, y1], fill=ink)
    mid_y = y0 + bh // 2
    d.rectangle([mid_x, mid_y - stroke // 2, x1, mid_y + stroke // 2 - 1], fill=ink)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def load_settings():
    out = dict(DEFAULTS)
    try:
        with open(SETTINGS) as fh:
            out.update(json.load(fh))
    except (OSError, ValueError):
        pass
    return out


def save_settings(s):
    os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
    tmp = SETTINGS + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(s, fh, indent=2)
    os.replace(tmp, SETTINGS)


def notify(title, body):
    subprocess.Popen(["notify-send", "-a", "Tiler", "-i", ICON, title, body],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class TilerTray(TrayApp):
    name = NAME
    poll_seconds = 0                  # nothing to poll
    share_dir = SHARE
    initial_label = ""                # no panel text, the icon says it all
    show_refresh = False
    left_click_menu = False

    def __init__(self):
        self.settings = load_settings()
        self.picker = None
        self.anchor = None            # last menu point the panel gave us
        super().__init__()
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, self._on_show_signal)
        if os.environ.get("TILER_SHOW_ON_START"):
            GLib.timeout_add(600, lambda: (self.show_picker(), False)[1])

    # --- traykit hooks -------------------------------------------------------
    def fetch(self):
        return {}

    def badge_path(self, data):
        if not os.path.exists(ICON):
            draw_icon(ICON)
        return ICON

    def tooltip(self, data):
        return "Tile windows  |  Super+T"

    def primary_click(self, x, y, time):
        self.anchor = (x, y)
        if self.picker is not None:
            self.picker.destroy()     # a second click closes it
            return
        self.show_picker(time)

    def render(self, menu, data, error):
        menu.append(self.action_item("Tile windows…", self.show_picker))
        undo = self.action_item("Undo last tile or reset", self._undo)
        undo.set_sensitive(engine.load_undo() is not None)
        menu.append(undo)
        menu.append(Gtk.SeparatorMenuItem())

        gap_item = Gtk.MenuItem(label="Gap between windows")
        sub = Gtk.Menu()
        group = None
        for g in GAPS:
            item = Gtk.RadioMenuItem.new_with_label_from_widget(
                group, "None" if g == 0 else "%d px" % g)
            group = item
            item.set_active(self.settings["gap"] == g)
            item.connect("toggled", self._set_gap, g)
            sub.append(item)
        gap_item.set_submenu(sub)
        menu.append(gap_item)

        ws = Gtk.CheckMenuItem(label="List windows from all workspaces")
        ws.set_active(bool(self.settings["all_workspaces"]))
        ws.connect("toggled", self._set_all_workspaces)
        menu.append(ws)

    # --- actions -------------------------------------------------------------
    def show_picker(self, time=0):
        if self.picker is not None:
            self.picker.present()
            return
        self.picker = Picker(self._tile,
                             last_layout=self.settings["last_layout"],
                             all_workspaces=self.settings["all_workspaces"],
                             anchor=self.anchor, event_time=time,
                             on_reset=self._reset)
        self.picker.connect("destroy", self._picker_gone)

    def _picker_gone(self, _w):
        self.picker = None

    def _on_show_signal(self):
        self.show_picker()
        return True                   # keep the handler installed

    def _tile(self, xids, layout):
        try:
            res = engine.tile(xids, layout, gap=self.settings["gap"])
        except Exception as exc:                            # noqa: BLE001
            notify("Could not tile", "%s: %s" % (type(exc).__name__, exc))
            return
        self.settings["last_layout"] = layout
        save_settings(self.settings)
        if res["stuck"]:
            notify("Some windows would not shrink",
                   "%s has a minimum size, so it overlaps its neighbour. "
                   "Try Grid or fewer windows." % ", ".join(res["stuck"]))
        if res["gone"]:
            notify("Skipped closed windows",
                   "%d window(s) closed before tiling and were left out." % res["gone"])
        self._rebuild_soon()          # Undo is available now

    def _reset(self, xids):
        try:
            n = engine.reset(xids)
        except Exception as exc:                            # noqa: BLE001
            notify("Could not reset", "%s: %s" % (type(exc).__name__, exc))
            return
        notify("Reset %d windows" % n,
               "All maximized and minimized. Right click the tile icon, "
               "Undo last tile or reset, to bring them back.")
        self._rebuild_soon()          # Undo is available now

    def _undo(self):
        back = engine.undo()
        if not back:
            notify("Nothing to undo", "The windows from the last tile have all closed.")
        self._rebuild_soon()

    def _rebuild_soon(self):
        # Never rebuild from inside a menu item's activate handler. Swapping the
        # menu drops the last reference to the one still closing, GDK then
        # dispatches its pending events to a freed widget and the process
        # segfaults. Seen once on Undo, 2026-10-31. Wait for it to close.
        GLib.timeout_add(300, lambda: (self.rebuild(), False)[1])

    def _set_gap(self, item, g):
        if item.get_active() and self.settings["gap"] != g:
            self.settings["gap"] = g
            save_settings(self.settings)

    def _set_all_workspaces(self, item):
        self.settings["all_workspaces"] = item.get_active()
        save_settings(self.settings)


def signal_running():
    """Ask a running tray to open the pop-up. True if one answered."""
    lock = os.path.join(SHARE, "%s.lock" % NAME)
    try:
        with open(lock) as fh:
            pid = int(fh.read().strip() or 0)
        with open("/proc/%d/cmdline" % pid, "rb") as fh:
            if b"tiler-tray.py" not in fh.read():
                return False
        os.kill(pid, signal.SIGUSR1)
        return True
    except (OSError, ValueError):
        return False


if __name__ == "__main__":
    if "--show" in sys.argv[1:]:
        if signal_running():
            sys.exit(0)
        os.environ["TILER_SHOW_ON_START"] = "1"
    sys.exit(TilerTray.run())
