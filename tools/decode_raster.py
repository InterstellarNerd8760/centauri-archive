"""Reference test decoder: turn rows of literal 0/1 into an 8-bit grayscale PGM."""
import argparse
from pathlib import Path


def decode_rows(rows):
    """A deliberate human-readable exercise, NOT an extraterrestrial bootstrap."""
    if len(rows) != 8 or any(len(row) != 8 or set(row) - {"0", "1"} for row in rows):
        raise ValueError("expected exactly eight rows of eight literal 0/1 symbols")
    data = bytes(255 if c == "1" else 0 for row in rows for c in row)
    return b"P5\n8 8\n255\n" + data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        encoded = decode_rows(args.source.read_text(encoding="ascii").splitlines())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(encoded)
        print(f"Wrote 8x8 raster to {args.output}")
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(1, f"decode: {error}\n")


if __name__ == "__main__":
    main()
