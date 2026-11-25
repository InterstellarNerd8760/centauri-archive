import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from wikipedia_sample import LEGALCODE, REST, acquire, contributors, revision_entry

REST_RESPONSE = {
    "id": 20,
    "size": 11,
    "timestamp": "2026-11-20T11:22:33Z",
    "content_model": "wikitext",
    "page": {"id": 10, "key": "Local_fixture", "title": "Local fixture"},
    "license": {"url": "https://creativecommons.org/licenses/by-sa/4.0/deed.en",
                "title": "Creative Commons Attribution-Share Alike 4.0"},
    "html": "<html><body><p>Test text.</p></body></html>",
}
RAW = json.dumps(REST_RESPONSE).encode()
ITEM = {"page_id": 10, "revision_id": 20, "title": "Local fixture", "rest_sha256": hashlib.sha256(RAW).hexdigest()}


def history(rows, continuation=None):
    response = {"query": {"pages": [{"pageid": 10, "revisions": rows}]}}
    if continuation is not None:
        response["continue"] = {"continue": "||", "rvcontinue": continuation}
    return json.dumps(response).encode()


class WikipediaSampleTests(unittest.TestCase):
    def test_pinned_rest_response_preserves_revision_and_original_license(self):
        with patch("wikipedia_sample.get", return_value=RAW) as get:
            article, source = revision_entry(ITEM)
        self.assertEqual(get.call_args.args[0], f"{REST}20/with_html")
        self.assertEqual(article["version"], {"identifier": 20, "date_modified": REST_RESPONSE["timestamp"]})
        self.assertEqual(article["rights"]["publisher_license"], REST_RESPONSE["license"])
        self.assertEqual(source["rest_sha256"], ITEM["rest_sha256"])
        with patch("wikipedia_sample.get", return_value=RAW + b" "):
            with self.assertRaisesRegex(ValueError, "checksum differs"):
                revision_entry(ITEM)

    def test_history_walk_is_bounded_and_excludes_legacy_ip_addresses(self):
        first = history([{"revid": 20, "user": "ArchiveFixtureEditor"},
                         {"revid": 19, "user": "192.0.2.4", "anon": True}], "one")
        second = history([{"revid": 18, "user": "~2026-123", "temp": True},
                          {"revid": 17, "userhidden": True}])
        with patch("wikipedia_sample.get", side_effect=[first, second]) as get:
            result = contributors(10, 20, 2)
        query = get.call_args_list[1].args[0]
        self.assertIn("rvstartid=20", query)
        self.assertIn("rvcontinue=one", query)
        self.assertEqual(result["status"], "public-pagination-exhausted")
        self.assertEqual(result["revision_rows"], 4)
        self.assertEqual(result["legacy_anonymous_edit_rows"], 1)
        self.assertEqual(result["withheld_editor_rows"], 1)
        self.assertEqual(result["visible_labels"], [{"label": "ArchiveFixtureEditor", "kind": "account"},
                                                    {"label": "~2026-123", "kind": "temporary-account"}])
        self.assertNotIn("192.0.2.4", json.dumps(result))
        with patch("wikipedia_sample.get", return_value=first):
            self.assertEqual(contributors(10, 20, 1)["status"], "request-limit-reached")

    def test_acquire_manifests_local_content_and_attribution_scope(self):
        config = {"id": "test", "acquisition_date": "2026-11-24", "articles": [ITEM]}
        with TemporaryDirectory() as temporary:
            output = Path(temporary) / "sample"
            with patch("wikipedia_sample.get", side_effect=[RAW, b"test license"]) as get:
                result = acquire(config, output)
            self.assertEqual(get.call_args.args[0], LEGALCODE)
            self.assertEqual(json.loads((output / "attribution.ndjson").read_bytes())["status"], "not-collected")
            for name, details in result["files"].items():
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), details["sha256"])


if __name__ == "__main__":
    unittest.main()
