import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import warnings
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from archive import build, examine
from build_site import assemble
from html.parser import HTMLParser


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []
        self.anchors = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.anchors.add(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.targets.append(attrs[key])


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
        self.assertTrue(1_000_000 <= second.stat().st_size <= 10_000_000)
        self.assertEqual(examine(second, verify=True), self.manifest)

    def test_raster_decoding(self):
        with ZipFile(self.sample) as package:
            magic, dimensions, maximum, pixels = package.read("content/primer/plate.pgm").split(b"\n", 3)
        self.assertEqual((magic, dimensions, maximum), (b"P5", b"1024 1024", b"255"))
        self.assertEqual(len(pixels), 1024**2)
        self.assertEqual((pixels[0], pixels[63], pixels[-1024], pixels[-1]), (0, 255, 0, 255))

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
        target = "content/earth/shadow.txt"
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
        parser = Links()
        parser.feed(html)
        for target in parser.targets:
            if target.startswith("#"):
                self.assertIn(target[1:], parser.anchors)
            elif not target.startswith("https://"):
                self.assertTrue((site / target).is_file(), target)
        self.assertNotIn("__EDITION__", html)
        self.assertIn("1.05 MB", html)
        with ZipFile(site / "downloads/centauri.zip") as package:
            self.assertEqual(package.read("manifest.json"), (site / "downloads/manifest.json").read_bytes())
        self.assertEqual(self.sample.read_bytes(), (site / "downloads/centauri.zip").read_bytes())
