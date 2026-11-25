"""Run seeded archive-damage experiments on four protected blocks."""
import argparse
import json
from random import Random
from time import perf_counter

from error_correction import RS_DATA, RS_TOTAL, Uncorrectable, rs_encode, rs_repair
from protect_archive import deinterleave, encoded_size, interleave, protect_record, recover_record


RECORD_ID = 42
LOGICAL_BYTES = 500


def _flip(word, positions, rng):
    changed = bytearray(word)
    for position in positions:
        changed[position] ^= rng.randrange(1, 256)
    return bytes(changed)


def _flip_random_bits(word, rng):
    changed = bytearray(word)
    for position in rng.sample(range(len(changed)), 12):
        changed[position] ^= 1 << rng.randrange(8)
    return bytes(changed)


def _force_miscorrection(word):
    """Place a word 16 symbols from another codeword and 17 from its original."""
    changed_message = bytearray(word[:RS_DATA])
    changed_message[-1] ^= 1
    alternate = rs_encode(changed_message)
    differences = [i for i, (a, b) in enumerate(zip(word, alternate)) if a != b]
    assert len(differences) == 33
    damaged = bytearray(word)
    for i in differences[:17]:
        damaged[i] = alternate[i]
    return bytes(damaged)


def damage_cases(words, rng):
    offset = rng.randrange(RS_TOTAL - 48 + 1)
    burst = range(offset, offset + 48)
    laid_out = interleave(words)
    start = rng.randrange(len(laid_out) - 48 + 1)
    lost = (words[0], None, *words[2:])
    complementary = (None, words[1], None, words[3])
    changed_first_copy = _flip(words[0], rng.sample(range(RS_TOTAL), 12), rng)
    changed_second_copy = _flip(words[1], rng.sample(range(RS_TOTAL), 12), rng)
    deliberate = _force_miscorrection(words[0])
    return {
        "clean": words,
        "random_bit_flips": tuple(_flip_random_bits(word, rng) for word in words),
        "burst_48_symbols_single_block": (_flip(words[0], burst, rng), *words[1:]),
        "burst_48_symbols_interleaved": deinterleave(
            _flip(laid_out, range(start, start + 48), rng), len(words)
        ),
        "missing_block": lost,
        "corrupted_metadata": (_flip(words[0], (0, 4, 6, 9, 14, 20, 24), rng), *words[1:]),
        "corrupted_correction_symbols": (
            _flip(words[0], range(RS_DATA, RS_DATA + 16), rng), *words[1:]
        ),
        "truncation_20_known_tail_symbols": (*words[:3], words[3][:-20]),
        "truncation_40_known_tail_symbols": (*words[:3], words[3][:-40]),
        "exceeds_correction_budget": (_flip(words[0], rng.sample(range(RS_TOTAL), 17), rng), *words[1:]),
        "false_codeword_with_stale_digest": (deliberate, *words[1:]),
        "complementary_damage_across_copies": (
            changed_first_copy, *lost[1:], complementary[0], changed_second_copy, *complementary[2:]
        ),
        "same_block_missing_across_copies": lost + lost,
    }


def run(seed=20261124, trials=20):
    rng = Random(seed)
    observations = {}
    pack_seconds = 0.0
    rejected_miscorrections = 0
    for _ in range(trials):
        original = rng.randbytes(LOGICAL_BYTES)
        start = perf_counter()
        words = tuple(protect_record(RECORD_ID, original))
        pack_seconds += perf_counter() - start
        for name, observed in damage_cases(words, rng).items():
            copies = len(observed) // len(words)
            storage = encoded_size(LOGICAL_BYTES, copies)
            row = observations.setdefault(name, dict(
                recovered=0, detected_unrecoverable=0, undetected_or_miscorrected=0,
                correction_guard_rejections=0, recovery_ms=0.0, stored_bytes=storage,
                overhead_bytes=storage - LOGICAL_BYTES,
            ))
            start = perf_counter()
            try:
                result = recover_record(RECORD_ID, observed)
            except Uncorrectable:
                row["detected_unrecoverable"] += 1
            else:
                category = "recovered" if result == original else "undetected_or_miscorrected"
                row[category] += 1
            row["recovery_ms"] += (perf_counter() - start) * 1_000
            if name == "false_codeword_with_stale_digest":
                bad_candidate, _ = rs_repair(observed[0])
                if bad_candidate != words[0]:
                    rejected_miscorrections += 1
                    row["correction_guard_rejections"] += 1

    for row in observations.values():
        row["recovery_ms"] = round(row["recovery_ms"], 3)
    return dict(seed=seed, trials_per_case=trials, logical_bytes=LOGICAL_BYTES,
                packing_ms=round(pack_seconds * 1_000, 3), cases=observations,
                alternate_rs_codewords_rejected_at_integrity_layer=rejected_miscorrections)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261124)
    parser.add_argument("--trials", type=int, default=20)
    args = parser.parse_args()
    if args.trials < 1:
        parser.error("trials must be positive")
    report = run(args.seed, args.trials)
    print(json.dumps(report, indent=2))
    return int(any(row["undetected_or_miscorrected"] for row in report["cases"].values()))


if __name__ == "__main__":
    raise SystemExit(main())
