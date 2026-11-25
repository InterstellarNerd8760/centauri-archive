"""Executable guarantees and bounds for the correction prototypes."""
from hashlib import sha256
from itertools import combinations
from pathlib import Path
from random import Random
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from error_correction import (
    RS_DATA, RS_TOTAL, Uncorrectable, hamming_decode, hamming_encode, rs_encode, rs_repair,
)
from protect_archive import (
    BLOCK_PAYLOAD, decode_block, deinterleave, encoded_size, interleave, protect_record, recover_record,
)
from simulate_archive_damage import _force_miscorrection, run


def flipped(word, *positions):
    altered = list(word)
    for position in positions:
        altered[position - 1] ^= 1
    return altered


class HammingTests(unittest.TestCase):
    def test_fixed_vector_and_all_single_and_double_errors(self):
        self.assertEqual(hamming_encode(11), (0, 1, 1, 0, 0, 1, 1, 0))
        for value in range(16):
            word = hamming_encode(value)
            self.assertEqual(hamming_decode(word).value, value)
            for position in range(1, 9):
                result = hamming_decode(flipped(word, position))
                self.assertEqual((result.value, result.codeword, result.corrected_position),
                                 (value, word, position))
            for left, right in combinations(range(1, 9), 2):
                with self.assertRaises(Uncorrectable):
                    hamming_decode(flipped(word, left, right))

    def test_beyond_guarantee_and_bad_inputs(self):
        word = hamming_encode(0)
        result = hamming_decode(flipped(word, 1, 2, 3))
        self.assertNotEqual(result.value, 0)
        self.assertEqual(result.corrected_position, 8)
        result = hamming_decode(flipped(word, 1, 2, 3, 8))
        self.assertNotEqual(result.value, 0)
        self.assertIsNone(result.corrected_position)
        with self.assertRaises(ValueError):
            hamming_encode(16)
        with self.assertRaises(ValueError):
            hamming_decode((0, 0, 2, 0, 0, 0, 0, 0))


