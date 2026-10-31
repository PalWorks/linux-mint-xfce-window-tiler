#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 PalWorks
"""traykit: the shared scaffolding behind the panel tray apps.

Subclass TrayApp, implement fetch/render/badge_path/label/tooltip, call run().
Everything awkward about XFCE status icons is handled here once:

  - XApp.StatusIcon, which Mint's xapp-status-plugin renders natively, with
    AyatanaAppIndicator3 as a fallback
  - the alternating icon filename, because setting the same path twice does not
    make the panel reload a changed file
  - a single instance flock, opened "a+" so a refused second launch cannot
    truncate the winner's pid
  - polling on a worker thread so the menu never blocks on IO

Must run under /usr/bin/python3, which is where the gi bindings live.
"""

import os
import sys
import fcntl
import shutil
import signal
import datetime
import subprocess
import threading

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # noqa: E402

HOME = os.path.expanduser("~")

GREEN = "#2ea043"
AMBER = "#db9a04"
RED = "#d1242f"
GREY = "#8a8a8a"
BLUE = "#3b82c4"


def esc(s):
    return GLib.markup_escape_text(str(s))


def human_eta(epoch):
    """Seconds until epoch, as 2d 4h / 3h 12m / 37m."""
    if not epoch:
        return "-"
    d = int(epoch - datetime.datetime.now().timestamp())
    if d <= 0:
        return "due"
    if d >= 86400:
        return "%dd %dh" % (d // 86400, (d % 86400) // 3600)
    if d >= 3600:
        return "%dh %dm" % (d // 3600, (d % 3600) // 60)
    return "%dm" % (d // 60)


def fmt_reset(epoch):
    """Absolute local time plus countdown: Sat 12 Sep 10:00 (4h 30m)."""
    if not epoch:
        return "-"
    stamp = datetime.datetime.fromtimestamp(epoch).strftime("%a %d %b %H:%M")
    return "%s (%s)" % (stamp, human_eta(epoch))


def fmt_bytes(b):
    """Bytes to a fixed width GiB/MiB/KiB string."""
    if b is None:
        return "n/a"
    b = float(b)
    if b >= 1024 ** 3:
        return "%.2f GiB" % (b / 1024 ** 3)
    if b >= 1024 ** 2:
        return "%.2f MiB" % (b / 1024 ** 2)
    if b >= 1024:
        return "%.2f KiB" % (b / 1024)
    return "%d B" % b


class TrayApp:
    """Base class. Subclasses override the five hooks below."""

    name = "traykit"                  # lock file and status icon name
    poll_seconds = 300                # 0 = no timer, fetch once at start
    share_dir = os.path.join(HOME, ".local/share/traykit")
    fallback_icon = "utilities-system-monitor"
    initial_label = " ..."           # see _build_icon, must be set at registration
    show_refresh = True               # add "Refresh now" to the menu
    left_click_menu = True            # False: left click calls primary_click()

    # --- hooks ---------------------------------------------------------------
    def fetch(self):
        """Runs on a worker thread. Return any object, or raise."""
        raise NotImplementedError

    def render(self, menu, data, error):
        """Append Gtk items for `data` to `menu`. Runs on the main loop."""
        raise NotImplementedError

    def badge_path(self, data):
        """Absolute path to the icon PNG, or None to keep the fallback."""
        return None

    def label(self, data):
        """Panel label text shown next to the icon, or None."""
        return None

    def tooltip(self, data):
        """Hover tooltip text, or None."""
        return None

    def primary_click(self, x, y, time):
        """Left click when left_click_menu is False. x, y are where the panel
        would put a menu, time is the X event time. XApp backend only."""

    # --- lifecycle -----------------------------------------------------------
    def __init__(self):
        self.data = None
        self.error = None
        self.last_poll = None
        self.polling = False
        self._badge_slot = 0
        self.icon = None
        self.backend = None
        os.makedirs(self.share_dir, exist_ok=True)
        self._build_icon()
        self.refresh()
        if self.poll_seconds > 0:
            GLib.timeout_add_seconds(self.poll_seconds, self._tick)

    def _build_icon(self):
        try:
            gi.require_version("XApp", "1.0")
            from gi.repository import XApp
            self.icon = XApp.StatusIcon()
            self.icon.set_name(self.name)
            self.icon.set_icon_name(self.fallback_icon)
            # The panel allocates the text area when the icon first registers.
            # An icon that registers without a label never grows one, and every
            # later set_label is accepted by the API but never drawn.
            self.icon.set_label(self.initial_label)
            if not self.left_click_menu:
                self.icon.connect("button-press-event", self._on_button_press)
            self.backend = "xapp"
        except Exception:                                   # noqa: BLE001
            gi.require_version("AyatanaAppIndicator3", "0.1")
            from gi.repository import AyatanaAppIndicator3 as AI
            self.icon = AI.Indicator.new(self.name, self.fallback_icon,
                                         AI.IndicatorCategory.SYSTEM_SERVICES)
            self.icon.set_status(AI.IndicatorStatus.ACTIVE)
            self.backend = "ayatana"

    def _set_icon_path(self, path):
        if not path or not os.path.exists(path):
            return
        self._badge_slot ^= 1
        slot = os.path.join(self.share_dir, "%s-icon-%d.png" % (self.name, self._badge_slot))
        try:
            shutil.copyfile(path, slot)
        except OSError:
            return
        if self.backend == "xapp":
            self.icon.set_icon_name(slot)
        else:
            self.icon.set_icon_full(slot, self.name)

    def _set_label(self, text):
        if text is None:
            return
        if self.backend == "xapp":
            self.icon.set_label(text)
        else:
            self.icon.set_label(text, text)

    def _set_tooltip(self, text):
        if text is None:
            return                      # "" is meaningful: it clears the tooltip
        try:
            self.icon.set_tooltip_text(text)
        except Exception:                                   # noqa: BLE001
            pass

    def _on_button_press(self, _icon, x, y, button, time, _panel_position):
        if button == 1:
            self.primary_click(x, y, time)

    def _set_menu(self, menu):
        if self.backend == "xapp":
            # no primary menu means the panel hands left clicks to us instead
            self.icon.set_primary_menu(menu if self.left_click_menu else None)
            self.icon.set_secondary_menu(menu)
        else:
            self.icon.set_menu(menu)

    # --- polling -------------------------------------------------------------
    def _worker(self, force):
        data, error = None, None
        try:
            data = self.fetch_forced(force) if force else self.fetch()
        except Exception as exc:                            # noqa: BLE001
            error = "%s: %s" % (type(exc).__name__, exc)
        GLib.idle_add(self._apply, data, error)

    def fetch_forced(self, force):
        """Override if a forced refresh differs from a scheduled one."""
        return self.fetch()

    def _apply(self, data, error):
        self.polling = False
        if data is not None:
            self.data = data
            self.last_poll = datetime.datetime.now()
        self.error = error
        self.rebuild()
        return False

    def refresh(self, force=False):
        if self.polling:
            return
        self.polling = True
        threading.Thread(target=self._worker, args=(force,), daemon=True).start()

    def _tick(self):
        self.refresh()
        return True

    # --- menu ----------------------------------------------------------------
    def label_item(self, markup, sensitive=False):
        item = Gtk.MenuItem()
        lbl = Gtk.Label(xalign=0)
        lbl.set_markup(markup)
        item.add(lbl)
        item.set_sensitive(sensitive)
        return item

    def action_item(self, text, callback):
        item = Gtk.MenuItem(label=text)
        item.connect("activate", lambda _w: callback())
        return item

    def header_item(self, title):
        stamp = self.last_poll.strftime("%H:%M:%S") if self.last_poll else "never"
        return self.label_item(
            "<b>%s</b>  <span size='small' foreground='%s'>as of %s</span>"
            % (esc(title), GREY, stamp))

    def _menu_shown(self, _menu):
        # Drop the tooltip while the dropdown is open. A menu takes a pointer
        # grab, and any tooltip already on screen when that happens is left
        # stranded until the pointer crosses the icon again.
        self._set_tooltip("")

    def _menu_hidden(self, _menu):
        self._set_tooltip(self.tooltip(self.data) or "")

    def rebuild(self):
        menu = Gtk.Menu()
        menu.connect("show", self._menu_shown)
        menu.connect("hide", self._menu_hidden)
        self.render(menu, self.data, self.error)
        menu.append(Gtk.SeparatorMenuItem())
        extras = self.extra_actions()
        if self.show_refresh:
            menu.append(self.action_item("Refresh now", lambda: self.refresh(force=True)))
        for text, cb in extras:
            menu.append(self.action_item(text, cb))
        if self.show_refresh or extras:
            menu.append(Gtk.SeparatorMenuItem())
        menu.append(self.action_item("Quit", Gtk.main_quit))
        menu.show_all()
        self._set_menu(menu)
        self._set_icon_path(self.badge_path(self.data))
        self._set_tooltip(self.tooltip(self.data))
        # Re-apply the label on the next main loop pass. Changing the icon name
        # re-registers the status icon asynchronously, which drops a label set
        # in the same pass, so setting it inline here silently does nothing.
        text = self.label(self.data)
        if text is not None:
            GLib.idle_add(self._set_label, text)

    def extra_actions(self):
        """List of (label, callback) added after Refresh now."""
        return []

    # --- helpers -------------------------------------------------------------
    def spawn(self, argv):
        try:
            subprocess.Popen(argv, start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as exc:                            # noqa: BLE001
            print("spawn failed: %s" % exc, file=sys.stderr)

    def clip(self, text):
        try:
            from gi.repository import Gdk
            cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            cb.set_text(text, -1)
            cb.store()
        except Exception as exc:                            # noqa: BLE001
            print("clipboard failed: %s" % exc, file=sys.stderr)

    # --- entry point ---------------------------------------------------------
    def _single_instance(self):
        path = os.path.join(self.share_dir, "%s.lock" % self.name)
        fh = open(path, "a+")      # never "w": a refused second instance would
        try:                       # truncate the winner's pid before failing
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("%s is already running" % self.name, file=sys.stderr)
            sys.exit(0)
        fh.seek(0)
        fh.truncate()
        fh.write(str(os.getpid()))
        fh.flush()
        return fh                  # kept open deliberately, closing frees it

    @classmethod
    def run(cls):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        os.makedirs(cls.share_dir, exist_ok=True)
        self = cls.__new__(cls)
        self._lock = cls._single_instance(self)             # noqa: SLF001
        cls.__init__(self)
        Gtk.main()
        return 0
