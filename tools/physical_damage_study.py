"""Measure recovery after seeded, synthetic damage to a small CAEC specimen."""
import argparse
import json
from random import Random
from time import perf_counter

from physical_recovery import (
    MAP_ID, SLOT_BYTES, SYNC, encode_specimen, load_records, recover_specimen, summarize,
)


def _prefix_bits(data, count, rng):
    pad = (-count) % 8
    prefix = rng.getrandbits(count) << (8 * len(data))
    integer = prefix | int.from_bytes(data, "big")
    return (integer << pad).to_bytes(len(data) + (count + pad) // 8, "big")


def _edit_slot(data, slot, offset, size, rng):
    changed = bytearray(data)
    start = slot * SLOT_BYTES + offset
    for index in range(start, start + size):
        changed[index] ^= rng.randrange(1, 256)
    return bytes(changed)


def _without_slots(data, slots):
    omit = set(slots)
    return b"".join(data[i:i + SLOT_BYTES] for i in range(0, len(data), SLOT_BYTES)
                    if i // SLOT_BYTES not in omit)


def run_study(records, seed=20261124, include_timing=False, *, target_id=19, logical_index_id=None):
    """Return exact record comparisons and coordinates suitable for rendering."""
    rng = Random(seed)
    started = perf_counter()
    original = encode_specimen(records)
    packing_ms = (perf_counter() - started) * 1_000
    clean = recover_specimen([original])
    before = clean.scans[0].slots
    map_slots = [slot for slot in before if slot.block.record_id == MAP_ID]
    data_slots = [slot for slot in before if slot.block.record_id != MAP_ID]
    map_half = len(map_slots) // 2
    map_length = map_half * SLOT_BYTES

    target_id = target_id if target_id in records else data_slots[0].block.record_id
    target_slots = [slot.bit_offset // (8 * SLOT_BYTES) for slot in data_slots
                    if slot.block.record_id == target_id]
    first, *remaining = target_slots
    no_first_data = _without_slots(original, (first,))
    marker_missing = _edit_slot(original, first, 0, len(SYNC), rng)
    # Separate loss of one sync token from corruption of data, header and parity.
    damaged = _edit_slot(original, first, 0, len(SYNC) // 2, rng)
    damaged = _edit_slot(damaged, first, len(SYNC), 8, rng)
    damaged = _edit_slot(damaged, first, SLOT_BYTES - 8, 7, rng)
    scratch = _edit_slot(original, first, len(SYNC) + 12, 48, rng)
    without_map = original[map_length:-map_length]
    insert_at = (first + 1) * SLOT_BYTES
    insertion = original[:insert_at] + b"\xff\x19\x0a\x81\x07\x63\x01" + original[insert_at:]

    # Prefer complementary losses within one record when it spans multiple slots.
    complement = _without_slots(damaged, (*range(map_half), *remaining[:1]))
    cases = {
        "clean": [original],
        "unknown_bit_phase": [_prefix_bits(original, 13, rng)],
        "inserted_bytes": [_prefix_bits(insertion, 3, rng)],
        "three_bit_slip_between_slots": [original[:insert_at] + _prefix_bits(original[insert_at:], 3, rng)],
        "one_sync_token_and_15_code_symbols_corrupted": [damaged],
        "both_sync_tokens_corrupted": [marker_missing],
        "48_symbol_scratch": [scratch],
        "one_slot_deleted": [_prefix_bits(no_first_data, 6, rng)],
        "both_map_bookends_missing": [_prefix_bits(without_map, 3, rng)],
        "complementary_copy_damage": [_prefix_bits(no_first_data, 5, rng),
                                      _prefix_bits(complement, 2, rng)],
        "same_slot_lost_in_both_copies": [no_first_data, marker_missing],
        "third_copy_supplies_missing_slot": [no_first_data, marker_missing, complement],
        "28_symbol_aligned_tail_truncation": [original[:-28]],
    }
    if logical_index_id in records and logical_index_id != target_id:
        missing_index_slots = [slot.bit_offset // (8 * SLOT_BYTES) for slot in data_slots
                               if slot.block.record_id == logical_index_id]
        cases["logical_index_missing"] = [_without_slots(original, missing_index_slots)]
    results = {}
    for name, copies in cases.items():
        started = perf_counter()
        recovered = recover_specimen(copies)
        elapsed_ms = (perf_counter() - started) * 1_000
        summary = summarize(recovered)
        summary["logical_bytes_recovered"] = sum(map(len, recovered.records.values()))
        if logical_index_id in records:
            summary["logical_index_recovered"] = logical_index_id in recovered.records
        summary["incorrect_accepted_ids"] = [
            record_id for record_id, data in recovered.records.items() if records.get(record_id) != data
        ]
        summary["slots_after"] = [
            [
                {"bit_offset": slot.bit_offset, "id": slot.block.record_id, "index": slot.block.index,
                 "role": "map" if slot.block.record_id == MAP_ID else "record",
                 "markers": slot.intact_markers, "corrected_symbols": len(slot.block.changed_positions)}
                for slot in scan.slots
            ]
            for scan in recovered.scans
        ]
        if include_timing:
            summary["recovery_ms"] = round(elapsed_ms, 3)
        results[name] = summary
    logical_bytes = sum(map(len, records.values()))
    output = {
        "schema_version": 1,
        "seed": seed,
        "slot_bytes": SLOT_BYTES,
        "damage_target_id": target_id,
        "logical_bytes": logical_bytes,
        "one_copy_bytes": len(original),
        "two_copy_bytes": 2 * len(original),
        "three_copy_bytes": 3 * len(original),
        "overhead_per_copy_bytes": len(original) - logical_bytes,
        "sync_bytes_per_copy": len(before) * len(SYNC),
        "physical_map_bytes_per_copy": len(map_slots) * SLOT_BYTES,
        "slots_before": [
            {"bit_offset": slot.bit_offset, "id": slot.block.record_id, "index": slot.block.index,
             "role": "map" if slot.block.record_id == MAP_ID else "record"}
            for slot in before
        ],
        "cases": results,
    }
    if include_timing:
        output["packing_ms"] = round(packing_ms, 3)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", nargs="*", metavar="ID=PATH")
    parser.add_argument("--seed", type=int, default=20261124)
    parser.add_argument("--timing", action="store_true", help="include non-deterministic wall-clock measurements")
    args = parser.parse_args()
    try:
        if args.records:
            result = run_study(load_records(args.records), args.seed, args.timing)
        else:
            from research_archive import frame, sample_records
            sample = sample_records()
            records = {record.id: frame(record) for record in sample}
            index_id = next((record.id for record in sample if record.kind == 10), None)
            result = run_study(records, args.seed, args.timing, logical_index_id=index_id)
    except (ValueError, OSError) as error:
        parser.exit(1, f"physical damage study: {error}\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(any(case["incorrect_accepted_ids"] for case in result["cases"].values()))


if __name__ == "__main__":
    raise SystemExit(main())
