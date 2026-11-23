"""Regression and independent-vector checks for the experimental raw raster."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from raw_raster import SYNC, encode_frame, decode_frame, grayscale_pgm, read_text_grid


class RawRasterTests(unittest.TestCase):
    def setUp(self):
        self.width, self.height, self.bits = read_text_grid(ROOT / "archive/primer/raster-example.txt")

    def test_published_fixed_vector(self):
        self.assertEqual((self.width, self.height), (8, 8))
        encoded = encode_frame(self.width, self.height, self.bits)
        golden = bytes.fromhex(
            "ff00ff0000ff00ff0100080008"
            "10387cfe18181801"
            "efc78301e7e7e7fe"
        )
        self.assertEqual(encoded, golden)
        self.assertEqual(decode_frame(golden), (8, 8, self.bits))
        self.assertEqual(grayscale_pgm(*decode_frame(golden)),
                         b"P5\n8 8\n255\n" + bytes(value * 255 for value in self.bits))

    def test_independently_parsed_frame(self):
        # Deliberately reconstruct with the publicly documented byte offsets,
        # without calling the production decoder.
        frame = encode_frame(self.width, self.height, self.bits)
        self.assertEqual(frame[:8], SYNC)
        self.assertEqual(frame[8], 1)
        width = (frame[9] << 8) + frame[10]
        height = (frame[11] << 8) + frame[12]
        payload = frame[13:13 + (width * height + 7) // 8]
        recovered = tuple((payload[i // 8] >> (7 - i % 8)) & 1
                          for i in range(width * height))
        self.assertEqual((width, height, recovered), (8, 8, self.bits))

    def test_detects_invalid_inputs_and_corruption(self):
        frame = encode_frame(self.width, self.height, self.bits)
        bad = [
            frame[:-1],
            frame + b"\0",
            b"\0" + frame[1:],
            frame[:8] + b"\2" + frame[9:],
            frame[:9] + b"\0\0" + frame[11:],
        ]
        altered = bytearray(frame)
        altered[13] ^= 0x10
        bad.append(bytes(altered))
        for candidate in bad:
            with self.subTest(candidate=candidate[:15].hex()), self.assertRaises(ValueError):
                decode_frame(candidate)

    def test_tail_padding_is_zero_and_checked(self):
        bits = (1, 0, 1, 0, 1, 0, 1, 0, 1)
        encoded = encode_frame(3, 3, bits)
        self.assertEqual(decode_frame(encoded), (3, 3, bits))
        damaged = bytearray(encoded)
        damaged[14] |= 1
        damaged[-1] &= 0xFE  # keep the inverted twin superficially consistent
        with self.assertRaises(ValueError):
            decode_frame(bytes(damaged))

    def test_reject_bad_dimensions_and_non_binary_values(self):
        for args in ((0, 8, ()), (1025, 1, ()), (2, 2, (0, 1)),
                     (2, 2, (0, 1, 2, 1))):
            with self.subTest(args=args), self.assertRaises(ValueError):
                encode_frame(*args)

    def test_cli_encode_decode(self):
        with tempfile.TemporaryDirectory() as temp:
            encoded = Path(temp) / "frame.bin"
            preview = Path(temp) / "preview.pgm"
            for command, source, target in (
                ("encode", ROOT / "archive/primer/raster-example.txt", encoded),
                ("decode", encoded, preview),
            ):
                result = subprocess.run(
                    [sys.executable, ROOT / "tools/raw_raster.py",
                     command, source, target],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(preview.read_bytes(),
                             grayscale_pgm(self.width, self.height, self.bits))


if __name__ == "__main__":
    unittest.main()
