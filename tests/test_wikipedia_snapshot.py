import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from wikipedia_snapshot import checksum_spec, fetch, transform

FIXTURE = ROOT / "tests/fixtures/wikipedia-synthetic.ndjson"
PIN = "sha256:31d1a70e4bb2f24c946b575050d4b337e8a4af2627af356b0ddbe51bdda34f70"
SETTINGS = dict(input_format="ndjson", project="syntheticwiki", snapshot_id="centauri-fixture-v1",
                snapshot_date="2026-11-24",
                source_url="https://archive-fixture.example.invalid/snapshot/centauri-fixture-v1")


class WikipediaSnapshotTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.output = self.root / "out"

    def build(self, source=FIXTURE, **settings):
        return transform(source, self.output, **(SETTINGS | settings))

    def records(self):
        return [json.loads(line) for line in (self.output / "articles.ndjson").read_bytes().splitlines()]

    def make_tarball(self, *entries):
        path = self.root / "input.tar.gz"
        with tarfile.open(path, "w:gz") as archive:
            for name, payload in entries:
                item = tarfile.TarInfo(name)
                item.size = len(payload)
                archive.addfile(item, io.BytesIO(payload))
        return path

    def test_pinned_extraction_preserves_content_and_provenance(self):
        manifest = self.build(expected=checksum_spec(PIN))
        first, second = self.records()
        article_file = (self.output / "articles.ndjson").read_bytes()
        self.assertEqual(manifest["articles"]["records"], 2)
        self.assertEqual(manifest["articles"]["sha256"], hashlib.sha256(article_file).hexdigest())
        self.assertEqual(manifest["articles"]["bytes"], len(article_file))
        self.assertEqual(manifest["snapshot"]["uncompressed_ndjson_bytes"], len(FIXTURE.read_bytes()))
        self.assertEqual(manifest["counts"], {"input_rows": 7, "article": 4, "outside-main-namespace": 1,
                                              "redirect": 1, "visibility-or-deletion": 1})
        self.assertEqual(first["id"], "wiki:syntheticwiki:11")
        self.assertEqual(second["id"], "wiki:syntheticwiki:12")
        self.assertEqual(first["source"]["revision_id"], 27)
        self.assertTrue(first["source"]["revision_url"].endswith("/revisions/27"))
        self.assertTrue(first["source"]["history_url"].endswith("/history"))
        self.assertEqual(first["source"]["snapshot_date"], "2026-11-24")
        self.assertEqual(first["source"]["licenses"][0]["identifier"], "CC0-1.0")
        self.assertIn("Centauri Archive", first["source"]["provided_attribution"]["attribution"][0])
        self.assertEqual(first["source"]["license_notices"][0]["url"],
                         "https://creativecommons.org/publicdomain/zero/1.0/")
        self.assertEqual([(b["level"], b["text"]) for b in first["blocks"] if b["kind"] == "heading"],
                         [(2, "Area"), (3, "Units"), (2, "References")])
        text = " ".join(b["text"] for b in first["blocks"])
        self.assertIn("π⟦math:1⟧.", text)
        self.assertIn("m^(2)", text)
        self.assertIn("radius | 3", text)
        self.assertNotIn("[1]", text)
        self.assertNotIn("Fixture navigation", text)
        self.assertNotIn("Fixture links omitted", text)
        self.assertEqual(first["formulae"][0]["tex"], "r^2")
        self.assertIn("<msup>", first["formulae"][0]["mathml"])
        self.assertEqual(first["citations"][0]["target"],
                         "https://archive-fixture.example.invalid/11#cite_note-area")
        self.assertIn("Original reference text", first["references"][0]["text"])
        self.assertIn("https://example.invalid/geometry", first["references"][0]["links"])
        self.assertIn({"text": "See counting", "url": "https://archive-fixture.example.invalid/12"}, first["links"])
        self.assertIn({"kind": "list-item", "list_depth": 2, "text": "Two"}, second["blocks"])

    def test_reproducible_and_tar_adapter(self):
        manifest = self.build(expected=checksum_spec(PIN))
        data = (self.output / "articles.ndjson").read_bytes()
        manifest_bytes = (self.output / "manifest.json").read_bytes()
        self.output = self.root / "reproduction"
        self.build(expected=checksum_spec(PIN))
        self.assertEqual(data, (self.output / "articles.ndjson").read_bytes())
        self.assertEqual(manifest_bytes, (self.output / "manifest.json").read_bytes())
        self.output = self.root / "from-tar"
        tarball = self.make_tarball(("source.ndjson", FIXTURE.read_bytes()))
        tar_manifest = self.build(tarball, input_format="enterprise-tar-gz")
        self.assertEqual(data, (self.output / "articles.ndjson").read_bytes())
        self.assertEqual(tar_manifest["articles"], manifest["articles"])
        self.assertEqual(tar_manifest["snapshot"]["bytes"], tarball.stat().st_size)

    def test_bad_checksum_bad_rows_and_extra_tar_members_fail_atomically(self):
        invalid_input = self.root / "invalid.ndjson"
        invalid_input.write_bytes(FIXTURE.read_bytes() + b'{"truncated"\n')
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            self.build(expected=checksum_spec("sha256:" + "0" * 64))
        with self.assertRaisesRegex(ValueError, "line 8"):
            self.build(invalid_input)
        tarball = self.make_tarball(("source.ndjson", FIXTURE.read_bytes()), ("extra.txt", b"extra"))
        with self.assertRaisesRegex(ValueError, "more than one data file"):
            self.build(tarball, input_format="enterprise-tar-gz")
        self.assertFalse(self.output.exists())
        self.assertEqual({p.name for p in self.root.iterdir()}, {invalid_input.name, tarball.name})

    def test_wikipedia_adapter_retains_expected_license_and_revision_links(self):
        article = json.loads(FIXTURE.read_bytes().splitlines()[0])
        article["is_part_of"]["identifier"] = "enwiki"
        article["url"] = "https://en.wikipedia.org/wiki/Synthetic_entry"
        article["license"] = [
            {"identifier": "CC-BY-SA-4.0", "url": "https://creativecommons.org/licenses/by-sa/4.0/"},
            {"identifier": "fixture-additional-notice", "url": "https://example.invalid/additional-notice"},
        ]
        input_path = self.root / "source.ndjson"
        input_path.write_text(json.dumps(article) + "\n", encoding="utf-8")
        self.build(input_path, project="enwiki")
        source = self.records()[0]["source"]
        self.assertEqual(source["revision_url"], "https://en.wikipedia.org/w/index.php?oldid=32")
        self.assertEqual(source["history_url"], "https://en.wikipedia.org/w/index.php?curid=12&action=history")
        self.assertEqual(source["licenses"], article["license"])

    def test_fetch_requires_https_limits_bytes_and_checks_integrity(self):
        body = b"pinned snapshot sample"
        target = self.root / "sample"
        url = "https://example.invalid/pinned"
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            fetch("http://example.invalid/pinned", target, 100, None)
        for headers, maximum, expected, failure in [
            ({"Content-Length": str(len(body))}, 8, None, "server reports"),
            ({}, 8, None, "explicit download byte limit"),
            ({"Content-Length": str(len(body) + 1)}, 100, None, "incomplete response"),
            ({}, 100, checksum_spec("sha1:" + "0" * 40), "checksum mismatch"),
        ]:
            with self.subTest(failure=failure), patch("wikipedia_snapshot.build_opener") as opener:
                response = Mock(wraps=io.BytesIO(body))
                response.headers = headers
                opener.return_value.open.return_value.__enter__.return_value = response
                with self.assertRaisesRegex(ValueError, failure):
                    fetch(url, target, maximum, expected)
                self.assertFalse(target.exists())
        with patch("wikipedia_snapshot.build_opener") as opener:
            response = Mock(wraps=io.BytesIO(body))
            response.headers = {"Content-Length": str(len(body))}
            opener.return_value.open.return_value.__enter__.return_value = response
            expected = checksum_spec("sha1:" + hashlib.sha1(body).hexdigest())
            result = fetch(url, target, len(body), expected)
        self.assertEqual(target.read_bytes(), body)
        self.assertEqual(result["sha256"], hashlib.sha256(body).hexdigest())


if __name__ == "__main__":
    unittest.main()
