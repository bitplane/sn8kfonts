import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from render import octant, render
from saa5050import import convert


class OctantTests(unittest.TestCase):
    def test_unicode_mapping_uses_legacy_and_supplement_characters(self):
        self.assertEqual(octant(0), " ")
        self.assertEqual(octant(4), "\U0001CD00")
        self.assertEqual(octant(0x55), "▌")
        self.assertEqual(octant(0xFF), "█")

    def test_render_packs_a_two_by_four_cell(self):
        self.assertEqual(render(["##"] * 4, 2, "octant"), "█")

    def test_digit_corrections_are_stable(self):
        self.assertEqual(convert(ord("0"), [0] * 10), [6, 9, 9, 9, 9, 9, 6, 0])
        self.assertEqual(convert(ord("1"), [0] * 10), [4, 12, 4, 4, 4, 4, 4, 0])


if __name__ == "__main__":
    unittest.main()
