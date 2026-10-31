# AGENTS.md: Linux Mint XFCE Window Tiler

_Last updated: 2026-10-31T05:26:41+00:00 (no drawn separators)._

The behaviour contract for any coding agent working in this repo. Read
[README.md](README.md) for what the project is, then this file before changing anything.

| To know | Read |
|---|---|
| How it fits together | [ARCHITECTURE.md](ARCHITECTURE.md) |
| What the words mean, the rules | [DOMAIN.md](DOMAIN.md) |
| Why it is this way | [DECISIONS.md](DECISIONS.md) |
| What is open | [ROADMAP.md](ROADMAP.md), following the roadmap guide's structure |
| What it cannot do | [LIMITATIONS.md](LIMITATIONS.md) |
| How to build, debug, release | [PLAYBOOK.md](PLAYBOOK.md), [RUNBOOK.md](RUNBOOK.md), [TESTING.md](TESTING.md) |

## Roles

| Role | Does |
|---|---|
| Maintainer | Decides priorities, answers Decision rows in [ROADMAP.md](ROADMAP.md), merges |
| Agent | Builds, tests and documents within the rules below |

## Allowed actions

- Edit anything under `src/`, `tests/` and the docs.
- Run `./install.sh` (idempotent) and restart the tiler tray.
- Open throwaway test windows titled `tilertest*` to try layouts, and close them after.

## Restricted areas

| Area | Rule |
|---|---|
| `src/traykit.py` | Other trays may share an installed copy. Changes stay backwards compatible, defaulting to the old behaviour |
| Installed symlinks in `TILER_BIN_DIR` | Point into `src/`. Never edit them or replace them with copies |
| The user's real windows | Never tile, move, reset or close them in tests without asking. Use `tilertest*` windows |
| Keyboard shortcuts | Never overwrite an existing binding |
| `LOCAL.md` | Machine-specific notes, gitignored. Read it if present; never commit it |
| Anything pushed | No personal names, emails, home paths, hostnames, account names, or window titles from a real desktop, in code, docs, commits or screenshots. Scan before every push (see Review rules) |

## Conventions

- **Run everything under `/usr/bin/python3`**, never bare `python3`.
- Every source file starts with `# SPDX-License-Identifier: AGPL-3.0-only` and the
  copyright line.
- Module docstring says what and why; short comments on the non-obvious only;
  `# noqa: BLE001` on deliberate broad excepts.
- Layout maths stays pure in `rects()`, testable without X.
- Plain, specific UI copy: buttons name the action, hints say what to do next.
- **Never draw separator lines in code**: not in the icon, not as label characters, not as
  `Gtk.Separator` between controls. Panel separators come from the panel's own Separator
  item in Panel Preferences; inside the pop-up, use space (DECISIONS D16).
- Doc timestamps: `date -u --iso-8601=seconds` (UTC, `+00:00`), never estimated. Commit
  with `TZ=UTC git commit ...` so commit dates carry no local offset either.

## Rules learned the hard way

1. **Never swap a tray menu while it is open or closing**, neither from one of its own
   item handlers nor from a poll that lands while the user has it open. The old menu is
   freed, GDK dispatches its pending events to freed memory, the process segfaults.
   traykit postpones `rebuild()` until the menu hides and keeps the previous menu alive
   one generation; `_rebuild_soon()` in the tray covers the item-handler case.
2. **Never show the pop-up before its size and position are settled.** Calling
   `show_all()` on the window, then hiding the layout bar and moving it, flashed a
   full-height window in the wrong place on every click. Show the children, settle, move,
   then present.
3. **Anchor `pkill -f` patterns** with `^/usr/bin/python3 <dir>/tiler-tray.py`.
   Unanchored, the pattern matches the shell running the command.
4. **Move windows with `wmctrl -e`, not `Wnck.Window.set_geometry`** (DECISIONS D2).
5. **Unmaximize, then wait, then move.** xfwm4 applies state asynchronously; `_settle()`
   waits up to 500ms. Undo does the same before restoring.
6. **Read frame extents after unmaximizing.** A maximized xfce4-terminal reports
   `0,0,36,0`, the same window normal `2,36,2,2`.
7. **A new xfconf shortcut is not live until `xfsettingsd` reloads.**
8. **A status icon must register with a label or never gets one** (`initial_label`), and
   setting the same icon path twice does not reload it (alternating icon files). Both are
   handled in `traykit.py`; do not remove them.

## Review rules

Before calling a change done:

1. `/usr/bin/python3 -m unittest discover -s tests` passes, layout and roadmap tests both.
2. `/usr/bin/python3 -m py_compile src/*.py`, then delete `src/__pycache__`.
3. Restart the tray and walk the flow on `tilertest*` windows: open, tick, tile, undo,
   reset, undo.
4. The tray process is still alive afterwards, and `journalctl --since <start>` shows no
   segfault.
5. Update CHANGELOG.md, ROADMAP.md, REQUIREMENTS.md and any doc the change touches.
   Releasing: [PLAYBOOK.md](PLAYBOOK.md).
6. Before a push: `git grep -niE "$HOME|$(whoami)|@[a-z0-9.-]+\.[a-z]{2,}"` and a
   scan for key patterns (`AIza`, `sk-`, `ghp_`, `xox`, `eyJ`, private key blocks) return
   nothing unexpected, commits use the GitHub noreply address, and `git log --format=%ad` shows `+0000` only.

## Safety

- No network calls, no secrets, no credentials anywhere in this project.
- `undo.json` and `settings.json` hold window ids, titles and geometry. Titles can contain
  email addresses and project names; both files stay local and never go into the repo.
