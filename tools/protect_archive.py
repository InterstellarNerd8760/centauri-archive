"""Protect one numbered archive record or recover it from aligned block copies."""
import argparse
from dataclasses import dataclass
from hashlib import sha256
from itertools import chain
from pathlib import Path
from struct import Struct
from tempfile import NamedTemporaryFile

from error_correction import RS_DATA, RS_TOTAL, Uncorrectable, rs_encode, rs_repair


HEADER = Struct(">4sBIIIQ")
MAGIC = b"CAEC"
VERSION = 1
DIGEST_LENGTH = 32
BLOCK_PAYLOAD = RS_DATA - HEADER.size - 2 * DIGEST_LENGTH


@dataclass(frozen=True)
class Block:
    record_id: int
    index: int
    count: int
    length: int
    record_digest: bytes
    payload: bytes
    changed_positions: tuple[int, ...]


def block_count(length):
    if type(length) is not int or length < 0:
        raise ValueError("record length must be a nonnegative integer")
    return max(1, (length + BLOCK_PAYLOAD - 1) // BLOCK_PAYLOAD)


def encoded_size(length, copies=1):
    if type(copies) is not int or copies < 1:
        raise ValueError("copy count must be a positive integer")
    return block_count(length) * RS_TOTAL * copies


def protect_record(record_id, data):
    """Yield independent protected blocks in ascending zero-based order."""
    if type(record_id) is not int or not 0 < record_id < 2**32:
        raise ValueError("record ID must be a positive unsigned 32-bit integer")
    count = block_count(len(data))
    if count >= 2**32:
        raise ValueError("record has too many blocks")
    digest = sha256(data).digest()
    for index in range(count):
        chunk = data[index * BLOCK_PAYLOAD : (index + 1) * BLOCK_PAYLOAD]
        header = HEADER.pack(MAGIC, VERSION, record_id, index, count, len(data))
        contents = header + digest + chunk.ljust(BLOCK_PAYLOAD, b"\0")
        yield rs_encode(contents + sha256(contents).digest())


def decode_block(word, erasures=()):
    """Correct one block and validate its metadata, payload, padding and digest."""
    if len(word) > RS_TOTAL:
        raise Uncorrectable("protected block exceeds slot size")
    if len(word) < RS_TOTAL:
        # An aligned short block at the end of a copy has lost a known suffix.
        erasures = (*erasures, *range(len(word), RS_TOTAL))
        word = bytes(word).ljust(RS_TOTAL, b"\0")
    repaired, changed = rs_repair(word, erasures)
    contents = repaired[: RS_DATA - DIGEST_LENGTH]
    if sha256(contents).digest() != repaired[RS_DATA - DIGEST_LENGTH : RS_DATA]:
        raise Uncorrectable("protected block SHA-256 mismatch")
    magic, version, record_id, index, count, length = HEADER.unpack_from(contents)
    if (magic, version) != (MAGIC, VERSION) or record_id == 0:
        raise Uncorrectable("unknown protected block format or invalid record ID")
    if count != block_count(length) or index >= count:
        raise Uncorrectable("inconsistent protected block dimensions")
    start = HEADER.size + DIGEST_LENGTH
    used = min(BLOCK_PAYLOAD, length - index * BLOCK_PAYLOAD)
    if any(contents[start + used :]):
        raise Uncorrectable("nonzero padding in protected block")
    return Block(record_id, index, count, length, contents[HEADER.size : start],
                 contents[start : start + used], changed)


def recover_record(record_id, words, expected_digest=None):
    """Recover a complete record from an iterable of aligned blocks or missing slots.

    An independently trusted expected_digest (32 raw bytes) can select an
    intended revision. Invalid blocks are skipped. Conflicting valid blocks
    for the same revision or record ID cause rejection.
    """
    if type(record_id) is not int or not 0 < record_id < 2**32:
        raise ValueError("record ID must be a positive unsigned 32-bit integer")
    if expected_digest is not None and len(expected_digest) != DIGEST_LENGTH:
        raise ValueError("expected digest must be 32 bytes")
    chunks, identity = {}, None
    for word in words:
        if word is None:
            continue
        try:
            block = decode_block(word)
        except Uncorrectable:
            continue
        if block.record_id != record_id:
            continue
        if expected_digest is not None and block.record_digest != expected_digest:
            continue
        observed = (block.count, block.length, block.record_digest)
        if identity is None:
            identity = observed
        if observed != identity or chunks.get(block.index, block.payload) != block.payload:
            raise Uncorrectable("conflicting verified blocks for record")
        chunks[block.index] = block.payload
    if identity is None:
        raise Uncorrectable("no verified blocks for record")
    count, length, digest = identity
    if len(chunks) != count:
        raise Uncorrectable(f"incomplete record: {len(chunks)} of {count} verified blocks")
    data = b"".join(chunks[index] for index in range(count))
    if len(data) != length or sha256(data).digest() != digest:
        raise Uncorrectable("reassembled record length or SHA-256 mismatch")
    return data


def interleave(words):
    """Lay out a known group of complete codewords column-first by byte."""
    words = tuple(words)
    if not words or any(len(word) != RS_TOTAL for word in words):
        raise ValueError("interleave requires complete codewords")
    return bytes(value for column in zip(*words) for value in column)


def deinterleave(data, depth):
    """Restore a complete interleaved group with externally supplied depth."""
    if type(depth) is not int or depth < 1 or len(data) != RS_TOTAL * depth:
        raise ValueError("incorrect interleave depth or incomplete group")
    return tuple(data[offset::depth] for offset in range(depth))


def read_slots(path):
    with path.open("rb") as source:
        while word := source.read(RS_TOTAL):
            yield word


def write_output(path, chunks):
    with NamedTemporaryFile(dir=path.parent, delete=False) as temp:
        staging = Path(temp.name)
    try:
        with staging.open("wb") as target:
            target.writelines(chunks)
        staging.replace(path)
    finally:
        staging.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    pack = commands.add_parser("pack", help="write one sequential protected copy")
    pack.add_argument("record_id", type=int)
    pack.add_argument("input", type=Path)
    pack.add_argument("output", type=Path)
    recover = commands.add_parser("recover", help="combine one or more fixed-slot copies")
    recover.add_argument("record_id", type=int)
    recover.add_argument("output", type=Path)
    recover.add_argument("copies", type=Path, nargs="+")
    recover.add_argument("--sha256", help="trusted hex-encoded digest of the intended record")
    try:
        args = parser.parse_args()
        if args.command == "pack":
            chunks = protect_record(args.record_id, args.input.read_bytes())
        else:
            expected = bytes.fromhex(args.sha256) if args.sha256 else None
            words = chain.from_iterable(map(read_slots, args.copies))
            chunks = (recover_record(args.record_id, words, expected),)
        write_output(args.output, chunks)
    except (ValueError, OSError) as error:
        parser.exit(1, f"archive protection: {error}\n")


if __name__ == "__main__":
    main()
