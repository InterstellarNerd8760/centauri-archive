"""Encode and recover a small, self-indexing CAEC readout specimen."""
import argparse
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from struct import Struct

from error_correction import RS_TOTAL, Uncorrectable
from protect_archive import Block, assemble_record, block_count, decode_block, protect_record, write_output


SYNC_A = bytes.fromhex("d392e7ac15804bf9")
SYNC_B = bytes.fromhex("2e6cb017f8439da5")
SYNC = SYNC_A + SYNC_B
SLOT_BYTES = len(SYNC) + RS_TOTAL
MAP_ID = 2**32 - 1
MAP_MAGIC = b"CASM"
VERSION = 1
MAP_HEADER = Struct(">4sBH")
MAP_ENTRY = Struct(">IQ32sI")
MAX_RECORD_BYTES = 500_000
MAX_STREAM_BYTES = 2 * 1024 * 1024
MAX_RECORDS = 128
MAX_COPIES = 8
MAX_CANDIDATES = 8192


@dataclass(frozen=True)
class MapEntry:
    record_id: int
    length: int
    digest: bytes
    first_slot: int


@dataclass(frozen=True)
class SlotObservation:
    bit_offset: int
    block: Block
    intact_markers: int


@dataclass(frozen=True)
class Scan:
    input_bytes: int
    candidates: int
    slots: tuple[SlotObservation, ...]


@dataclass(frozen=True)
class Recovery:
    records: dict[int, bytes]
    missing_ids: tuple[int, ...]
    map_status: str
    map_entries: tuple[MapEntry, ...]
    failures: dict[int, str]
    scans: tuple[Scan, ...]

    @property
    def complete(self):
        return self.map_status == "verified" and not self.missing_ids


def _valid_size(length):
    return 0 <= length <= MAX_RECORD_BYTES


def _map_bytes(entries):
    return MAP_HEADER.pack(MAP_MAGIC, VERSION, len(entries)) + b"".join(
        MAP_ENTRY.pack(entry.record_id, entry.length, entry.digest, entry.first_slot)
        for entry in entries
    )


def parse_slot_map(data):
    if len(data) < MAP_HEADER.size:
        raise ValueError("incomplete physical slot map header")
    magic, version, count = MAP_HEADER.unpack_from(data)
    if (magic, version) != (MAP_MAGIC, VERSION) or not 1 <= count <= MAX_RECORDS:
        raise ValueError("unsupported physical slot map or record count")
    if len(data) != MAP_HEADER.size + count * MAP_ENTRY.size:
        raise ValueError("incorrect physical slot map length")
    map_blocks = block_count(len(data))
    next_slot, last_id = map_blocks, 0
    entries = []
    for fields in MAP_ENTRY.iter_unpack(data[MAP_HEADER.size:]):
        entry = MapEntry(*fields)
        if not last_id < entry.record_id < MAP_ID:
            raise ValueError("slot-map IDs must be ordered, unique and positive")
        if not _valid_size(entry.length) or entry.first_slot != next_slot:
            raise ValueError("invalid record length or slot offset")
        entries.append(entry)
        last_id = entry.record_id
        next_slot += block_count(entry.length)
    if (next_slot + map_blocks) * SLOT_BYTES > MAX_STREAM_BYTES:
        raise ValueError("slot map exceeds specimen size limit")
    return tuple(entries)


def encode_specimen(records: Mapping[int, bytes]) -> bytes:
    """Encode one copy with protected catalog bookends and stable slot ordering."""
    if not 1 <= len(records) <= MAX_RECORDS:
        raise ValueError(f"specimen needs 1 to {MAX_RECORDS} records")
    for record_id, data in records.items():
        if type(record_id) is not int or not 0 < record_id < MAP_ID:
            raise ValueError("invalid or reserved physical specimen record ID")
        if not isinstance(data, bytes) or not _valid_size(len(data)):
            raise ValueError(f"specimen record must contain at most {MAX_RECORD_BYTES} bytes")

    map_blocks = block_count(MAP_HEADER.size + len(records) * MAP_ENTRY.size)
    next_slot = map_blocks
    entries = []
    for record_id, data in sorted(records.items()):
        entries.append(MapEntry(record_id, len(data), sha256(data).digest(), next_slot))
        next_slot += block_count(len(data))
    if (next_slot + map_blocks) * SLOT_BYTES > MAX_STREAM_BYTES:
        raise ValueError("encoded specimen exceeds byte limit")

    layout = tuple(SYNC + word for word in protect_record(MAP_ID, _map_bytes(entries)))
    contents = (SYNC + word for entry in entries
                for word in protect_record(entry.record_id, records[entry.record_id]))
    return b"".join((*layout, *contents, *layout))


def _phase_streams(data):
    yield 0, data
    if len(data) < len(SYNC_A) + 1:
        return
    integer = int.from_bytes(data, "big")
    mask = (1 << (8 * len(data))) - 1
    for phase in range(1, 8):
        shifted = ((integer << phase) & mask).to_bytes(len(data), "big")
        yield phase, shifted[:-1]


def _marker_positions(data, marker):
    offset = data.find(marker)
    while offset >= 0:
        yield offset
        offset = data.find(marker, offset + 1)


