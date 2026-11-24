"""Verify canonical site images, source provenance, and protected reconstruction."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from photo_raster import archive_selections, inspect, read_frame
from protect_archive import BLOCK_PAYLOAD, RS_TOTAL, read_slots, recover_record

EXHIBIT = ROOT / "website/photo-reconstruction"


class PhotoExhibitTests(unittest.TestCase):
    def test_canonical_files_and_provenance(self):
        manifest = json.loads((EXHIBIT / "manifest.json").read_text(encoding="utf-8"))
        identifiers = {record["id"] for record in manifest["records"]}
        self.assertEqual(identifiers, {"IMG-019", "IMG-036", "IMG-050", "IMG-073", "IMG-011"})
        sources = {item[0]: item[1:] for item in archive_selections(identifiers)}
        expected = {"manifest.json", manifest["protection"]["file"]}
        for record in manifest["records"]:
            source, _, catalog = sources[record["id"]]
            self.assertEqual(record["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(record["rights"], catalog["rights"])
            self.assertEqual(record["credit"], catalog["photographer"])
            self.assertEqual(record["sources"], catalog["sources"])
            for variant in record["variants"]:
                name = variant["file"]
                self.assertNotIn(name, expected)
                expected.add(name)
                path = EXHIBIT / name
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), variant["sha256"])
                frame = read_frame(path)
                self.assertEqual(frame.record_id, int(record["id"][4:]))
                self.assertEqual(inspect(frame), {key: variant[key] for key in inspect(frame)})
                self.assertEqual(max(frame.width, frame.height), variant["edge"])
        self.assertEqual({path.name for path in EXHIBIT.iterdir()}, expected)
        self.assertEqual(len(expected), 50)

    def test_protected_sample_recovers_to_verified_pixels(self):
        header = json.loads((EXHIBIT / "manifest.json").read_text(encoding="utf-8"))["protection"]
        protected = EXHIBIT / header["file"]
        raster = (EXHIBIT / header["raw"]).read_bytes()
        slots = list(read_slots(protected))
        self.assertEqual(header["block_count"], len(slots))
        self.assertEqual(header["payload_bytes_per_block"], BLOCK_PAYLOAD)
        self.assertEqual(header["encoded_bytes"], len(slots) * RS_TOTAL)
        self.assertEqual(header["raw_bytes"], len(raster))
        self.assertEqual(hashlib.sha256(protected.read_bytes()).hexdigest(), header["sha256"])
        damaged = bytearray(slots[0])
        for position in (0, 24, 56, 80, 223, 254):
            damaged[position] ^= 0x20
        slots[0] = damaged
        self.assertEqual(recover_record(header["record_id"], slots, hashlib.sha256(raster).digest()), raster)

    @unittest.skipUnless(shutil.which("node"), "browser decoder conformance needs Node.js")
    def test_browser_decoder_conformance(self):
        result = subprocess.run(["node", ROOT / "tests/photo_exhibit.cjs"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("48 frames", result.stdout)
