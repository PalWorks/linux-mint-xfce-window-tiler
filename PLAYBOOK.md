# Playbook

Step-by-step procedures: build a feature, add a layout, debug, release, roll back.

_Last updated: 2026-10-31T04:22:28+00:00 (first version)._

## Implement a feature

1. Read [AGENTS.md](AGENTS.md), [DOMAIN.md](DOMAIN.md) and the ROADMAP row, if there is
   one.
2. Put maths in `tiler_engine.py` as pure functions with tests; window manager calls next
   to `tile()`; UI in `tiler_picker.py`; menu and settings in `tiler-tray.py`.
3. Test on `tilertest*` windows only ([TESTING.md](TESTING.md) has the script).
4. Update REQUIREMENTS, CHANGELOG, ROADMAP and any doc the change touches, timestamped.

## Add a layout

1. `tiler_engine.py`: add the key to `LAYOUTS`, its button text to `LAYOUT_NAMES`, a branch
   in `rects()`, and a rule in `available()` if it needs a minimum count.
2. `tests/test_layouts.py` picks it up in the fill-and-overlap test automatically; add one
   fixed expectation for a small count.
3. The pop-up button and its picture come from `LAYOUTS` and `rects()`; nothing to add in
   the UI unless the label is long.
4. Run the tests, then tile 2, 3 and 5 test windows in it from the CLI.

## Debug

1. Start with [RUNBOOK.md](RUNBOOK.md).
2. Reproduce with the engine CLI: `tiler_engine.py --list`, then `--layout` on
   `tilertest*` xids. It prints `tiled`, `stuck` and `gone`.
3. Compare where a window landed (`xwininfo -id <xid>`) with its slot
   (`tiler_engine.rects(...)`), allowing for frame extents and drawn shadow
   (`xprop -id <xid> _NET_FRAME_EXTENTS _GTK_FRAME_EXTENTS`).
4. Crashes: `journalctl --since <time> | grep -A30 'python3.*segfault'` gives the native
   stack. GDK in the stack usually means a widget destroyed while handling its own event.
5. Run the tray in a terminal to see Python errors:
   `/usr/bin/python3 <bin>/tiler-tray.py` after stopping the running one.

## Release

1. Tests pass; walk the flow on test windows (AGENTS.md Review rules).
2. CHANGELOG: new `## X.Y.Z, <timestamp>` section. ROADMAP: close shipped rows, update §1
   and §2.1. Timestamp every doc you touched.
3. Privacy and secret scan, the commands in AGENTS.md Review rule 6, plus a look at every
   added image. Commits must use the GitHub noreply address.
4. Commit with `TZ=UTC git commit`, then tag: `TZ=UTC git tag -a vX.Y.Z -m "X.Y.Z"`,
   `git push --follow-tags`.
5. `gh release create vX.Y.Z --notes-file <the CHANGELOG section>`.

Versioning: patch for fixes and docs, minor for new features or layouts, major if the
settings or undo file formats change incompatibly.

## Roll back

Installed files are symlinks into the clone, so the clone's checkout is what runs.

1. `git checkout vX.Y.Z` (or `git revert <commit>` to undo one change on `main`).
2. Restart the tray (RUNBOOK, "Restart cleanly").
3. If the installed shape changed between versions, run `./install.sh` again with the same
   `TILER_BIN_DIR`.
