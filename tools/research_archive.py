"""Build and inspect Centauri's experimental CAX1 logical record stream."""
import argparse
from collections import deque
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from struct import Struct
from tempfile import NamedTemporaryFile

from archive import ROOT
from photo_raster import decode_frame

SYNC = b"\xca\x1c\x66\x2a"
HEADER = Struct(">4sBBBBII")
INDEX_ENTRY = Struct(">IBBI")
LINK_ENTRY = Struct(">IIB")
COUNT = Struct(">I")
MAX_PAYLOAD = 16 * 1024 * 1024
MAX_STREAM = 128 * 1024 * 1024
TYPE = {
    1: "mathematics", 2: "photograph", 3: "diagram", 4: "vocabulary",
    5: "article", 6: "reference", 7: "attribution", 8: "relationships",
    9: "recovery", 10: "index", 11: "specification",
}
TEXT_TYPES = {1, 3, 4, 5, 6, 7, 9, 11}
ROLE = {1: "prerequisite", 2: "illustrates", 3: "credited-by", 4: "cites", 5: "related"}


@dataclass(frozen=True)
class Record:
    id: int
    kind: int
    layer: int
    payload: bytes


def read_table(data, entry):
    if len(data) < COUNT.size:
        raise ValueError("truncated table")
    count = COUNT.unpack_from(data)[0]
    if len(data) != COUNT.size + count * entry.size:
        raise ValueError("invalid table length")
    return list(entry.iter_unpack(data[COUNT.size:]))


def pack_table(rows, entry):
    return COUNT.pack(len(rows)) + b"".join(entry.pack(*row) for row in rows)


def validate(record):
    if (not 1 <= record.id < 0xFFFFFFFF or record.kind not in TYPE
            or not 0 <= record.layer <= 5 or not 0 < len(record.payload) <= MAX_PAYLOAD):
        raise ValueError("invalid record ID, type, layer or length")
    if record.kind in TEXT_TYPES:
        text = record.payload.decode("utf-8")
        if "\x00" in text or not text.strip(" \t\n\v\f\r"):
            raise ValueError("empty text or NUL in text record")
    elif record.kind == 2:
        if decode_frame(record.payload).record_id != record.id:
            raise ValueError("CAR record ID differs from frame ID")
    elif record.kind == 8:
        rows = read_table(record.payload, LINK_ENTRY)
        if rows != sorted(set(rows)) or any(
            not 1 <= source < 0xFFFFFFFF or not 1 <= target < 0xFFFFFFFF or source == target or role not in ROLE
            for source, target, role in rows
        ):
            raise ValueError("invalid or unordered relationship")
    elif record.kind == 10:
        rows = read_table(record.payload, INDEX_ENTRY)
        if [row[0] for row in rows] != sorted({row[0] for row in rows}) or any(
            not 1 <= number < 0xFFFFFFFF or kind not in TYPE or kind == 10
            or not 0 <= layer <= 5 or not 0 < length <= MAX_PAYLOAD
            for number, kind, layer, length in rows
        ):
            raise ValueError("invalid or unordered index")


def frame(record):
    validate(record)
    body = HEADER.pack(SYNC, 1, record.kind, record.layer, 0, record.id, len(record.payload)) + record.payload
    return body + sha256(body).digest()


def read_frame(data, offset=0):
    if offset < 0 or len(data) - offset < HEADER.size:
        raise ValueError("truncated header")
    sync, version, kind, layer, flags, number, length = HEADER.unpack_from(data, offset)
    if sync != SYNC or version != 1 or flags:
        raise ValueError("unrecognized frame signature, version or flags")
    start = offset + HEADER.size
    end = start + length
    if not 0 < length <= MAX_PAYLOAD or end + 32 > len(data):
        raise ValueError("invalid or truncated payload")
    if sha256(memoryview(data)[offset:end]).digest() != data[end:end + 32]:
        raise ValueError("frame digest mismatch")
    record = Record(number, kind, layer, data[start:end])
    validate(record)
    return record, end + 32


def inventory(records):
    return sorted((record.id, record.kind, record.layer, len(record.payload))
                  for record in records if record.kind != 10)


def assemble(records):
    ordered = sorted(records, key=lambda record: record.id)
    packed = b"".join(map(frame, ordered))
    inspect(packed)
    return packed


