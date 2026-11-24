"""Structural validation of the human-readable encyclopedia."""
from datetime import date
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
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
        self.assertEqual(images, {image for a in self.articles for image in a["images"]})

    def test_editorial_evidence_matches_article_status(self):
        stages = {
            "ai-drafted": "AI-drafted",
            "source-checked": "Source-checked draft",
            "independently-reviewed": "Independently reviewed",
            "publication-ready": "Publication-ready",
        }
        for article in self.articles:
            with self.subTest(article=article["id"]):
                stage = article["review_stage"]
                self.assertIn(stage, stages)
                self.assertTrue(article["status"].startswith(stages[stage]))
                history = article["revision_history"]
                revisions = [entry["revision"] for entry in history]
                self.assertEqual(revisions, sorted(set(revisions)))
                self.assertEqual(revisions[-1], article["revision"])
                for entry in history:
                    self.assertTrue(entry["change"].strip())
                    if "date" in entry:
                        date.fromisoformat(entry["date"])
                terms = article.get("terms", [])
                self.assertEqual(len(terms), len({term["term"].casefold() for term in terms}))
                for term in terms:
                    self.assertTrue(term["term"].strip())
                    self.assertTrue(term["definition"].strip())

                if stage != "ai-drafted":
                    covered_paragraphs = set()
                    for source in article["sources"]:
                        self.assertTrue(urlsplit(source["url"]).hostname)
                        self.assertTrue(source["label"].strip())
                        date.fromisoformat(source["accessed"])
                        self.assertTrue(source["paragraphs"])
                        self.assertTrue(all(type(p) is int for p in source["paragraphs"]))
                        covered_paragraphs.update(source["paragraphs"])
                    self.assertEqual(covered_paragraphs, set(range(1, len(article["body"]) + 1)))
                if stage in ("independently-reviewed", "publication-ready"):
                    review = article["human_review"]
                    self.assertEqual(review["revision"], article["revision"])
                    self.assertTrue(review["reviewer"].strip() and review["evidence"].strip())
                    date.fromisoformat(review["date"])
                if stage == "publication-ready":
                    self.assertTrue(article["publication_record"].strip())

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
