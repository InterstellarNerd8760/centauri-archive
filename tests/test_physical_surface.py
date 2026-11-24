"""Verify surface coordinates and the integrated scratch study."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from physical_surface import Surface, measure


class PhysicalSurfaceTests(unittest.TestCase):
    def test_calibration_rows_and_multiple_planes(self):
        surface = Surface(8, 4, 1, planes=2, primer_rows=1)
        self.assertEqual(surface.usable_bits, 48)
        self.assertEqual(surface.sample(bytes([255]) * 6, [(0, 0, 0, 8, 2), (1, 4, 2, 4, 1)]),
                         (bytes([0, 255, 255, 255, 240, 255]), 12))
        with self.assertRaises(ValueError):
            surface.sample(bytes(7))
        with self.assertRaises(ValueError):
            surface.sample(bytes(6), [(0, 7, 1, 2, 1)])

    def test_integrated_scratch_recovery(self):
        outcome = measure(Surface(40_000, 40_000, 80))
        self.assertEqual(outcome["records_before"], 10)
        self.assertEqual(outcome["combined_records"], 10)
        self.assertGreater(outcome["changed_sample_bits"], 0)
        self.assertLess(outcome["records_after"], 10)
        self.assertEqual(outcome["incorrect_accepted"], 0)
