#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 PalWorks
"""tiler_picker: the pop-up that lists windows and offers the layouts.

One window, two parts. The list on top: tick windows in the order you want
them placed, each tick shows its position number. The layout bar underneath
only appears once two or more are ticked, so the first thing on screen is the
one thing to do.

Keys: Up/Down move, Space ticks, 1-9 tick row n, Enter applies the last
layout used, Esc closes.
"""

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkX11", "3.0")
from gi.repository import Gtk, Gdk, GdkX11, GLib, Pango  # noqa: E402

import tiler_engine as engine  # noqa: E402

WIDTH = 360
SEARCH_FROM = 9           # show the search box once there are this many windows
PICTO_W, PICTO_H = 56, 34

CSS = b"""
#tiler-picker { border: 1px solid alpha(@theme_fg_color, 0.18); }
#tiler-picker .tiler-title { font-weight: bold; }
#tiler-picker .tiler-dim { opacity: 0.55; }
#tiler-picker .tiler-hint { opacity: 0.7; font-size: smaller; }
#tiler-picker list row { min-height: 40px; }
#tiler-picker .tiler-badge {
    min-width: 22px; min-height: 22px; border-radius: 11px;
    font-weight: bold; font-size: smaller;
}
#tiler-picker .tiler-badge.on {
    background: @theme_selected_bg_color; color: @theme_selected_fg_color;
}
#tiler-picker .tiler-layout { padding: 6px 4px; min-height: 40px; }
#tiler-picker .tiler-icon-btn { min-width: 40px; min-height: 40px; padding: 0; }
"""


def _install_css():
    if getattr(_install_css, "done", False):
        return
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    _install_css.done = True


