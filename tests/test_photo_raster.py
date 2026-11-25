"""Interoperability, malformed frames, and real photograph tests for raster v2."""
import hashlib
from importlib.util import find_spec
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/photo-raster-v2"
CLI = ROOT / "tools/photo_raster.py"
NODE = ROOT / "tools/photo_raster_independent.cjs"
sys.path.insert(0, str(ROOT / "tools"))

from photo_raster import (DEMO_IDS, MODE_NAMES, OVERHEAD, Raster, batch,
                          collection_budget, decode_frame, encode_frame, preview)


VECTORS = {
    "mono-3x5": (Raster(0xFFFF0001, 3, 5, 1, bytes.fromhex("96b0")),
                 b"P5\n3 5\n255\n" + bytes(bit * 255 for bit in (
                     1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0))),
    "gray-5x2": (Raster(0xFFFF0002, 5, 2, 8, bytes.fromhex("00 20 80 ff c0 10 50 70 e0 30")),
                 b"P5\n5 2\n255\n" + bytes((0, 32, 128, 255, 192, 16, 80, 112, 224, 48))),
    "rgb-2x3": (Raster(0xFFFF0003, 2, 3, 24, bytes.fromhex("ff0000 008000 2040ff 10a020 ffffff 384060")),
                b"P6\n2 3\n255\n" + bytes((255, 0, 0, 0, 128, 0, 32, 64, 255,
                                         16, 160, 32, 255, 255, 255, 56, 64, 96))),
}


