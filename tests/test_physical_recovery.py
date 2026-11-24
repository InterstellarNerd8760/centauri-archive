"""Recovery tests for unsynchronized readouts and damaged archive copies."""
from hashlib import sha256
from pathlib import Path
from random import Random
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from physical_damage_study import _prefix_bits, _without_slots, run_study
from physical_recovery import (
    MAP_ENTRY, MAP_HEADER, MAP_ID, MAP_MAGIC, MAX_CANDIDATES, MAX_RECORD_BYTES, MAX_STREAM_BYTES,
    SLOT_BYTES, SYNC, SYNC_A, encode_specimen, parse_slot_map, recover_specimen, scan_readout,
)
from protect_archive import BLOCK_PAYLOAD, protect_record
from research_archive import frame, inspect, sample_records


def physical_words(record_id, data):
    return b"".join(SYNC + block for block in protect_record(record_id, data))


class PhysicalRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.records = {19: Random(19).randbytes(300), 90: b"example", 510: b"label"}
        self.specimen = encode_specimen(self.records)
        self.clean = recover_specimen([self.specimen])

    def slot_numbers(self, record_id):
        return [slot.bit_offset // (8 * SLOT_BYTES) for slot in self.clean.scans[0].slots
                if slot.block.record_id == record_id]

    def test_deterministic_map_and_round_trip_every_bit_phase(self):
        self.assertEqual(self.specimen, encode_specimen(dict(reversed(list(self.records.items())))))
        self.assertEqual(self.clean.records, self.records)
        self.assertTrue(self.clean.complete)
        placement = [(entry.record_id, entry.length, entry.first_slot) for entry in self.clean.map_entries]
        self.assertEqual(placement, [(19, 300, 2), (90, 7, 5), (510, 5, 6)])
        for phase in range(8):
            offset = 32 + phase
            readout = _prefix_bits(self.specimen, offset, Random(7))
            result = recover_specimen([readout])
            self.assertEqual(result.scans[0].slots[0].bit_offset, offset)
            self.assertEqual(result.records, self.records)

    def test_sync_loss_parity_damage_and_resynchronization(self):
        start = self.slot_numbers(19)[1] * SLOT_BYTES
        word_start = start + len(SYNC)
        damaged = bytearray(self.specimen)
        for index in [*range(start, start + len(SYNC_A)), word_start, word_start + 5, start + SLOT_BYTES - 1]:
            damaged[index] ^= 0x55
        result = recover_specimen([bytes(damaged)])
        slot = next(slot for slot in result.scans[0].slots if slot.bit_offset == start * 8)
        self.assertEqual(slot.intact_markers, 1)
        self.assertEqual(len(slot.block.changed_positions), 3)
        self.assertEqual(result.records, self.records)
        recovered_after_insertion = recover_specimen([self.specimen[:start] + b"abc" + self.specimen[start:]])
        self.assertTrue(recovered_after_insertion.complete)
        self.assertEqual(recovered_after_insertion.records, self.records)

    def test_deliberate_misleading_markers_and_partial_leading_marker(self):
        source = b"prefix" + SYNC * 3 + self.specimen[len(SYNC_A):]
        result = recover_specimen([source])
        self.assertEqual(result.records, self.records)
        self.assertGreater(result.scans[0].candidates, len(result.scans[0].slots))
        with_partial = recover_specimen([self.specimen[len(SYNC_A):]])
        self.assertEqual(with_partial.scans[0].slots[0].bit_offset, -8 * len(SYNC_A))
        self.assertTrue(with_partial.complete)

    def test_missing_map_preserves_verified_records_without_claiming_coverage(self):
        lost = _without_slots(self.specimen, self.slot_numbers(MAP_ID))
        result = recover_specimen([lost])
        self.assertEqual(result.map_status, "missing")
        self.assertFalse(result.complete)
        self.assertEqual(result.records, self.records)

    def test_complementary_copies_require_assembly(self):
        first, second = self.slot_numbers(19)[:2]
        damaged_a = _without_slots(self.specimen, [first])
        damaged_b = _without_slots(self.specimen, [second])
        for damaged in (damaged_a, damaged_b):
            result = recover_specimen([damaged])
            self.assertEqual(result.missing_ids, (19,))
            self.assertNotIn(19, result.records)
            self.assertFalse(result.complete)
        repaired = recover_specimen([_prefix_bits(damaged_a, 3, Random(0)),
                                     _prefix_bits(damaged_b, 5, Random(0))])
        self.assertEqual(repaired.records, self.records)
        self.assertTrue(repaired.complete)

    def test_conflicting_valid_maps_and_unindexed_revision(self):
        revised = {**self.records, 19: b"other photo"}
        result = recover_specimen([self.specimen, encode_specimen(revised)])
        self.assertEqual(result.map_status, "conflict")
        self.assertEqual(set(result.records), {90, 510})
        self.assertIn(19, result.failures)
        self.assertFalse(result.complete)
        result = recover_specimen([self.specimen, physical_words(19, revised[19])])
        self.assertEqual(result.records, self.records)
        self.assertTrue(result.complete)

    def test_valid_map_digest_with_wrong_length_does_not_claim_completeness(self):
        record = b"lengths"
        bogus = MAP_HEADER.pack(MAP_MAGIC, 1, 1) + MAP_ENTRY.pack(1, 1, sha256(record).digest(), 1)
        result = recover_specimen([physical_words(MAP_ID, bogus) + physical_words(1, record)])
        self.assertEqual(result.map_status, "verified")
        self.assertEqual(result.missing_ids, (1,))
        self.assertIn("length", result.failures[1])

    def test_rejects_oversized_specimen_map_and_input(self):
        with self.assertRaises(ValueError):
            encode_specimen({MAP_ID: b"reserved"})
        with self.assertRaises(ValueError):
            encode_specimen({1: bytes(MAX_RECORD_BYTES + 1)})
        with self.assertRaises(ValueError):
            encode_specimen({1: bytes(MAX_RECORD_BYTES), 2: bytes(MAX_RECORD_BYTES), 3: bytes(MAX_RECORD_BYTES)})
        with self.assertRaises(ValueError):
            scan_readout(bytes(MAX_STREAM_BYTES + 1))
        with self.assertRaisesRegex(ValueError, "candidate limit"):
            scan_readout(SYNC_A * (MAX_CANDIDATES + 1))
        with self.assertRaises(ValueError):
            parse_slot_map(MAP_HEADER.pack(MAP_MAGIC, 1, 1) +
                           MAP_ENTRY.pack(1, 10 * BLOCK_PAYLOAD, bytes(32), 0))
        with self.assertRaises(ValueError):
            recover_specimen([])
        self.assertFalse(recover_specimen([b"noise"]).complete)

    def test_cli_partial_recovery_never_writes_missing_ids(self):
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            lost = self.slot_numbers(19)
            readout = directory / "input.cas"
            readout.write_bytes(_without_slots(self.specimen, lost))
            output = directory / "output"
            result = subprocess.run([sys.executable, ROOT / "tools/physical_recovery.py", "recover",
                                     output, readout], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse((output / "19.bin").exists())
            self.assertEqual((output / "90.bin").read_bytes(), self.records[90])

    def test_integrated_cax_recovery_and_missing_logical_index(self):
        records = {record.id: frame(record) for record in sample_records()}
        specimen = encode_specimen(records)
        actual = recover_specimen([_prefix_bits(specimen, 9, Random(2))])
        self.assertEqual(actual.records, records)
        logical = inspect(b"".join(actual.records.values()))
        self.assertEqual(logical["index"], "consistent")
        self.assertEqual(logical["records"][19].kind, 2)
        study = run_study(records, logical_index_id=506)
        self.assertEqual(study["damage_target_id"], 19)
        cases = study["cases"]
        self.assertEqual(cases["same_slot_lost_in_both_copies"]["missing_ids"], [19])
        self.assertTrue(cases["complementary_copy_damage"]["complete"])
        self.assertTrue(cases["third_copy_supplies_missing_slot"]["complete"])
        self.assertTrue(cases["three_bit_slip_between_slots"]["complete"])
        self.assertEqual(cases["logical_index_missing"]["missing_ids"], [506])
        self.assertFalse(cases["logical_index_missing"]["logical_index_recovered"])
        self.assertEqual(cases["both_map_bookends_missing"]["map_status"], "missing")
        self.assertEqual(cases["both_map_bookends_missing"]["logical_bytes_recovered"], study["logical_bytes"])
        self.assertTrue(all(not case["incorrect_accepted_ids"] for case in cases.values()))


if __name__ == "__main__":
    unittest.main()
