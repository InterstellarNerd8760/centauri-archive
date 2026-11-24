"""Validate experimental glyph and source references."""
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class VocabularyTests(unittest.TestCase):
    def test_tokens_figures_and_sources(self):
        vocabulary = json.loads((ROOT / "archive/vocabulary/index.json").read_text())
        glyphs = ET.parse(ROOT / "archive" / vocabulary["sheet"])
        symbols = {node.attrib["id"] for node in glyphs.iter("{http://www.w3.org/2000/svg}symbol")}
        entries = {entry["id"]: entry for entry in vocabulary["entries"]}
        known_tokens = entries.keys()
        self.assertEqual(len(known_tokens), len(vocabulary["entries"]))
        photos = json.loads((ROOT / "curation/images-100.json").read_text())["records"]
        included = {record["id"] for record in photos if record["status"] == "included"}
        encyclopedia = json.loads((ROOT / "archive/encyclopedia/index.json").read_text())
        articles = {article["id"] for article in encyclopedia["articles"]}
        for entry in vocabulary["entries"]:
            self.assertRegex(entry["id"], r"^V-\d{3}$")
            self.assertIn(entry["id"], symbols)
            self.assertEqual(len(set(entry["examples"] + entry["images"])), 2)
            self.assertTrue(set(entry["examples"]) <= symbols)
            self.assertTrue(set(entry["images"]) <= included)
            self.assertTrue(set(entry["articles"]) <= articles)
            self.assertTrue(entry["ambiguity"])
            for counterpart in entry.get("contrast_with", []):
                self.assertNotEqual(entry["id"], counterpart)
                self.assertIn(counterpart, known_tokens)
                self.assertIn(entry["id"], entries[counterpart]["contrast_with"])
        compounds = vocabulary["statements"]
        descriptions = vocabulary["illustrations"]
        examples = {key for entry in vocabulary["entries"] + compounds for key in entry["examples"]}
        self.assertEqual(set(descriptions), examples)
        self.assertTrue(all(descriptions.values()))
        self.assertEqual(len({entry["id"] for entry in compounds}), len(compounds))
        for statement in compounds:
            self.assertRegex(statement["id"], r"^VS-\d{3}$")
            self.assertGreaterEqual(len(statement["tokens"]), 2)
            self.assertTrue(set(statement["tokens"]) <= known_tokens)
            self.assertEqual(len(set(statement["examples"])), 2)
            self.assertTrue(set(statement["examples"]) <= symbols)
            self.assertTrue(statement["ambiguity"])