class Picker(Gtk.Window):
    """`on_tile(xids, layout)` and `on_reset(xids)` are called after the
    pop-up has closed."""

    def __init__(self, on_tile, last_layout="side", all_workspaces=False,
                 anchor=None, event_time=0, on_reset=None):
        super().__init__(type=Gtk.WindowType.TOPLEVEL, title="Tile windows")
        _install_css()
        self.set_name("tiler-picker")
        self.on_tile = on_tile
        self.on_reset = on_reset          # on_reset(xids): every listed window
        self.last_layout = last_layout if last_layout in engine.LAYOUTS else "side"
        self.order = []                   # xids in tick order
        self.rows = []                    # (row, xid, check, badge)
        self._closing = False

        self.set_decorated(False)
        self.set_resizable(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_size_request(WIDTH, -1)

        self.windows = engine.list_windows(all_workspaces=all_workspaces)
        self._build()
        self.connect("key-press-event", self._on_key)
        self.connect("focus-out-event", self._on_focus_out)

        # Settle visibility, size and position before the window maps. Mapping
        # first (show_all on the window) drew it once at full height in the
        # wrong place, then shrank and moved it: a visible flash on every click.
        self.get_child().show_all()
        self._refresh_state()
        self._place(anchor)
        self.realize()
        self.present_with_time(event_time or self._server_time())
        if self.rows:
            self.rows[0][0].grab_focus()

    # --- construction --------------------------------------------------------
    def _build(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        outer.set_border_width(12)
        self.add(outer)

        head = Gtk.Box(spacing=8)
        title = Gtk.Label(label="Tile windows", xalign=0)
        title.get_style_context().add_class("tiler-title")
        head.pack_start(title, True, True, 0)
        # icon only, as the owner asked; the tooltip carries the name and what it does
        self.btn_reset = self._icon_button(
            "view-refresh-symbolic", "Reset all",
            "Maximize every listed window, then minimize them all.\n"
            "Undo from the tray icon's right-click menu.", self._reset)
        self.btn_reset.set_sensitive(bool(self.windows) and self.on_reset is not None)
        self.btn_all = self._icon_button(
            "edit-select-all-symbolic", "Select all",
            "Tick every window in the list, top to bottom.", self._select_all)
        self.btn_clear = self._icon_button(
            "edit-clear-all-symbolic", "Clear",
            "Untick every window.", self._clear)
        # whole-desk Reset sits apart from the per-tick pair
        head.pack_end(self.btn_reset, False, False, 0)
        head.pack_end(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 2)
        head.pack_end(self.btn_clear, False, False, 0)
        head.pack_end(self.btn_all, False, False, 0)
        outer.pack_start(head, False, False, 0)

        hint = Gtk.Label(label="Tick windows in the order you want them placed",
                         xalign=0)
        hint.get_style_context().add_class("tiler-hint")
        outer.pack_start(hint, False, False, 0)

        self.search = None
        if len(self.windows) >= SEARCH_FROM:
            self.search = Gtk.SearchEntry(placeholder_text="Filter windows")
            self.search.connect("search-changed", lambda _e: self.listbox.invalidate_filter())
            outer.pack_start(self.search, False, False, 0)

        self.listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.listbox.set_activate_on_single_click(True)
        self.listbox.connect("row-activated", self._on_row_activated)
        self.listbox.set_filter_func(self._filter)
        for w in self.windows:
            self.listbox.add(self._row(w))

        if not self.windows:
            empty = Gtk.Label(label="No windows open on this workspace.\n"
                                    "Open two or more, then click the tile icon again.",
                              justify=Gtk.Justification.CENTER)
            empty.get_style_context().add_class("tiler-hint")
            empty.set_margin_top(16)
            empty.set_margin_bottom(16)
            outer.pack_start(empty, False, False, 0)
        else:
            scroller = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
            scroller.set_propagate_natural_height(True)
            scroller.set_max_content_height(self._max_list_height())
            scroller.add(self.listbox)
            outer.pack_start(scroller, True, True, 0)

        outer.pack_start(Gtk.Separator(), False, False, 0)

        self.nudge = Gtk.Label(label="Tick 2 or more windows to see layouts", xalign=0.5)
        self.nudge.get_style_context().add_class("tiler-hint")
        outer.pack_start(self.nudge, False, False, 0)

        self.layout_bar = Gtk.Box(spacing=6, homogeneous=True)
        self.layout_buttons = {}
        for name in engine.LAYOUTS:
            btn = Gtk.Button()
            btn.get_style_context().add_class("tiler-layout")
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            area = Gtk.DrawingArea()
            area.set_size_request(PICTO_W, PICTO_H)
            area.connect("draw", self._draw_picto, name)
            box.pack_start(area, False, False, 0)
            lbl = Gtk.Label(label=engine.LAYOUT_NAMES[name])
            lbl.set_line_wrap(True)
            lbl.set_justify(Gtk.Justification.CENTER)
            box.pack_start(lbl, False, False, 0)
            btn.add(box)
            btn.set_tooltip_text("%s (Enter)" % engine.LAYOUT_NAMES[name]
                                 if name == self.last_layout else engine.LAYOUT_NAMES[name])
            btn.connect("clicked", lambda _b, n=name: self._apply(n))
            if name == self.last_layout:
                btn.get_style_context().add_class("suggested-action")
            self.layout_buttons[name] = (btn, area)
            self.layout_bar.pack_start(btn, True, True, 0)
        outer.pack_start(self.layout_bar, False, False, 0)

        self.enter_hint = Gtk.Label(xalign=0.5)
        self.enter_hint.get_style_context().add_class("tiler-hint")
        outer.pack_start(self.enter_hint, False, False, 0)

    def _icon_button(self, icon, title, subtitle, callback):
        btn = Gtk.Button(relief=Gtk.ReliefStyle.NONE)
        btn.set_image(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON))
        btn.get_style_context().add_class("tiler-icon-btn")
        btn.set_tooltip_markup("<b>%s</b>\n%s" % (GLib.markup_escape_text(title),
                                                  GLib.markup_escape_text(subtitle)))
        btn.get_accessible().set_name(title)      # screen readers still get a name
        btn.connect("clicked", lambda _b: callback())
        return btn

    def _row(self, w):
        row = Gtk.ListBoxRow()
        box = Gtk.Box(spacing=6)
        box.set_border_width(4)
        check = Gtk.CheckButton()
        check.set_can_focus(False)        # the row takes focus, Space ticks it
        box.pack_start(check, False, False, 0)

        # the position number sits at the far right, so an unticked row has no
        # empty slot between the checkbox and the app icon
        badge = Gtk.Label(label="")
        badge.set_valign(Gtk.Align.CENTER)    # keep it a circle, not row height
        badge.get_style_context().add_class("tiler-badge")
        box.pack_end(badge, False, False, 0)

        pix = w["window"].get_mini_icon()
        if pix is not None:
            box.pack_start(Gtk.Image.new_from_pixbuf(pix), False, False, 0)

        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title = Gtk.Label(label=w["title"] or "(untitled)", xalign=0)
        title.set_ellipsize(Pango.EllipsizeMode.END)
        title.set_max_width_chars(34)
        sub = Gtk.Label(xalign=0)
        bits = [w["app"]] if w["app"] else []
        if w["minimized"]:
            bits.append("minimized")
        sub.set_text("  ·  ".join(bits))
        sub.get_style_context().add_class("tiler-hint")
        text.pack_start(title, False, False, 0)
        text.pack_start(sub, False, False, 0)
        box.pack_start(text, True, True, 0)
        if w["minimized"]:
            title.get_style_context().add_class("tiler-dim")

        row.add(box)
        row.set_tooltip_text(w["title"])
        xid = w["xid"]
        check.connect("toggled", self._on_toggled, xid)
        self.rows.append((row, xid, check, badge))
        row._tiler_text = ("%s %s" % (w["title"], w["app"])).lower()
        return row

    def _max_list_height(self):
        try:
            area = engine.monitor_area()
            return int(area[3] * 0.6)
        except Exception:                                   # noqa: BLE001
            return 600

    # --- behaviour -----------------------------------------------------------
    def _filter(self, row):
        if not self.search:
            return True
        q = self.search.get_text().strip().lower()
        return not q or q in row._tiler_text

    def _visible_rows(self):
        return [r for r in self.rows if r[0].get_child_visible() and r[0].get_mapped()]

    def _on_row_activated(self, _lb, row):
        for r, _x, check, _b in self.rows:
            if r is row:
                check.set_active(not check.get_active())
                return

    def _on_toggled(self, check, xid):
        if check.get_active():
            if xid not in self.order:
                self.order.append(xid)
        elif xid in self.order:
            self.order.remove(xid)
        self._refresh_state()

    def _select_all(self):
        for _r, _x, check, _b in self._visible_rows():
            check.set_active(True)

    def _clear(self):
        for _r, _x, check, _b in self.rows:
            check.set_active(False)

    def _refresh_state(self):
        n = len(self.order)
        for _r, xid, _c, badge in self.rows:
            ctx = badge.get_style_context()
            if xid in self.order:
                badge.set_text(str(self.order.index(xid) + 1))
                ctx.add_class("on")
            else:
                badge.set_text("")
                ctx.remove_class("on")
        ready = n >= 2
        self.nudge.set_visible(not ready and bool(self.rows))
        self.layout_bar.set_visible(ready)
        self.enter_hint.set_visible(ready)
        self.btn_clear.set_sensitive(n > 0)
        self.btn_all.set_sensitive(len(self.rows) > n)
        if ready:
            for name, (btn, area) in self.layout_buttons.items():
                btn.set_visible(engine.available(name, n))
                area.queue_draw()
            last = self.last_layout if engine.available(self.last_layout, n) else "side"
            self.enter_hint.set_text("Enter: %s, %d windows" % (engine.LAYOUT_NAMES[last], n))
        self.resize(WIDTH, 1)             # shrink back when the bar hides

    def _draw_picto(self, area, cr, name):
        n = max(len(self.order), 2)
        alloc = area.get_allocation()
        w, h = alloc.width, alloc.height
        ox = (w - PICTO_W) / 2
        ctx = area.get_style_context()
        fg = ctx.get_color(Gtk.StateFlags.NORMAL)
        for i, (x, y, rw, rh) in enumerate(engine.rects(name, n, (0, 0, PICTO_W, PICTO_H), gap=2)):
            cr.rectangle(ox + x + 0.5, y + 0.5, rw - 1, rh - 1)
            cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.85 if i == 0 else 0.35)
            cr.fill_preserve()
            cr.set_source_rgba(fg.red, fg.green, fg.blue, 0.9)
            cr.set_line_width(1)
            cr.stroke()
        return False

    def _apply(self, layout):
        if len(self.order) < 2 or not engine.available(layout, len(self.order)):
            return
        xids = list(self.order)
        self._close()
        # let the pop-up unmap first, so it is not the window on top when the
        # tiled windows are raised
        GLib.timeout_add(60, lambda: (self.on_tile(xids, layout), False)[1])

    def _reset(self):
        xids = [w["xid"] for w in self.windows]
        if not xids or self.on_reset is None:
            return
        self._close()
        GLib.timeout_add(60, lambda: (self.on_reset(xids), False)[1])

    def _close(self):
        if self._closing:
            return
        self._closing = True
        self.destroy()

    def _on_key(self, _w, ev):
        key = ev.keyval
        if key == Gdk.KEY_Escape:
            self._close()
            return True
        if key in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if len(self.order) >= 2:
                n = len(self.order)
                self._apply(self.last_layout if engine.available(self.last_layout, n) else "side")
                return True
            return False                  # fewer than two: Enter ticks the row
        typing = self.search is not None and self.search.has_focus()
        if not typing and Gdk.KEY_1 <= key <= Gdk.KEY_9:
            idx = key - Gdk.KEY_1
            vis = self._visible_rows()
            if idx < len(vis):
                check = vis[idx][2]
                check.set_active(not check.get_active())
            return True
        return False

    def _on_focus_out(self, *_a):
        # closing straight away would also catch the brief focus shuffle while
        # the window maps, so check again a moment later
        GLib.timeout_add(150, self._maybe_close)
        return False

    def _maybe_close(self):
        if not self._closing and not self.is_active():
            self._close()
        return False

    # --- placement -----------------------------------------------------------
    def _server_time(self):
        gw = self.get_window()
        try:
            return GdkX11.x11_get_server_time(gw) if gw else 0
        except Exception:                                   # noqa: BLE001
            return 0

    def _place(self, anchor):
        """Top left at the panel's menu point, kept inside the work area.
        Without an anchor (the hotkey), centre it near the top of the screen."""
        area = engine.monitor_area()
        ax, ay, aw, ah = area
        _min, nat = self.get_preferred_size()     # not mapped yet, so not get_size()
        w, h = max(nat.width, WIDTH), nat.height
        if anchor:
            x, y = anchor
            x = x - w // 2
        else:
            x = ax + (aw - w) // 2
            y = ay + ah // 6
        x = max(ax + 4, min(x, ax + aw - w - 4))
        y = max(ay + 4, min(y, ay + ah - h - 4))
        self.move(x, y)
