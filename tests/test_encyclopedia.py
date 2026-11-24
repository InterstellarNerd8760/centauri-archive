"""Structural validation of the human-readable encyclopedia."""
import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_site import assemble

class EncyclopediaTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "archive/encyclopedia/index.json").read_text())
        self.articles = self.data["articles"]

    def test_hierarchy_and_article_links(self):
        names = ["Mathematics", "Physical universe", "Earth", "Life", "Humanity",
                 "Civilization", "Technology", "Culture and experience", "The archive and mission"]
        self.assertEqual([c["title"] for c in self.data["categories"]], names)
        self.assertEqual([c["id"] for c in self.data["categories"]], [f"{i:02}" for i in range(1, 10)])
        self.assertGreaterEqual(len(self.articles), 25)
        by_id = {a["id"]: a for a in self.articles}
        self.assertEqual(len(by_id), len(self.articles))
        image_plan = json.loads((ROOT / "curation/images-100.json").read_text())
        images = {r["id"] for r in image_plan["records"]}
        catalog = json.loads((ROOT / "archive/catalog.json").read_text())
        paths = {r["path"] for r in catalog["records"]}
        for a in self.articles:
            self.assertRegex(a["id"], r"^CA-" + a["category"] + r"\.[0-9]{3}$")
            self.assertTrue(a["body"] and a["limitations"] and a["status"])
            self.assertTrue(set(a["prerequisites"]) <= set(by_id))
            self.assertTrue(set(a["images"]) <= images)
            self.assertTrue(set(a["records"]) <= paths)
            for source in a["sources"]:
                self.assertTrue(source["url"].startswith("https://"))
        visiting, visited = set(), set()
        def visit(key):
            self.assertNotIn(key, visiting, "Cyclic prerequisite graph")
            if key in visited:
                return
            visiting.add(key)
            for p in by_id[key]["prerequisites"]:
                visit(p)
            visiting.remove(key)
            visited.add(key)
        for key in by_id:
            visit(key)

    def test_site_and_package_share_source_bytes(self):
        with TemporaryDirectory() as temp:
            site = Path(temp)
            assemble(site)
            source = (ROOT / "archive/encyclopedia/index.json").read_bytes()
            self.assertEqual(source, (site / "records/encyclopedia/index.json").read_bytes())
            with ZipFile(site / "downloads/centauri.zip") as package:
                self.assertEqual(source, package.read("content/encyclopedia/index.json"))
            for name in ("encyclopedia.html", "encyclopedia.js", "encyclopedia.css"):
                self.assertTrue((site / name).is_file())
            self.assertIn("encyclopedia.html", (site / "index.html").read_text())

if __name__ == "__main__":
    unittest.main()