def inspect(data, salvage=False):
    if not data or len(data) > MAX_STREAM:
        raise ValueError("empty stream or reference-reader stream limit exceeded")
    found, rejected, conflicts = {}, [], set()
    offset = 0
    while offset < len(data):
        start = data.find(SYNC, offset) if salvage else offset
        if start < 0:
            break
        try:
            record, offset = read_frame(data, start)
        except ValueError as error:
            if not salvage:
                raise
            rejected.append((start, str(error)))
            offset = start + 1
            continue
        if record.id in found:
            if not salvage:
                raise ValueError("duplicate record ID")
            if found[record.id] != record:
                conflicts.add(record.id)
        else:
            if not salvage and found and record.id <= next(reversed(found)):
                raise ValueError("record IDs must ascend")
            found[record.id] = record
    for number in conflicts:
        del found[number]
    indexes = [record for record in found.values() if record.kind == 10]
    index_status = "missing"
    if indexes:
        index_status = "consistent" if len(indexes) == 1 and read_table(
            indexes[0].payload, INDEX_ENTRY
        ) == inventory(found.values()) else "inconsistent"
    unresolved, invalid = [], []
    prerequisites = {number: set() for number in found}
    dependents = {number: set() for number in found}
    for record in found.values():
        if record.kind == 8:
            for source, target, role in read_table(record.payload, LINK_ENTRY):
                if source not in found or target not in found:
                    unresolved.append((source, target, role))
                elif role == 1:
                    if found[target].layer > found[source].layer:
                        invalid.append((source, target, role))
                    else:
                        prerequisites[source].add(target)
                        dependents[target].add(source)
    ready = deque(number for number, dependencies in prerequisites.items() if not dependencies)
    while ready:
        number = ready.popleft()
        for later in dependents[number]:
            prerequisites[later].remove(number)
            if not prerequisites[later]:
                ready.append(later)
    blocked = sorted(number for number, dependencies in prerequisites.items() if dependencies)
    if not salvage and (index_status == "inconsistent" or unresolved or invalid or blocked):
        raise ValueError("index or relationships disagree with the record stream")
    return dict(records=dict(sorted(found.items())), index=index_status, rejected=rejected,
                conflicting_ids=sorted(conflicts), unresolved_links=unresolved,
                invalid_links=invalid, blocked_prerequisites=blocked)


def sample_records():
    root = ROOT / "archive"
    encyclopedia = json.loads((root / "encyclopedia/index.json").read_text(encoding="utf-8"))
    earth = next(item for item in encyclopedia["articles"] if item["id"] == "CA-03.001")
    vocab = json.loads((root / "vocabulary/index.json").read_text(encoding="utf-8"))
    term = next(item for item in vocab["entries"] if item["id"] == "V-004")
    catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    photo = next(item for item in catalog["records"] if item["path"] == "photos/earth-apollo17.jpg")
    source_credit = "\n".join(
        [f"{photo['title']} · IMG-019", photo["photographer"], photo["rights"]]
        + [source["url"] for source in photo["sources"]]
    )
    rows = [(101, 19, 2), (301, 1, 1), (301, 101, 1), (301, 501, 4), (19, 502, 3)]
    records = [
        Record(1, 1, 1, (root / "primer/mathematics.txt").read_bytes()),
        Record(19, 2, 1, (ROOT / "website/photo-reconstruction/img-019-e32-rgb.car").read_bytes()),
        Record(101, 4, 2, ("V-004 · " + term["label"] + "\n" + term["ambiguity"]).encode()),
        Record(301, 5, 3, ("\n\n".join(
            [earth["id"] + " · " + earth["title"], *earth["body"], earth["limitations"], earth["status"]]
        )).encode()),
        Record(501, 6, 3, "\n".join(source["label"] + " · " + source["url"] for source in earth["sources"]).encode()),
        Record(502, 7, 1, source_credit.encode()),
        Record(503, 8, 1, pack_table(sorted(rows), LINK_ENTRY)),
        Record(504, 9, 1, b"Use separate protected slots. Verify each CAX record before interpreting it. The index is a consistency witness when present."),
        Record(505, 11, 1, (ROOT / "docs/research-archive-format.md").read_bytes()),
    ]
    return records + [Record(506, 10, 1, pack_table(inventory(records), INDEX_ENTRY))]


def report(result):
    return {**result, "records": [
        dict(id=r.id, type=TYPE[r.kind], kind=r.kind, layer=r.layer, bytes=len(r.payload),
             sha256=sha256(r.payload).hexdigest()) for r in result["records"].values()
    ]}


def write_output(path, data):
    if path.resolve().is_relative_to(ROOT / "archive"):
        raise ValueError("write experiment output outside the archive source collection")
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        temporary.write_bytes(data)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    sample = commands.add_parser("sample", help="build the demonstration record stream")
    sample.add_argument("output", type=Path)
    read = commands.add_parser("inspect", help="verify and inventory a stream")
    read.add_argument("input", type=Path)
    read.add_argument("--salvage", action="store_true")
    read.add_argument("--extract", type=int, metavar="ID")
    read.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "sample":
            write_output(args.output, assemble(sample_records()))
            return
        with args.input.open("rb") as source:
            result = inspect(source.read(MAX_STREAM + 1), args.salvage)
        if (args.extract is None) != (args.output is None):
            raise ValueError("--extract and --output must be supplied together")
        if args.extract is not None:
            if args.extract not in result["records"]:
                raise ValueError("record does not exist or could not be verified")
            write_output(args.output, result["records"][args.extract].payload)
        print(json.dumps(report(result), indent=2))
    except (OSError, ValueError) as error:
        parser.exit(1, f"research archive: {error}\n")


if __name__ == "__main__":
    main()
