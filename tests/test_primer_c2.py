"""Check C2 reproducibility and coverage of the readout conventions."""
import graphlib
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_primer_c2


class PrimerC2Tests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "docs/primer-c2-data.json").read_text())

    def test_drawings_regenerate_and_annotations_do_not_change_marks(self):
        rendered = build_primer_c2.outputs(self.data)
        for name, svg in rendered.items():
            self.assertEqual((ROOT / "docs" / name).read_bytes(), svg.encode("utf-8"))
        plain = ET.fromstring(rendered["primer-c2.svg"])
        annotated = ET.fromstring(rendered["primer-c2-annotated.svg"])
        trial = ET.fromstring(rendered["primer-c2-trial.svg"])
        for root in (plain, trial):
            self.assertFalse(any(element.text and element.text.strip() for element in root.iter()))
            self.assertTrue(all("href" not in key
                                for element in root.iter() for key in element.attrib))
        marks = {"path", "rect", "circle"}
        self.assertEqual(
            [ET.tostring(node) for node in plain],
            [ET.tostring(node) for node in annotated if node.tag.rsplit("}", 1)[-1] in marks],
        )

    def test_readout_target_is_unseen_and_decoys_use_other_locators(self):
        self.assertEqual(4 * self.data["fine_pitch"], self.data["coarse_pitch"])
        trial = self.data["trial"]
        training = self.data["training"]
        self.assertNotIn(trial["locator"], {record["locator"] for record in training})
        self.assertNotIn(trial["rows"], [record["rows"] for record in training])
        for record in [*training, trial]:
            self.assertGreaterEqual(record["locator"], 0)
            self.assertLess(record["locator"], 16)
            self.assertEqual(len(record["rows"]), 3)
            for row in record["rows"]:
                self.assertRegex(row, r"^[01]{8}$")

    def test_convention_catalog_has_resolvable_acyclic_dependencies(self):
        catalog = json.loads((ROOT / "docs/primer-c2-conventions.json").read_text())
        self.assertEqual(catalog["schema_version"], 1)
        self.assertEqual(catalog["parent_edition"], "C1")
        self.assertEqual(catalog["primer_edition"], self.data["sheet"])
        entries = catalog["conventions"]
        dependencies = {entry["id"]: entry["prerequisites"] for entry in entries}
        self.assertEqual(len(dependencies), len(entries))
        for entry in entries:
            self.assertRegex(entry["introduced"], r"^(C1/[A-E]|C2/F)$")
            self.assertTrue(entry["definition"])
            self.assertTrue(entry["observation"])
            self.assertTrue(set(entry["prerequisites"]) <= dependencies.keys())
        self.assertEqual(len(list(graphlib.TopologicalSorter(dependencies).static_order())), len(entries))


if __name__ == "__main__":
    unittest.main()