class ReedSolomonTests(unittest.TestCase):
    def test_independent_fixed_vector_and_every_codeword_position(self):
        data = bytes(range(RS_DATA))
        # Cross-checked against reedsolo 1.7.0 RSCodec(32, fcr=0, prim=0x11d).
        parity = bytes.fromhex("41841183b11fdb537421939696cda70e1db5c86684af222564b89cc6069f172e")
        word = data + parity
        self.assertEqual(rs_encode(data), word)
        self.assertEqual(rs_repair(word), (word, ()))
        for position in range(RS_TOTAL):
            altered = bytearray(word)
            altered[position] ^= 0x95
            self.assertEqual(rs_repair(altered), (word, (position,)))

    def test_all_mix_counts_within_guarantee(self):
        rng = Random(251901)
        word = rs_encode(rng.randbytes(RS_DATA))
        for erasures in range(33):
            for errors in range((32 - erasures) // 2 + 1):
                positions = rng.sample(range(RS_TOTAL), erasures + errors)
                altered = bytearray(word)
                for position in positions:
                    altered[position] ^= rng.randrange(1, 256)
                with self.subTest(erasures=erasures, errors=errors):
                    self.assertEqual(rs_repair(altered, positions[:erasures]),
                                     (word, tuple(sorted(positions))))
        self.assertEqual(rs_repair(word, (0, 1)), (word, ()))
        with self.assertRaises(Uncorrectable):
            rs_repair(word, range(33))
        with self.assertRaises(ValueError):
            rs_repair(word, (1, 1))
        with self.assertRaises(ValueError):
            rs_repair(word[:-1])


class ProtectedRecordTests(unittest.TestCase):
    def setUp(self):
        self.content = Random(7).randbytes(500)
        self.words = tuple(protect_record(42, self.content))

    def test_record_round_trip_and_capacity(self):
        self.assertEqual(BLOCK_PAYLOAD, 134)
        self.assertEqual(encoded_size(0), 255)
        self.assertEqual(encoded_size(134), 255)
        self.assertEqual(encoded_size(135, 2), 1020)
        self.assertEqual(encoded_size(len(self.content)), 1020)
        fixed_word = next(protect_record(42, b"abc"))
        self.assertEqual(sha256(fixed_word).hexdigest(),
                         "388faca5a53ac82dd657cf0395e6fdcd25aa244a43a8cad38f4bea210e261562")
        self.assertEqual(recover_record(42, reversed(self.words)), self.content)
        self.assertEqual(recover_record(42, protect_record(42, b"")), b"")
        with self.assertRaises(ValueError):
            encoded_size(1, 0)

    def test_block_metadata_integrity_and_recovery_with_erasure_information(self):
        altered = bytearray(self.words[0])
        altered[24] ^= 16
        altered[RS_DATA] ^= 32
        altered[-28:] = bytes(28)
        result = decode_block(altered, range(RS_TOTAL - 28, RS_TOTAL))
        self.assertEqual((result.record_id, result.index, result.count, result.length),
                         (42, 0, 4, len(self.content)))
        self.assertEqual(result.payload, self.content[:BLOCK_PAYLOAD])
        self.assertIn(24, result.changed_positions)
        self.assertIn(RS_DATA, result.changed_positions)
        self.assertEqual(decode_block(self.words[0][:-32]).payload, result.payload)
        with self.assertRaises(Uncorrectable):
            decode_block(self.words[0][:-33])

    def test_malformed_metadata_and_padding_rejected_after_valid_ecc_and_hash(self):
        word = self.words[-1]
        for position in (4, 8, 12, 16, 24, 190):
            body = bytearray(word[:RS_DATA - 32])
            if position == 8:
                body[5:9] = bytes(4)
            else:
                body[position] ^= 0x80
            invalid = rs_encode(body + sha256(body).digest())
            with self.subTest(position=position), self.assertRaises(Uncorrectable):
                decode_block(invalid)

    def test_alternate_valid_codeword_is_rejected_after_miscorrection(self):
        deliberate = _force_miscorrection(self.words[0])
        candidate, _ = rs_repair(deliberate)
        self.assertNotEqual(candidate, self.words[0])
        with self.assertRaisesRegex(Uncorrectable, "SHA-256"):
            decode_block(deliberate)
        with self.assertRaises(Uncorrectable):
            recover_record(42, (deliberate, *self.words[1:]))

    def test_incomplete_conflicting_and_complementary_copies(self):
        copy_a = (self.words[0], None, *self.words[2:])
        copy_b = (None, self.words[1], None, self.words[3])
        for copy in (copy_a, copy_b):
            with self.assertRaisesRegex(Uncorrectable, "incomplete"):
                recover_record(42, copy)
        self.assertEqual(recover_record(42, copy_a + copy_b), self.content)
        alternate = tuple(protect_record(42, b"different revision"))
        with self.assertRaisesRegex(Uncorrectable, "conflicting"):
            recover_record(42, self.words + alternate)
        self.assertEqual(recover_record(42, self.words + alternate, sha256(self.content).digest()),
                         self.content)

    def test_interleaved_layout(self):
        transmitted = interleave(self.words)
        self.assertEqual(transmitted[:4], bytes(word[0] for word in self.words))
        self.assertEqual(deinterleave(transmitted, 4), self.words)
        with self.assertRaises(ValueError):
            deinterleave(transmitted[:-1], 4)

    def test_cli_round_trip_and_failed_recovery_leaves_output_intact(self):
        cli = ROOT / "tools/protect_archive.py"
        with TemporaryDirectory() as temp:
            original, packed, recovered = [Path(temp) / name for name in ("input", "pack", "recovered")]
            original.write_bytes(self.content)
            subprocess.run([sys.executable, cli, "pack", "42", original, packed], check=True)
            self.assertEqual(packed.read_bytes(), b"".join(self.words))
            subprocess.run([sys.executable, cli, "recover", "42", recovered, packed, "--sha256",
                            sha256(self.content).hexdigest()], check=True)
            self.assertEqual(recovered.read_bytes(), self.content)
            packed.write_bytes(packed.read_bytes()[:-33])
            result = subprocess.run([sys.executable, cli, "recover", "42", recovered, packed],
                                    capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(recovered.read_bytes(), self.content)

    def test_seeded_damage_outcomes(self):
        report = run(seed=20261124, trials=2)
        success = {"clean", "random_bit_flips", "burst_48_symbols_interleaved", "corrupted_metadata",
                   "corrupted_correction_symbols", "truncation_20_known_tail_symbols",
                   "complementary_damage_across_copies"}
        self.assertEqual(len(report["cases"]), 13)
        for name, row in report["cases"].items():
            self.assertEqual(row["undetected_or_miscorrected"], 0)
            self.assertEqual(row["recovered"], 2 if name in success else 0)
            self.assertEqual(row["detected_unrecoverable"], 0 if name in success else 2)
        self.assertEqual(report["alternate_rs_codewords_rejected_at_integrity_layer"], 2)


if __name__ == "__main__":
    unittest.main()
