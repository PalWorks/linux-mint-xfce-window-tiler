#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 PalWorks
"""Layout maths tests. No X needed: rects() is pure.

    /usr/bin/python3 -m unittest discover -s tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from tiler_engine import LAYOUTS, available, grid_shape, rects, split  # noqa: E402

AREA = (0, 33, 1920, 1047)          # a 1080p screen under a 33px top panel


def overlaps(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


class SplitTests(unittest.TestCase):
    def test_pieces_fill_exactly(self):
        for k in range(1, 10):
            for gap in (0, 4, 8):
                parts = split(0, 1920, k, gap)
                used = sum(s for _o, s in parts) + gap * (k + 1)
                self.assertEqual(used, 1920, (k, gap))
                self.assertEqual(parts[-1][0] + parts[-1][1] + gap, 1920)

    def test_sizes_differ_by_at_most_one(self):
        sizes = [s for _o, s in split(0, 1000, 7, 0)]
        self.assertLessEqual(max(sizes) - min(sizes), 1)


class RectTests(unittest.TestCase):
    def check(self, layout, n, gap):
        rs = rects(layout, n, AREA, gap)
        self.assertEqual(len(rs), n)
        ax, ay, aw, ah = AREA
        for r in rs:
            x, y, w, h = r
            self.assertGreater(w, 0)
            self.assertGreater(h, 0)
            self.assertGreaterEqual(x, ax + gap)
            self.assertGreaterEqual(y, ay + gap)
            self.assertLessEqual(x + w, ax + aw - gap)
            self.assertLessEqual(y + h, ay + ah - gap)
        for i in range(n):
            for j in range(i + 1, n):
                self.assertFalse(overlaps(rs[i], rs[j]), (layout, n, gap, rs[i], rs[j]))
        if gap == 0:
            self.assertEqual(sum(w * h for _x, _y, w, h in rs), aw * ah,
                             "%s n=%d leaves a hole" % (layout, n))

    def test_every_layout_fills_without_overlap(self):
        for layout in LAYOUTS:
            for n in range(2, 10):
                for gap in (0, 8):
                    with self.subTest(layout=layout, n=n, gap=gap):
                        self.check(layout, n, gap)

    def test_side_by_side_three(self):
        self.assertEqual(rects("side", 3, AREA),
                         [(0, 33, 640, 1047), (640, 33, 640, 1047), (1280, 33, 640, 1047)])

    def test_stacked_two(self):
        self.assertEqual(rects("stacked", 2, AREA),
                         [(0, 33, 1920, 524), (0, 557, 1920, 523)])

    def test_grid_three_stretches_last_row(self):
        self.assertEqual(rects("grid", 3, AREA),
                         [(0, 33, 960, 524), (960, 33, 960, 524), (0, 557, 1920, 523)])

    def test_main_puts_window_one_left_at_sixty_percent(self):
        rs = rects("main", 3, AREA)
        self.assertEqual(rs[0], (0, 33, 1152, 1047))
        self.assertEqual(rs[1], (1152, 33, 768, 524))
        self.assertEqual(rs[2], (1152, 557, 768, 523))

    def test_grid_shape(self):
        self.assertEqual(grid_shape(4), (2, 2))
        self.assertEqual(grid_shape(5), (3, 2))
        self.assertEqual(grid_shape(9), (3, 3))

    def test_available(self):
        self.assertFalse(available("side", 1))
        self.assertTrue(available("side", 2))
        self.assertFalse(available("grid", 2))
        self.assertTrue(available("grid", 3))
        self.assertTrue(available("main", 2))


if __name__ == "__main__":
    unittest.main()
