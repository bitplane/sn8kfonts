import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from flfimport import trim
from genfiglet import main
from render import render


class TextEncodingTests(unittest.TestCase):
    def test_cells_are_drawn_as_written(self):
        self.assertEqual(render(["S.", "' "], 2, "text"), "S.\n' ")

    def test_a_font_that_draws_dollars_gets_another_hardblank(self):
        with tempfile.TemporaryDirectory() as tmp:
            font = Path(tmp) / "x"
            font.mkdir()
            (font / "0024_dollar.txt").write_text("$ \n' \n")
            out = Path(tmp) / "x.tlf"
            main([str(font), "--encoding", "text", "--gap", "0", "-o", str(out)])
            lines = out.read_text().splitlines()
            self.assertTrue(lines[0].startswith("tlf2a~ 2 2"))
            dollar = lines.index("$ @")
            self.assertEqual(lines[dollar + 1], "' @@")


    def test_imported_glyphs_lose_their_smushing_padding(self):
        self.assertEqual(trim(["  __ ", " (_  ", " __) "]), [" __", "(_ ", "__)"])

    def test_credits_replace_the_licence_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            font = Path(tmp) / "x"
            font.mkdir()
            (font / "0041_A.txt").write_text("A\n")
            (font / "CREDITS").write_text("Glyphs: someone else's\n")
            out = Path(tmp) / "x.tlf"
            main([str(font), "--encoding", "text", "-o", str(out)])
            text = out.read_text()
            self.assertIn("Glyphs: someone else's", text)
            self.assertNotIn("WTFPL", text)


if __name__ == "__main__":
    unittest.main()