def scan_readout(data: bytes) -> Scan:
    """Search every bit phase and validate a CAEC word at each unique sync hit."""
    if not isinstance(data, bytes) or len(data) > MAX_STREAM_BYTES:
        raise ValueError("readout must be bytes within the specimen stream limit")
    observations, candidates = [], 0
    for phase, aligned in _phase_streams(data):
        starts = set()
        for marker, displacement in ((SYNC_A, 0), (SYNC_B, len(SYNC_A))):
            for hit in _marker_positions(aligned, marker):
                # If the readout begins within the first token, the second
                # token can still locate an intact word at a negative slot start.
                start = hit - displacement
                if start not in starts:
                    starts.add(start)
                    if candidates + len(starts) > MAX_CANDIDATES:
                        raise ValueError("specimen candidate limit exceeded")
        candidates += len(starts)
        for start in sorted(starts):
            word_start = start + len(SYNC)
            word = aligned[word_start : word_start + RS_TOTAL]
            try:
                block = decode_block(word)
            except Uncorrectable:
                continue
            limit = (MAP_HEADER.size + MAX_RECORDS * MAP_ENTRY.size
                     if block.record_id == MAP_ID else MAX_RECORD_BYTES)
            if block.length > limit:
                continue
            both = start >= 0 and aligned[start:word_start] == SYNC
            observations.append(SlotObservation(start * 8 + phase, block, 2 if both else 1))
    return Scan(len(data), candidates, tuple(sorted(observations, key=lambda slot: slot.bit_offset)))


def _recover_map(blocks):
    by_digest = defaultdict(list)
    for block in blocks:
        by_digest[block.record_digest].append(block)
    candidates = []
    for digest, group in by_digest.items():
        try:
            record = assemble_record(MAP_ID, group, digest)
            candidates.append(parse_slot_map(record))
        except ValueError:
            continue
    if len(candidates) == 1:
        return "verified", candidates[0]
    return ("conflict" if len(candidates) > 1 else "missing"), ()


def recover_specimen(copies: Sequence[bytes]) -> Recovery:
    """Join verified blocks across copies and report whether coverage is known."""
    if not 1 <= len(copies) <= MAX_COPIES:
        raise ValueError(f"recovery needs 1 to {MAX_COPIES} readouts")
    scans = tuple(scan_readout(data) for data in copies)
    blocks = defaultdict(list)
    for scan in scans:
        for slot in scan.slots:
            blocks[slot.block.record_id].append(slot.block)
    map_status, entries = _recover_map(blocks.pop(MAP_ID, ()))
    expected = {entry.record_id: entry for entry in entries}
    ids = expected if map_status == "verified" else blocks
    records, failures = {}, {}
    for record_id in sorted(ids):
        entry = expected.get(record_id)
        try:
            record = assemble_record(
                record_id, blocks.get(record_id, ()), entry.digest if entry else None
            )
            if entry and len(record) != entry.length:
                raise Uncorrectable("record length differs from verified slot map")
            records[record_id] = record
        except Uncorrectable as error:
            failures[record_id] = str(error)
    missing = tuple(record_id for record_id in expected if record_id not in records)
    return Recovery(records, missing, map_status, entries, failures, scans)


def summarize(recovery):
    return {
        "map_status": recovery.map_status,
        "complete": recovery.complete,
        "records": [
            {"record_id": record_id, "bytes": len(data), "sha256": sha256(data).hexdigest()}
            for record_id, data in recovery.records.items()
        ],
        "missing_ids": list(recovery.missing_ids),
        "failures": recovery.failures,
        "readouts": [
            {"bytes": scan.input_bytes, "candidates": scan.candidates, "verified_slots": len(scan.slots)}
            for scan in recovery.scans
        ],
    }


def read_bounded(path, limit):
    with path.open("rb") as source:
        data = source.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"{path} exceeds the {limit}-byte specimen limit")
    return data


def load_records(specifications):
    records = {}
    if len(specifications) > MAX_RECORDS:
        raise ValueError("too many specimen records")
    slots = 2 * block_count(MAP_HEADER.size + len(specifications) * MAP_ENTRY.size)
    for item in specifications:
        key, path = item.split("=", 1)
        record_id = int(key)
        if record_id in records:
            raise ValueError(f"duplicate record ID {record_id}")
        record = read_bounded(Path(path), MAX_RECORD_BYTES)
        slots += block_count(len(record))
        if slots * SLOT_BYTES > MAX_STREAM_BYTES:
            raise ValueError("encoded specimen exceeds byte limit")
        records[record_id] = record
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    pack = commands.add_parser("pack", help="write one specimen copy")
    pack.add_argument("output", type=Path)
    pack.add_argument("records", nargs="+", metavar="ID=PATH")
    sample = commands.add_parser("sample", help="encode the mixed CAX1 research specimen")
    sample.add_argument("output", type=Path)
    recover = commands.add_parser("recover", help="extract verified records and report coverage")
    recover.add_argument("output_directory", type=Path)
    recover.add_argument("copies", nargs="+", type=Path)
    args = parser.parse_args()
    try:
        if args.command in ("pack", "sample"):
            if args.command == "sample":
                from research_archive import frame, sample_records
                records = {record.id: frame(record) for record in sample_records()}
            else:
                records = load_records(args.records)
            specimen = encode_specimen(records)
            write_output(args.output, (specimen,))
            return 0
        if len(args.copies) > MAX_COPIES:
            raise ValueError("too many copies")
        result = recover_specimen([read_bounded(copy, MAX_STREAM_BYTES) for copy in args.copies])
        args.output_directory.mkdir(parents=True)
        for record_id, contents in result.records.items():
            write_output(args.output_directory / f"{record_id}.bin", (contents,))
        print(json.dumps(summarize(result), indent=2, sort_keys=True))
        return 0 if result.complete else 2
    except (ValueError, OSError) as error:
        parser.exit(1, f"physical recovery: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
