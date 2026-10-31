# Contributing

Thanks for helping. Bug reports, layout ideas and fixes are all welcome.

## Before you start

- Read [AGENTS.md](AGENTS.md): the conventions and the rules learned the hard way apply to
  people as much as to coding agents.
- For anything larger than a small fix, open an issue first so the approach can be agreed.

## Making a change

1. Fork, branch from `main`.
2. Keep `rects()` pure; add or extend tests in `tests/` for any layout change.
3. Run `/usr/bin/python3 -m unittest discover -s tests` (it also checks ROADMAP.md stays
   consistent) and walk the flow on throwaway
   `tilertest*` windows (see [TESTING.md](TESTING.md)).
4. Update [CHANGELOG.md](CHANGELOG.md), and [ROADMAP.md](ROADMAP.md) if the change opens or
   closes an item.
5. Never include personal details: no home paths, emails, hostnames, or screenshots with
   real window titles.
6. Open a pull request describing what changed and how you tested it.

## Licence grant (required)

This project is dual licensed under the AGPL 3.0 and a commercial licence
([COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md)). By submitting a contribution you agree
that:

1. You wrote it, or otherwise have the right to submit it.
2. It is licensed to the public under `AGPL-3.0-only`, like the rest of the project.
3. You grant the maintainer a perpetual, worldwide, irrevocable, royalty-free licence to
   use, modify, sublicense and distribute your contribution under other terms, including
   the commercial licence.

State this in your pull request with the line:

```
I agree to the licence grant in CONTRIBUTING.md.
```

Pull requests without it cannot be merged.
