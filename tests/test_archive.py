import json
import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import warnings
from zipfile import ZipFile
from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from archive import build, examine
from build_site import assemble
from plate import plate
from decode_raster import decode_rows


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []
        self.anchors = set()
        self.canonicals = []
        self.section_nav = []
        self.brand = None
        self.in_section_nav = False
        self.section_link_text = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.anchors.add(attrs["id"])
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonicals.append(attrs.get("href"))
        if tag == "nav" and attrs.get("aria-label") == "Centauri Archive":
            self.in_section_nav = True
        if tag == "a":
            if "brand" in attrs.get("class", "").split():
                self.brand = (attrs.get("href"), attrs.get("aria-current"))
            if self.in_section_nav:
                self.section_nav.append((attrs.get("href"), attrs.get("aria-current"), []))
                self.section_link_text = self.section_nav[-1][2]
        for key in ("href", "src"):
            if key in attrs:
                self.targets.append(attrs[key])

    def handle_data(self, data):
        if self.section_link_text is not None:
            self.section_link_text.append(data)

    def handle_endtag(self, tag):
        if tag == "nav":
            self.in_section_nav = False
        if tag == "a":
            self.section_link_text = None


class ArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.sample = cls.root / "sample.zip"
        cls.manifest = build(cls.sample)

    def test_deterministic_and_within_budget(self):
        second = self.root / "second.zip"
        build(second)
        self.assertEqual(second.read_bytes(), self.sample.read_bytes())
        self.assertTrue(1000 <= second.stat().st_size <= 80_000_000)
        self.assertEqual(examine(second, verify=True), self.manifest)
        self.assertEqual(self.manifest["archive_version"], "0.8.0")

    def test_archive_has_meaningful_records(self):
        names = {item["path"] for item in self.manifest["files"]}
        required = {
            "content/primer/start.txt",
            "content/primer/mathematics.txt",
            "content/earth/solar-system.txt",
            "content/biology/foundations.txt",
            "content/biology/genetics.txt",
            "content/biology/diversity.txt",
            "content/humanity/civilization.txt",
            "content/humanity/history.txt",
            "content/messages/draft.txt",
        }
        self.assertTrue(required.issubset(names))
        self.assertNotIn("content/earth/shadow.txt", names)
        self.assertNotIn("content/life/leaf.txt", names)
        self.assertNotIn("content/civilization/weaving.csv", names)
        self.assertNotIn("content/primer/plate.pgm", names)
        with ZipFile(self.sample) as package:
            for name in required:
                self.assertGreater(len(package.read(name)), 150)
            self.assertIn(b"DNA", package.read("content/biology/genetics.txt"))
            self.assertIn(b"Earth", package.read("content/earth/solar-system.txt"))
            self.assertIn(b"UNAPPROVED", package.read("content/messages/draft.txt"))

    def test_multimedia_catalog_and_provenance(self):
        with ZipFile(self.sample) as package:
            catalog = json.loads(package.read("content/catalog.json"))
        paths = {entry["path"] for entry in self.manifest["files"]} - {"content/catalog.json"}
        catalog_paths = ["content/" + item["path"] for item in catalog["records"]]
        self.assertEqual(paths, set(catalog_paths))
        self.assertEqual(len(catalog_paths), len(set(catalog_paths)))
        self.assertGreaterEqual(len(paths), 20)
        self.assertGreaterEqual(sum(p.endswith(".svg") for p in paths), 3)
        for path in (ROOT / "archive/visuals").glob("*.svg"):
            ET.parse(path)
        for item in catalog["records"]:
            for field in ("title", "summary", "group", "status", "rights"):
                self.assertTrue(item.get(field), (item["path"], field))
            for source in item.get("sources", []):
                self.assertTrue(source["url"].startswith("https://"))

    def test_one_hundred_image_editorial_plan(self):
        plan = json.loads((ROOT / "curation/images-100.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["editorial_goal"], 100)
        self.assertGreaterEqual(len(plan["records"]), plan["editorial_goal"])
        self.assertEqual(len(plan["categories"]), 10)
        self.assertEqual(sum(cat["target"] for cat in plan["categories"]), len(plan["records"]))
        self.assertEqual(len({r["id"] for r in plan["records"]}), len(plan["records"]))
        self.assertEqual(len({r["title"] for r in plan["records"]}), len(plan["records"]))
        categories = {cat["id"]: cat["target"] for cat in plan["categories"]}
        for cat, target in categories.items():
            self.assertEqual(sum(r["category"] == cat for r in plan["records"]), target)
        included = [r for r in plan["records"] if r["status"] == "included"]
        planned = [r for r in plan["records"] if r["status"] == "planned"]
        self.assertGreaterEqual(len(included), 15)
        self.assertEqual(len(included) + len(planned), len(plan["records"]))
        self.assertEqual(len(included), len(list((ROOT / "archive/photos").glob("*.jpg"))))
        self.assertEqual({r["asset"] for r in included},
                         {"photos/" + path.name for path in (ROOT / "archive/photos").glob("*.jpg")})
        with ZipFile(self.sample) as package:
            packaged = set(package.namelist())
        for record in included:
            self.assertIn("content/" + record["asset"], packaged)
        for record in planned:
            self.assertIsNone(record["asset"])
        self.assertNotIn("content/images-100.json", packaged)

    def test_real_photographs_stored_with_provenance(self):
        files = sorted((ROOT / "archive/photos").glob("*.jpg"))
        self.assertGreaterEqual(len(files), 15)
        catalog = json.loads((ROOT / "archive/catalog.json").read_text())
        indexed = {item["path"]: item for item in catalog["records"]}
        with ZipFile(self.sample) as package:
            for image in files:
                path = "photos/" + image.name
                contents = image.read_bytes()
                self.assertTrue(contents.startswith(bytes((0xFF, 0xD8))), image.name)
                self.assertGreater(len(contents), 8_000, image.name)
                self.assertEqual(package.read("content/" + path), contents)
                record = indexed[path]
                self.assertTrue(record.get("sources"))
                self.assertTrue(record.get("photographer"))
                self.assertTrue(record["rights"])
                if path == "photos/elodea-leaf.jpg":
                    self.assertIn("CC BY-SA 4.0", record["rights"])

    def test_calibration_raster_is_only_a_test_fixture(self):
        magic, dimensions, maximum, pixels = plate().split(b"\n", 3)
        self.assertEqual((magic, dimensions, maximum), (b"P5", b"1024 1024", b"255"))
        self.assertEqual(len(pixels), 1024**2)
        self.assertEqual((pixels[0], pixels[63], pixels[-1024], pixels[-1]), (0, 255, 0, 255))

    def test_simple_raster_decoding_exercise(self):
        path = ROOT / "archive/primer/raster-example.txt"
        rendered = decode_rows(path.read_text().splitlines())
        self.assertTrue(rendered.startswith(b"P5\n8 8\n255\n"))
        self.assertEqual(len(rendered.split(b"\n", 3)[3]), 64)
        with ZipFile(self.sample) as package:
            self.assertEqual(package.read("content/primer/raster-example.txt"), path.read_bytes())

    def repack(self, mutate):
        with ZipFile(self.sample) as source:
            files = {name: source.read(name) for name in source.namelist()}
        manifest = json.loads(files.pop("manifest.json"))
        mutate(manifest, files)
        altered = self.root / "altered.zip"
        with ZipFile(altered, "w") as result:
            result.writestr("manifest.json", json.dumps(manifest))
            for name, data in files.items():
                result.writestr(name, data)
        return altered

    def test_rejects_invalid_packages(self):
        target = "content/earth/solar-system.txt"
        cases = {
            "format": lambda m, f: m.update(format_version=2),
            "size": lambda m, f: m["files"][0].update(size=False),
            "path": lambda m, f: m["files"][0].update(path="../record"),
            "extra": lambda m, f: f.update(extra=b"x"),
            "missing": lambda m, f: f.pop(target),
            "duplicate record": lambda m, f: m["files"].append(m["files"][0]),
            "malformed digest": lambda m, f: m["files"][0].update(sha256="123"),
        }
        for case, mutate in cases.items():
            with self.subTest(case=case), self.assertRaises(ValueError):
                examine(self.repack(mutate), verify=True)

    def test_digest_and_cli_failure(self):
        def corrupt(manifest, files):
            name = manifest["files"][0]["path"]
            files[name] = b"!" + files[name][1:]
        altered = self.repack(corrupt)
        self.assertEqual(examine(altered), self.manifest)
        result = subprocess.run([sys.executable, ROOT / "tools/archive.py", "verify", altered],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum mismatch", result.stderr)

    def test_duplicate_members(self):
        altered = self.repack(lambda m, f: None)
        with warnings.catch_warnings(), ZipFile(altered, "a") as package:
            warnings.simplefilter("ignore", UserWarning)
            package.writestr("manifest.json", "{}")
        with self.assertRaises(ValueError):
            examine(altered)

    def test_static_site(self):
        site = self.root / "site"
        assemble(site)
        html = (site / "index.html").read_text()
        pages = {}
        for page in site.rglob("*.html"):
            parser = Links()
            parser.feed(page.read_text(encoding="utf-8"))
            pages[page] = parser
        records = json.loads((site / "image-plan.json").read_text())["records"]
        image_targets = {record["asset"] for record in records if record["status"] == "included"}
        image_targets.update(record["id"] for record in records if record["status"] == "included")
        knowledge = json.loads((site / "records/encyclopedia/index.json").read_text())["articles"]
        article_targets = {article["id"] for article in knowledge}
        for page, parser in pages.items():
            for target in parser.targets:
                with self.subTest(page=page.name, target=target):
                    url = urlsplit(target)
                    if url.scheme or url.netloc:
                        continue
                    file = (page.parent / unquote(url.path)).resolve() if url.path else page
                    self.assertTrue(file.is_relative_to(site))
                    self.assertTrue(file.is_file())
                    if url.fragment and file in pages:
                        self.assertIn(unquote(url.fragment), pages[file].anchors)
                    for key, values in parse_qs(url.query).items():
                        if key == "article" and file.name == "encyclopedia.html":
                            self.assertTrue(set(values) <= article_targets)
                        if key == "record" and file.name == "images.html":
                            self.assertTrue(set(values) <= image_targets)
        self.assertNotIn("__EDITION__", html)
        self.assertNotIn("__SIZE__", html)
        self.assertRegex(html, r'<a\b[^>]*href="brief\.html"[^>]*>\s*Read the project brief\b')
        self.assertRegex(html, r'<a\b[^>]*href="#archive"[^>]*>\s*Explore the archive\b')
        self.assertTrue((site / "primer-panel.svg").is_file())
        self.assertTrue((site / "encyclopedia.txt").is_file())
        for name in ("mono-3x5.car", "gray-5x2.car", "rgb-2x3.car"):
            self.assertEqual((site / "downloads/raster-vectors" / name).read_bytes(),
                             (ROOT / "tests/fixtures/photo-raster-v2" / name).read_bytes())
        self.assertTrue((site / "library.html").is_file())
        self.assertTrue((site / "library.js").is_file())
        self.assertTrue((site / "images.html").is_file())
        self.assertIn("photos/earth-apollo17.jpg", (site / "index.html").read_text())
        self.assertTrue((site / "images.js").is_file())
        self.assertTrue((site / "image-plan.json").is_file())
        self.assertEqual((site / "image-plan.json").read_bytes(), (ROOT / "curation/images-100.json").read_bytes())
        image_html = (site / "images.html").read_text()
        image_js = (site / "images.js").read_text()
        self.assertIn('aria-label="Filter by category"', image_html)
        self.assertIn('type="search"', image_html)
        self.assertIn('id="photo-gallery" class="atlas-results"', image_html)
        self.assertIn("matches.map(imageCard)", image_js)
        self.assertIn("atlas-item-placeholder", image_js)
        self.assertIn("if (!slot.asset)", image_js)
        self.assertTrue((site / "decoder.js").is_file())
        self.assertTrue((site / "records/catalog.json").is_file())
        self.assertIn("decoded-grid", (site / "guide.html").read_text())
        self.assertIn("record-details", (site / "library.html").read_text())
        self.assertTrue((site / "guide.html").is_file())
        library = (site / "library.html").read_text()
        self.assertIn("Explore the", library)
        self.assertIn("library.js", library)
        self.assertIn('id="record-nav"', library)
        self.assertIn("What actually goes on the probe?", (site / "guide.html").read_text())
        brief = (site / "brief.html").read_text()
        self.assertIn('href="proposal.html"', brief)
        self.assertNotIn("__EDITION__", brief)
        self.assertTrue({"top", "overview", "archive", "visuals", "decoding", "engineering", "carrier"}
                        <= pages[site / "index.html"].anchors)
        sections = {
            "brief.html": "Project brief",
            "encyclopedia.html": "Encyclopedia",
            "images.html": "Image library",
            "engineering.html": "Decoding and engineering",
        }
        subsection_parents = {
            "proposal.html": "brief.html",
            "library.html": "encyclopedia.html",
            "guide.html": "engineering.html",
            "discovery.html": "engineering.html",
            "vocabulary.html": "engineering.html",
        }
        for name in ("index.html", *sections, *subsection_parents):
            with self.subTest(navigation=name):
                parser = pages[site / name]
                route = "" if name == "index.html" else name.removesuffix(".html")
                self.assertEqual(parser.canonicals, [f"https://westonrosch.com/archive/{route}"])
                self.assertEqual(parser.brand, ("index.html", "page" if name == "index.html" else None))
                self.assertIn("#main", parser.targets)
                self.assertEqual([(href, " ".join("".join(label).split()))
                                  for href, _, label in parser.section_nav], list(sections.items()))
                current = {href: state for href, state, _ in parser.section_nav if state}
                expected = {name: "page"} if name in sections else {}
                if name in subsection_parents:
                    expected = {subsection_parents[name]: "location"}
                self.assertEqual(current, expected)
        style = (site / "style.css").read_text()
        self.assertIn("--bg:#05080f", style)
        self.assertIn("Instrument Serif", style)
        with ZipFile(site / "downloads/centauri.zip") as package:
            self.assertEqual(package.read("manifest.json"), (site / "downloads/manifest.json").read_bytes())
        self.assertEqual(self.sample.read_bytes(), (site / "downloads/centauri.zip").read_bytes())
        for entry in self.manifest["files"]:
            path = entry["path"].removeprefix("content/")
            self.assertEqual((site / "records" / path).read_bytes(), (ROOT / "archive" / path).read_bytes())