class PhotoRasterTests(unittest.TestCase):
    def test_fixed_vectors(self):
        for name, (raster, expected) in VECTORS.items():
            with self.subTest(name=name):
                encoded = (FIXTURES / f"{name}.car").read_bytes()
                self.assertEqual(encode_frame(raster), encoded)
                self.assertEqual(decode_frame(encoded), raster)
                self.assertEqual(preview(decode_frame(encoded)), expected)

    @unittest.skipUnless(shutil.which("node"), "independent decoder needs Node.js")
    def test_independent_node_decoder(self):
        for name, (_, expected) in VECTORS.items():
            with self.subTest(name=name):
                encoded = FIXTURES / f"{name}.car"
                result = subprocess.run(["node", NODE, encoded], capture_output=True, check=True)
                self.assertEqual(result.stdout, expected)
                with TemporaryDirectory() as temp:
                    malformed = Path(temp) / "corrupt.car"
                    damaged = bytearray(encoded.read_bytes())
                    damaged[22] ^= 0x80
                    malformed.write_bytes(damaged)
                    failed = subprocess.run(["node", NODE, malformed], capture_output=True)
                    self.assertEqual(failed.returncode, 1)
                    self.assertFalse(failed.stdout)

    def test_rejects_each_single_bit_error(self):
        for name in VECTORS:
            encoded = (FIXTURES / f"{name}.car").read_bytes()
            for offset in range(len(encoded)):
                for bit in range(8):
                    with self.subTest(name=name, offset=offset, bit=bit):
                        damaged = bytearray(encoded)
                        damaged[offset] ^= 1 << bit
                        with self.assertRaises(ValueError):
                            decode_frame(damaged)

    def test_rejects_malformed_frames_even_when_digest_matches(self):
        good = (FIXTURES / "mono-3x5.car").read_bytes()
        for candidate in (b"", good[:-1], good + b"x"):
            with self.subTest(size=len(candidate)), self.assertRaises(ValueError):
                decode_frame(candidate)
        for offset, value in ((8, b"\x01"), (9, b"\x04"), (10, b"\x00\x00"),
                              (10, b"\x10\x01\x10\x01"), (14, b"\x00" * 4),
                              (18, b"\x00\x00\x00\x01"), (23, b"\xb1")):
            body = good[:offset] + value + good[offset + len(value):-32]
            invalid = body + hashlib.sha256(body).digest()
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                decode_frame(invalid)

    def test_rejects_invalid_encoder_fields(self):
        for raster in (Raster(0, 1, 1, 8, b"K"), Raster(2**32, 1, 1, 8, b"K"),
                       Raster(1, 0, 1, 8, b"K"), Raster(1, 1, 1, 7, b"K"),
                       Raster(1, 2, 1, 8, b"K"), Raster(1, 1, 1, 1, b"K")):
            with self.subTest(raster=raster), self.assertRaises(ValueError):
                encode_frame(raster)

    def test_cli_failure_leaves_output_untouched(self):
        with TemporaryDirectory() as temp:
            source = Path(temp) / "invalid.car"
            source.write_bytes(b"short")
            destination = Path(temp) / "existing.pgm"
            destination.write_bytes(b"keep")
            result = subprocess.run([sys.executable, CLI, "decode", source, destination],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("truncated", result.stderr)
            self.assertEqual(destination.read_bytes(), b"keep")

    @unittest.skipUnless(find_spec("PIL"), "photo preparation needs Pillow")
    def test_real_photo_batch_roundtrip_and_calculated_capacity(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            first = directory / "first"
            second = directory / "second"
            manifest = batch(first, DEMO_IDS, 64, [1, 8, 24])
            batch(second, tuple(reversed(DEMO_IDS)), 64, [1, 8, 24])
            self.assertEqual(sorted(file.name for file in first.iterdir()),
                             sorted(file.name for file in second.iterdir()))
            for file in first.iterdir():
                with self.subTest(file=file):
                    self.assertEqual(file.read_bytes(), (second / file.name).read_bytes())
            self.assertEqual([record["id"] for record in manifest["records"]], list(DEMO_IDS))
            totals = dict.fromkeys(MODE_NAMES.values(), 0)
            for record in manifest["records"]:
                source = ROOT / "archive" / record["source"]["asset"]
                self.assertEqual(record["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
                self.assertTrue(record["catalog"]["rights"])
                self.assertTrue(record["catalog"]["sources"])
                for item in record["derivatives"]:
                    path = first / item["path"]
                    encoded = path.read_bytes()
                    self.assertEqual(len(encoded), item["payload_bytes"] + OVERHEAD)
                    self.assertEqual(hashlib.sha256(encoded).hexdigest(), item["sha256"])
                    recovered = decode_frame(encoded)
                    self.assertEqual(recovered.record_id, int(record["id"][4:]))
                    self.assertEqual(max(recovered.width, recovered.height), 64)
                    self.assertEqual(encode_frame(recovered), encoded)
                    totals[item["mode"]] += len(encoded)
                    if shutil.which("node"):
                        result = subprocess.run(["node", NODE, path], capture_output=True, check=True)
                        self.assertEqual(result.stdout, preview(recovered))
            budget = collection_budget(DEMO_IDS, [64])
            self.assertEqual(budget["photos"], len(DEMO_IDS))
            self.assertEqual(budget["scenarios"], [{"max_edge": 64, "frame_bytes": totals}])

    @unittest.skipUnless(find_spec("PIL"), "photo preparation needs Pillow")
    def test_encoder_sample_values_and_inspector(self):
        from PIL import Image

        with TemporaryDirectory() as temp:
            source = Path(temp) / "known.png"
            file = Path(temp) / "known.car"
            image = Image.new("RGB", (3, 2))
            image.putdata([(255, 0, 0), (0, 255, 0), (0, 0, 255),
                           (128, 128, 128), (0, 0, 0), (255, 255, 255)])
            image.save(source)
            subprocess.run([sys.executable, CLI, "encode", source, file, "--mode", "gray",
                            "--record-id", "999"], check=True)
            result = subprocess.run([sys.executable, CLI, "inspect", file],
                                    capture_output=True, text=True, check=True)
            self.assertIn('"record_id": 999', result.stdout)
            self.assertEqual(decode_frame(file.read_bytes()).payload, bytes((76, 150, 29, 128, 0, 255)))
