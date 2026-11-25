"""Validate the reproducible primer drawings and their held-out examples."""
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_primer


class PrimerTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((build_primer.DOCS / "primer-ladder-data.json").read_text())

    def test_generated_drawings_are_current(self):
        rendered = build_primer.outputs(self.data)
        for name, svg in rendered.items():
            with self.subTest(name=name):
                self.assertEqual((build_primer.DOCS / name).read_bytes(), svg.encode("utf-8"))

    def test_annotation_keeps_training_marks_and_trial_has_no_text(self):
        def marks(svg):
            root = ET.fromstring(svg)
            return [element for element in root if element.tag.rsplit("}", 1)[-1] in
                    {"circle", "path", "rect"}]

        plain = build_primer.render_ladder(self.data)
        annotated = build_primer.render_ladder(self.data, annotated=True)
        trial = build_primer.render_trial(self.data)
        self.assertEqual(
            [ET.tostring(element) for element in marks(plain)],
            [ET.tostring(element) for element in marks(annotated)],
        )
        for svg in (plain, trial):
            root = ET.fromstring(svg)
            self.assertFalse(any((element.text or "").strip() for element in root.iter()))
            self.assertTrue(all(not name.endswith("href")
                                for element in root.iter() for name in element.attrib))

    def test_orientation_reference_has_one_dissenting_cell(self):
        reference = self.data["orientation"]
        patterns = self.data["patterns"]
        self.assertEqual(len(set(map(len, patterns))), 1)
        self.assertEqual(patterns.count(reference), 3)
        self.assertEqual([index for index, pair in enumerate(zip(reference, patterns[2]))
                          if pair[0] != pair[1]], [3])

    def test_raster_examples_fit_fields_and_trials_are_held_out(self):
        training = self.data["rasters"]
        trial = self.data["trial"]["rasters"]
        self.assertTrue({0, 1, 2}.issubset(record["mode"] for record in training))
        all_records = [*training, *trial]
        self.assertEqual(len({record["id"] for record in all_records}), len(all_records))
        self.assertTrue({(len(record["rows"][0]), len(record["rows"])) for record in training}
                        .isdisjoint((len(record["rows"][0]), len(record["rows"])) for record in trial))
        for record in all_records:
            with self.subTest(record_id=record["id"]):
                rows = record["rows"]
                width = len(rows[0])
                self.assertTrue(0 < record["id"] < 16)
                self.assertTrue(0 < width * len(rows) < 16)
                self.assertTrue(all(len(row) == width for row in rows))
                for row in rows:
                    for pixel in row:
                        if record["mode"] == 2:
                            self.assertEqual(len(pixel), 3)
                            self.assertTrue(all(0 <= value <= 7 for value in pixel))
                        else:
                            self.assertTrue(0 <= pixel <= (1 if record["mode"] == 0 else 7))


if __name__ == "__main__":
    unittest.main()
