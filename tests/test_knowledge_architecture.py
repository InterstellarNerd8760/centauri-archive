"""Check the knowledge planning graph, archive budgets and browser derivatives."""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build_knowledge import publish_knowledge
from knowledge_budget import PLANS, measure


class KnowledgeArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads((ROOT / "archive/encyclopedia/index.json").read_text(encoding="utf-8"))
        self.articles = {a["id"]: a for a in self.source["articles"]}

    def test_article_knowledge_fields(self):
        vocab = json.loads((ROOT / "archive/vocabulary/index.json").read_text(encoding="utf-8"))
        known = {entry["id"] for entry in vocab["entries"]}
        purposes = set()
        for a in self.articles.values():
            self.assertIn(a["knowledge_layer"], (3, 4))
            self.assertTrue(a["purpose"].strip())
            self.assertNotIn(a["purpose"], purposes)
            purposes.add(a["purpose"])
            self.assertTrue(set(a["related"]) <= self.articles.keys() - {a["id"]})
            self.assertTrue(set(a["vocabulary"]) <= known)
            self.assertEqual(a["diagrams"], [path for path in a["records"] if path.endswith(".svg")])
            self.assertEqual(a["edition_inclusion"]["core"], "candidate")
            self.assertTrue(all(layer < a["knowledge_layer"] for layer in a["physical_encoding"]["requires_layers"]))
            self.assertTrue(all(self.articles[key]["knowledge_layer"] <= a["knowledge_layer"]
                                for key in a["prerequisites"]))

    def test_backlog_has_stable_unique_topics_and_acyclic_dependencies(self):
        data = json.loads((ROOT / "curation/knowledge-backlog.json").read_text(encoding="utf-8"))
        passed = set()
        categories = {category["id"] for category in self.source["categories"]}
        topic_ids = set()
        essential = 0
        for strand in data["strands"]:
            self.assertNotIn(strand["id"], passed)
            self.assertTrue(set(strand["prerequisite_strands"]) <= passed)
            self.assertIn(strand["category"], categories)
            passed.add(strand["id"])
            for topic in strand["topics"]:
                self.assertNotIn(topic["id"], topic_ids)
                self.assertTrue(topic["id"].startswith(strand["id"] + ":"))
                topic_ids.add(topic["id"])
                if topic["layer"] == 3:
                    essential += 1
                else:
                    self.assertEqual(topic["layer"], 4)
                if "draft_reference" in topic:
                    self.assertIn(topic["draft_reference"], self.articles)
        self.assertEqual((essential, len(topic_ids)), (100, 300))

    def test_site_index_does_not_include_article_bodies(self):
        with TemporaryDirectory() as root:
            publish_knowledge(root)
            out = Path(root) / "knowledge"
            catalog = json.loads((out / "catalog.json").read_text(encoding="utf-8"))
            self.assertEqual({a["id"] for a in catalog["articles"]}, self.articles.keys())
            for article in catalog["articles"]:
                number = article["id"]
                self.assertNotIn("body", article)
                self.assertEqual(json.loads((out / "articles" / f"{number}.json").read_text(encoding="utf-8")),
                                 self.articles[number])
            shard = json.loads((out / "search-01.json").read_text(encoding="utf-8"))
            self.assertIn(self.articles["CA-01.001"]["body"][0].lower(), shard["CA-01.001"])

    def test_budget_exact_totals_and_separate_copy_multiplier(self):
        ledger, tripled = measure(copies=1), measure(copies=3)
        self.assertEqual(sum(ledger["source_bytes"].values()), ledger["logical_source_bytes"])
        self.assertEqual(ledger["articles"], len(self.articles))
        self.assertEqual(tuple(case["articles"] for case in ledger["scenarios"]), PLANS)
        for first, third in zip(ledger["scenarios"], tripled["scenarios"]):
            self.assertEqual(first["logical_bytes"], third["logical_bytes"])
            self.assertGreater(first["protected_bytes"], first["logical_bytes"])
            self.assertEqual(first["encoded_bytes"] * 3, third["encoded_bytes"])
            self.assertEqual(first["encoded_bytes"] * 2, third["redundant_copy_bytes"])
