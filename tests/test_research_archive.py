"""Verify independent framing, salvage and the layered specimen."""
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from photo_raster import decode_frame, preview
from research_archive import (
    HEADER, INDEX_ENTRY, LINK_ENTRY, Record, assemble, frame, inspect, inventory,
    pack_table, read_frame, report, sample_records,
)


class ResearchArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = sample_records()
        cls.data = assemble(cls.records)

    def test_uses_real_labeled_records(self):
        result = inspect(self.data)
        self.assertEqual(result["index"], "consistent")
        self.assertEqual(len(result["records"]), 10)
        photo = decode_frame(result["records"][19].payload)
        self.assertEqual((photo.width, photo.height, photo.mode), (32, 32, 24))
        self.assertEqual(len(preview(photo)), 3085)
        self.assertIn(b"CA-03.001", result["records"][301].payload)
        self.assertIn(b"IMG-019", result["records"][502].payload)
        self.assertEqual(self.data, assemble(reversed(self.records)))

    def test_lost_index_and_corrupted_header(self):
        indexless = self.data[:-len(frame(self.records[-1]))]
        self.assertEqual(inspect(indexless)["index"], "missing")
        offset = len(frame(self.records[0]))
        damaged = bytearray(indexless)
        damaged[offset + 12] ^= 1
        with self.assertRaises(ValueError):
            inspect(bytes(damaged))
        salvaged = inspect(b"lead noise" + bytes(damaged), salvage=True)
        self.assertEqual(salvaged["index"], "missing")
        self.assertNotIn(19, salvaged["records"])
        self.assertIn(301, salvaged["records"])
        self.assertEqual(len(salvaged["rejected"]), 1)
        self.assertTrue(salvaged["unresolved_links"])

    def test_index_mismatch_and_conflicting_revisions(self):
        indexless = self.data[:-len(frame(self.records[-1]))]
        stale = Record(506, 10, 1, pack_table(inventory(self.records[1:]), INDEX_ENTRY))
        with self.assertRaises(ValueError):
            inspect(indexless + frame(stale))
        revised = Record(1, 1, 1, b"Different revision.")
        result = inspect(self.data + frame(revised), salvage=True)
        self.assertEqual(result["conflicting_ids"], [1])
        self.assertNotIn(1, result["records"])
        self.assertEqual(result["index"], "inconsistent")

    def test_rejects_invalid_payloads_and_dependencies(self):
        with self.assertRaises(ValueError):
            frame(Record(1, 1, 1, b"\xff"))
        with self.assertRaises(ValueError):
            frame(Record(20, 2, 1, self.records[1].payload))
        item = bytearray(frame(self.records[0]))
        item[7] = 2
        item[-32:] = sha256(item[:-32]).digest()
        with self.assertRaises(ValueError):
            read_frame(item)
        bad_links = Record(100, 8, 1, pack_table([(1, 7, 1)], LINK_ENTRY))
        with self.assertRaises(ValueError):
            assemble([self.records[0], Record(7, 1, 3, b"Later."), bad_links])
        cycle = Record(100, 8, 1, pack_table([(1, 7, 1), (7, 1, 1)], LINK_ENTRY))
        stream = frame(self.records[0]) + frame(Record(7, 1, 1, b"Same layer.")) + frame(cycle)
        with self.assertRaises(ValueError):
            inspect(stream)
        self.assertEqual(inspect(stream, salvage=True)["blocked_prerequisites"], [1, 7])
        self.assertEqual(HEADER.size, 16)

    @unittest.skipUnless(shutil.which("node"), "Independent reader requires Node")
    def test_independent_reader(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "specimen.cax"
            source.write_bytes(self.data)
            command = ["node", str(ROOT / "tools/research_archive_independent.cjs"), str(source)]
            output = json.loads(subprocess.check_output(command))
            expected = report(inspect(self.data))
            for key in ("index", "records"):
                self.assertEqual(output[key], expected[key])
            damaged = bytearray(self.data)
            damaged[-1] ^= 1
            source.write_bytes(damaged)
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
