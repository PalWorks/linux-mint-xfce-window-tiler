#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 PalWorks
"""ROADMAP.md consistency, the checks the roadmap guide asks for.

Sections are found by heading name, not number, so renumbering does not break this.

    /usr/bin/python3 -m unittest discover -s tests -v
"""

import os
import re
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ROADMAP = os.path.join(ROOT, "ROADMAP.md")

# The guide's closed state vocabulary. The legend must define exactly these. Not every
# state needs a row: Open, Decision or Blocked can all be empty at a given moment, so
# "every state used" would fail on a healthy roadmap.
GUIDE_STATES = {"Open", "Blocked", "Waiting", "Deferred", "Decision", "Recurring", "Done"}


def read():
    with open(ROADMAP) as fh:
        return fh.read()


def section(text, heading_words):
    """Body of the first heading whose text contains heading_words, up to the next
    heading of the same or higher level."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#+)\s+(.*)", line)
        if m and heading_words.lower() in m.group(2).lower():
            level = len(m.group(1))
            body = []
            for nxt in lines[i + 1:]:
                n = re.match(r"^(#+)\s", nxt)
                if n and len(n.group(1)) <= level:
                    break
                body.append(nxt)
            return "\n".join(body)
    raise AssertionError("no heading containing %r" % heading_words)


def table_rows(body):
    """Data rows of the first markdown table in body, as lists of stripped cells."""
    rows, started = [], False
    for line in body.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not started:
                started = True            # header row
                continue
            if all(set(c) <= set("-: ") for c in cells):
                continue                  # separator row
            rows.append(cells)
        elif started:
            break
    return rows


def state_word(cell):
    m = re.match(r"\*\*(\w+)\*\*", cell)
    return m.group(1) if m else None


class RoadmapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read()
        cls.north = table_rows(section(cls.text, "North star"))
        cls.ledger = table_rows(section(cls.text, "The ledger"))
        legend = section(cls.text, "Legend")
        cls.legend_states = set(re.findall(r"^\| \*\*(\w+)\*\* \|", legend.split("**State**")[1], re.M))
        prio = legend.split("**Priority**")[1].split("**Impact**")[0]
        cls.legend_prios = re.findall(r"^\| \*\*(P\d)\*\* \|", prio, re.M)

    def test_ledger_states_come_from_the_guide_vocabulary(self):
        self.assertEqual(self.legend_states, GUIDE_STATES)
        used = {state_word(r[3]) for r in self.ledger}
        self.assertTrue(used <= self.legend_states, used - self.legend_states)

    def test_numbers_are_contiguous_and_unique(self):
        nums = [int(r[0]) for r in self.ledger]
        self.assertEqual(sorted(nums), list(range(1, max(nums) + 1)))

    def test_pending_rows_sit_above_done_rows(self):
        states = [state_word(r[3]) for r in self.ledger]
        done = [i for i, s in enumerate(states) if s == "Done"]
        pending = [i for i, s in enumerate(states) if s != "Done"]
        if done and pending:
            self.assertLess(max(pending), min(done))

    def test_cited_sections_exist(self):
        headings = re.findall(r"^#+\s+(\d+(?:\.\d+)*)\.?\s", self.text, re.M)
        for ref in set(re.findall(r"§(\d+(?:\.\d+)*)", self.text)):
            self.assertIn(ref, headings, "§%s is cited but has no heading" % ref)

    def test_north_star_matches_the_ledger(self):
        north = {r[0]: r for r in self.north}
        pending = {r[0]: r for r in self.ledger if state_word(r[3]) != "Done"}
        self.assertEqual(set(north), set(pending))
        for num, row in north.items():
            self.assertEqual(state_word(row[3]), state_word(pending[num][3]), "row %s state" % num)
            self.assertEqual(row[1], pending[num][2], "row %s section" % num)

    def test_priorities_are_from_a_contiguous_legend(self):
        self.assertEqual(self.legend_prios, ["P%d" % i for i in range(len(self.legend_prios))])
        for r in self.north:
            self.assertIn(r[2], self.legend_prios, "row %s" % r[0])

    def test_every_open_row_has_a_problem_and_a_next_step(self):
        for r in self.north:
            self.assertTrue(r[7] and r[8], "row %s" % r[0])

    def test_linked_documents_exist(self):
        for link in set(re.findall(r"\]\(([A-Za-z_./-]+\.md)(?:#[^)]*)?\)", self.text)):
            self.assertTrue(os.path.exists(os.path.join(ROOT, link)), link)


if __name__ == "__main__":
    unittest.main()
