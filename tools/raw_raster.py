"""Experimental byte-framed binary raster independent of ZIP, JSON and JPEG.

This is a software interoperability experiment, NOT a demonstrated universal
or extraterrestrial-decodable format. A physical primer still must teach bits,
reading direction, width/height, units, contrast and file boundaries.
"""
import argparse
from pathlib import Path

SYNC = bytes.fromhex("ff00ff0000ff00ff")
VERSION = 1
HEADER_BYTES = 13
MAX_SIDE = 1024


def encode_frame(width, height, pixels):
    """Pack row-major monochrome pixels, most-significant bit first."""
    if (type(width) is not int or type(height) is not int
            or not (1 <= width <= MAX_SIDE and 1 <= height <= MAX_SIDE)):
        raise ValueError("invalid image dimensions")
    if len(pixels) != width * height:
        raise ValueError("pixel count does not match dimensions")
    packed = bytearray((width * height + 7) // 8)
    for index, pixel in enumerate(pixels):
        if pixel not in (0, 1):
            raise ValueError("pixels must be binary values")
        if pixel:
            packed[index // 8] |= 1 << (7 - (index % 8))
    inverse = bytes(value ^ 0xFF for value in packed)
    return (SYNC + bytes((VERSION,)) + width.to_bytes(2, "big")
            + height.to_bytes(2, "big") + bytes(packed) + inverse)


def decode_frame(data):
    """Return (width, height, tuple of bits) or reject a malformed frame."""
    if len(data) < HEADER_BYTES or data[:8] != SYNC:
        raise ValueError("missing experimental sync pattern")
    if data[8] != VERSION:
        raise ValueError("unsupported experimental frame version")
    width, height = int.from_bytes(data[9:11], "big"), int.from_bytes(data[11:13], "big")
    if not (1 <= width <= MAX_SIDE and 1 <= height <= MAX_SIDE):
        raise ValueError("invalid raster dimensions")
    count = width * height
    nbytes = (count + 7) // 8
    if len(data) != HEADER_BYTES + nbytes * 2:
        raise ValueError("wrong frame length")
    values = data[HEADER_BYTES:HEADER_BYTES + nbytes]
    inverse = data[HEADER_BYTES + nbytes:]
    if any((a ^ b) != 0xFF for a, b in zip(values, inverse)):
        raise ValueError("data and inverted copy disagree")
    if count % 8 and values[-1] & ((1 << (8 - count % 8)) - 1):
        raise ValueError("nonzero tail padding")
    pixels = tuple((values[index // 8] >> (7 - index % 8)) & 1 for index in range(count))
    return width, height, pixels


def read_text_grid(path):
    """Parse a developer-side example using printable ASCII zero and one."""
    rows = path.read_text(encoding="ascii").splitlines()
    if not rows or not rows[0] or any(len(row) != len(rows[0]) or set(row) - {"0", "1"} for row in rows):
        raise ValueError("expected a rectangular grid of literal zero/one characters")
    return len(rows[0]), len(rows), tuple(int(bit) for row in rows for bit in row)


def grayscale_pgm(width, height, pixels):
    """Convert to a common Earth-side image format for inspection only."""
    return f"P5\n{width} {height}\n255\n".encode("ascii") + bytes(bit * 255 for bit in pixels)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("encode", "decode"):
        sub = commands.add_parser(name)
        sub.add_argument("source", type=Path)
        sub.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "encode":
            width, height, pixels = read_text_grid(args.source)
            encoded = encode_frame(width, height, pixels)
        else:
            width, height, pixels = decode_frame(args.source.read_bytes())
            encoded = grayscale_pgm(width, height, pixels)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(encoded)
        print(f"Written {args.output} ({len(encoded)} bytes)")
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(1, f"raw-raster: {error}\n")


if __name__ == "__main__":
    main()
