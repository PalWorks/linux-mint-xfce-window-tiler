# Security

## What the tiler touches

| Touches | How |
|---|---|
| Your windows | Reads titles, classes and geometry through Wnck; moves, maximizes and minimizes them through `wmctrl` |
| Files | `~/.config/tiler-tray/settings.json`, `~/.local/share/tiler-tray/` (icon, lock file, `undo.json`), `~/.config/autostart/tiler-tray.desktop` |
| Settings | One XFCE keyboard shortcut, `<Super>t`, only if it was free |
| Processes | Sends `SIGUSR1` only to the pid in its own lock file, after checking that process is `tiler-tray.py` |

It makes **no network connections**, needs no root, and stores no credentials.

`undo.json` holds the titles of the windows last tiled or reset. Window titles can contain
email addresses, document names or project names, so treat that file as private. It is
deleted once Undo uses it.

## Reporting a vulnerability

Please do not open a public issue for a security problem. Use GitHub's private
vulnerability reporting on this repository (Security tab, "Report a vulnerability"). You
will get an acknowledgement, and a fix or an explanation, as soon as it can be looked at.

## Supported versions

Only the latest release on `main` receives fixes.
