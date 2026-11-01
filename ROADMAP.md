# Roadmap & Backlog: Window Tiler Tray

> **The single source of truth for forward-looking work.** Anything not shipped lives here.
> Shipped history is in [CHANGELOG.md](CHANGELOG.md), rationale in
> [DECISIONS.md](DECISIONS.md), system design in [ARCHITECTURE.md](ARCHITECTURE.md), known limits
> in [LIMITATIONS.md](LIMITATIONS.md).
>
> **Start at §0.** It lists every open item, one row each. §2.2 is the ledger: the same open
> rows plus every closed one.
>
> Timestamps are ISO 8601 to the second, in UTC (`+00:00`), as for every public repo here. Every row so far was raised on
> 2026-10-31, before the first commit, so Raised dates come from that session.
>
> _Last updated: 2026-11-01T17:48:27+00:00 (0.2.6: rows 26 and 27, §1 and §2.1)._

## 0. North star: every open item, one row each

Grouped by state (Open, Decision, Waiting, Blocked, Deferred, Recurring), then by priority.
`#` is the ledger number and never changes.

| # | Bucket | Priority | State | Size | Impact | Raised | Problem | Solution or next step |
|---|---|---|---|---|---|---|---|---|
| 10 | §3.1 | P2 | **Waiting** | T | M | 2026-10-31 | Autostart is validated but not yet seen working through a real login | At the next login, check the icon is back; RUNBOOK K1 row 1 if not |
| 11 | §3.2 | P3 | **Deferred** | S | L | 2026-10-31 | Two-monitor tiling is coded (target monitor is window 1's) but untested; the test machine has one screen | Comes back when a second monitor is attached |
| 12 | §3.2 | P3 | **Deferred** | S | L | 2026-10-31 | HiDPI scaling and Wayland untested; the work area is read in Gdk logical pixels and wmctrl takes device pixels, and wmctrl is X11 only | Comes back when someone runs a scaled display or asks for Wayland |
| 13 | §3.1 | P3 | **Deferred** | S | L | 2026-10-31 | Undo of a maximized window re-maximizes it, but xfwm4's remembered un-maximized size is lost, so a later un-maximize gives a full-screen-sized window | xfwm4 does not expose that size. Comes back if it bites in daily use |
| 15 | §3.2 | P3 | **Deferred** | M | L | 2026-10-31 | Order can only be set by tick sequence; fixing a wrong order means untick and retick | Drag to reorder rows; comes back if retick proves annoying |
| 27 | §3.1 | P3 | **Decision** | S | M | 2026-11-01 | A crash still leaves the icon gone until the next login or a manual restart | Recommendation: `install.sh --service` installs the RUNBOOK systemd user unit (`Restart=on-abnormal`) and points the autostart entry at it; default install unchanged. Tried on the maintainer's machine 2026-11-01: back 3 seconds after `kill -KILL` |
| 21 | §3.3 | P1 | **Recurring** | T | H | 2026-10-31 | A home path, email, hostname or window title pushed to this public repo would expose the maintainer's setup | Before every push run AGENTS.md Review rule 6 and look at every new image. Last run 2026-11-01T17:48:27+00:00: clean |

**Reading the narrow columns.** Bucket is the §3 area: 3.1 Reliability, 3.2 Features, 3.3
Privacy and release.
Size: T trivial, S small, M medium, L large, ? unknown. Impact: H high, M medium, L low.

### Legend

**Priority** (how much it hurts):

| Priority | Means |
|---|---|
| **P0** | A live customer is losing something today |
| **P1** | Costs a support ticket, real money or a release every time it happens |
| **P2** | The product is measurably worse without it |
| **P3** | Worth doing; nothing breaks if it waits |

An empty P0 is good news. Never inflate an item to fill it.

**Impact** (what it costs not to do):

| Impact | Means |
|---|---|
| **High** | Costs activations, refunds, revenue, or a customer meeting a defect |
| **Medium** | Costs support hours, or blocks something High |
| **Low** | Real, and nobody is bleeding |

Priority, Size and Impact are separate columns because they answer separate questions.

**State** (closed vocabulary; use no other word):

| State | Means |
|---|---|
| **Open** | Not started or partly done; nothing stops it but a decision to begin |
| **Blocked** | Cannot proceed until someone outside the project acts or changes a policy; the row names who |
| **Waiting** | Ready, and deliberately held until a named date (a measurement window, a staged rollout) |
| **Deferred** | Could proceed, and the owner has chosen not to yet (usually new spend, or no demand); the row says what would bring it back |
| **Decision** | An answer from the owner is needed first; the row carries a recommendation |
| **Recurring** | A procedure that runs again every release or on a date; the row records the last run |
| **Done** | Closed, with the date and the size it turned out to be (ledger only) |

## How to keep this file current

| When | Do this |
|---|---|
| An item closes | Move its ledger row to the Done block with `**Done** <date>` and `Was <size>`, remove it from §0, delete its §8 subsection. Never delete the ledger row |
| An item is found | Add it to §0 and the ledger with the next unused number, and to its §3 area if it needs context |
| The owner answers a Decision | Update the §0 row and the ledger row the same day |
| A state changes | Change it in §0 and the ledger together |
| A release or milestone ships | Update §2.1, close the rows it shipped, update §1 |
| Anything above happens | Update the header's `_Last updated_` line with the timestamp and what changed |

---

## 1. Shipped capabilities

| Capability | Since |
|---|---|
| Panel icon, pop-up, four layouts, undo, Super+T, autostart entry | 0.1.0, 2026-10-31 |
| Reset all, flash-free pop-up, public repo under AGPL 3.0 or commercial | 0.2.0, 2026-10-31 |
| Windows that draw their own shadow (Chromium browsers) fill their slot | 0.2.1, 2026-10-31 |
| Docs to the guidelines, roadmap consistency test, UTC-only public history | 0.2.2, 2026-10-31 |
| Overlap notice names apps, not window titles; all layouts verified on real windows | 0.2.3, 2026-10-31 |
| No tray crash when a refresh lands while a menu is open | 0.2.4, 2026-10-31 |
| No separator lines drawn by code | 0.2.5, 2026-10-31 |
| One tray menu for the life of the process, rows edited in place | 0.2.6, 2026-11-01 |

## 2. Next up

### 2.1 Status: 0.2.6 tagged (GitHub releases 0.2.2 to 0.2.5; 0.2.6 release left to the maintainer); row 10 waiting on a real login, row 27 waiting on a maintainer decision (updated 2026-11-01T17:48:27+00:00)

### 2.2 The ledger: every backlog item, pending first, done at the bottom

**The ledger is authoritative for STATE; §3 and §8 are authoritative for REASONING.** Open
rows repeat §0 in one line; §0 holds the problem and solution. Closed rows keep only their
date and size.

| # | Item | Section | State | Size | Impact |
|---|---|---|---|---|---|
| 10 | Autostart seen through a real login | §3.1 | **Waiting**: next login | T | M |
| 11 | Two-monitor tiling | §3.2 | **Deferred** | S | L |
| 12 | HiDPI scaling | §3.2 | **Deferred** | S | L |
| 13 | Undo loses xfwm4's un-maximized size | §3.1 | **Deferred** | S | L |
| 15 | Drag to reorder ticked windows | §3.2 | **Deferred** | M | L |
| 27 | Optional systemd unit that restarts the tray after a crash | §3.1 | **Decision**: maintainer | S | M |
| 21 | Privacy and secret scan before every push | §3.3 | **Recurring**: last run 2026-11-01T17:48:27+00:00 | T | H |
| 1 | Layout engine and CLI | §3.2 | **Done** 2026-10-31 | Was Medium | M |
| 2 | traykit left-click hook, no-poll, no-refresh | §3.2 | **Done** 2026-10-31 | Was Small | M |
| 3 | Panel icon and right-click menu | §3.2 | **Done** 2026-10-31 | Was Small | M |
| 4 | Pop-up picker | §3.2 | **Done** 2026-10-31 | Was Medium | H |
| 5 | Undo last tile | §3.2 | **Done** 2026-10-31 | Was Small | M |
| 6 | Super+T shortcut | §3.2 | **Done** 2026-10-31 | Was Trivial | L |
| 7 | Autostart entry and install.sh | §3.1 | **Done** 2026-10-31 | Was Small | M |
| 8 | Segfault after Undo from the menu | §3.1 | **Done** 2026-10-31 | Was Small | H |
| 14 | Put the project under git | §3.2 | **Done** 2026-10-31: public repo | Was Trivial | L |
| 16 | Reset all: maximize then minimize every window | §3.2 | **Done** 2026-10-31 | Was Small | M |
| 17 | Pop-up flashed and jumped on open | §3.1 | **Done** 2026-10-31 | Was Trivial | M |
| 18 | Gap between checkbox and app icon | §3.2 | **Done** 2026-10-31 | Was Trivial | L |
| 19 | Chromium-based browsers tiled smaller than their slot | §3.1 | **Done** 2026-10-31 | Was Small | M |
| 9 | Trial on real app windows | §3.1 | **Done** 2026-10-31: Grid on 7 by maintainer; Side by side, Stacked, Main + side on 4 real windows, minimum sizes reported correctly | Was Trivial | M |
| 20 | Browser shadow overlapping a neighbour's edge | §3.1 | **Done** 2026-10-31: maintainer clicked next to Edge on all sides, nothing triggered | Was Trivial | L |
| 23 | Overlap notice listed long, private window titles | §3.1 | **Done** 2026-10-31 | Was Trivial | L |
| 24 | Tray segfault when a refresh lands with the menu open | §3.1 | **Done** 2026-10-31 | Was Small | H |
| 25 | Divider lines drawn by code in the icon and pop-up | §3.2 | **Done** 2026-10-31: removed, maintainer | Was Trivial | L |
| 22 | UTC offset and hours visible in timestamps | §3.3 | **Done** 2026-10-31: option (c), maintainer; history squashed, UTC | Was Small | L |
| 26 | Tray segfault with the menu closed: a new menu was swapped in on every rebuild | §3.1 | **Done** 2026-11-01: 0.2.6, one menu edited in place | Was Small | H |

---

## 3. Backlog by area

### 3.1 Reliability

Rows 10, 13 and 27 (rows 8, 24 and 26, the tray crashes, closed).

### 3.2 Features

Rows 11, 12 and 15.

### 3.3 Privacy and release

Row 21 (row 22 closed). The repo is public, so anything committed is permanent in practice: forks
and caches keep it even after a history rewrite.

## 4. Deferred: decided, waiting on something

| Item | Waiting on | Detail |
|---|---|---|
| Two-monitor tiling | A second monitor to test on | Row 11 |
| HiDPI scaling, Wayland | A scaled display, or a user asking for Wayland | Row 12 |
| Keeping the pre-maximize size through Undo | It biting in daily use; xfwm4 does not expose the size | Row 13 |
| Drag to reorder | Retick proving annoying | Row 15 |

## 5. Not doing: decided against, with the reason

| Item | Why |
|---|---|
| X-Tile's own tray mode | Full window, other tray area, ambiguous labels (DECISIONS D1) |
| Calling X-Tile's internal modules | Breaks on any package update (D1) |
| Padding terminals to fill their slot exactly | The terminal's character-cell size hints decide; overriding them gives half a character of dead space either way |
| A two-screen flow | Merged into one pop-up (D3, maintainer 2026-10-31) |
| Separator lines drawn by code | The panel's own Separator item only (D16, maintainer 2026-10-31) |
| A confirmation dialog on Reset all | It is undoable; Undo beats a confirmation for reversible actions (D11) |

## 7. Closed, kept for the reasoning

- Row 8: the crash came from swapping a Gtk menu inside its own item's activate handler.
  **Never rebuild a tray menu synchronously from a menu handler; defer it.**
- Row 24: a timed refresh replaced a menu the user had open. **A menu swap waits until the
  menu is closed, whoever asks for it.**
- Row 26: even with row 24 fixed, a sibling tray segfaulted with its menu closed: each
  rebuild still dropped the old menu while GDK could hold events for it. **Never swap the
  menu at all; keep one and edit its rows in place** (DECISIONS D17).
- Row 17: the window mapped before its layout bar was hidden and before it was moved.
  **Settle a pop-up's size and position before it maps.**

## 8. Open rows in full

None yet: every open row fits in its §0 cells.
