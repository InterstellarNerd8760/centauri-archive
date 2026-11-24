"""Encode, decode, inspect and budget experimental Centauri raw raster v2."""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import struct
from tempfile import NamedTemporaryFile, TemporaryDirectory

from raw_raster import SYNC

ROOT = Path(__file__).resolve().parents[1]
VERSION = 2
HEADER = struct.Struct(">8sBBHHII")
DIGEST_BYTES = 32
OVERHEAD = HEADER.size + DIGEST_BYTES
MODE_CODES = {"mono": 1, "gray": 8, "rgb": 24}
MODE_NAMES = {code: name for name, code in MODE_CODES.items()}
MAX_SIDE = 16_384
MAX_PIXELS = 16_777_216
MAX_FRAME_BYTES = MAX_PIXELS * 3 + OVERHEAD
DEMO_IDS = ("IMG-019", "IMG-036", "IMG-050", "IMG-073")


@dataclass(frozen=True)
class Raster:
    """A validated frame's scalar fields and packed payload."""

    record_id: int
    width: int
    height: int
    mode: int
    payload: bytes


def pixel_count(width, height):
    if (type(width) is not int or type(height) is not int
            or not (1 <= width <= MAX_SIDE and 1 <= height <= MAX_SIDE)
            or width * height > MAX_PIXELS):
        raise ValueError("invalid raster dimensions")
    return width * height


def payload_size(width, height, mode):
    count = pixel_count(width, height)
    if type(mode) is not int or mode not in MODE_NAMES:
        raise ValueError("unknown raster mode")
    return (count * mode + 7) // 8


def validate_record_id(record_id):
    if type(record_id) is not int or not 1 <= record_id <= 0xFFFFFFFF:
        raise ValueError("record ID must be a positive unsigned 32-bit integer")
    return record_id


def validate_padding(width, height, mode, last_byte):
    tail_bits = (width * height) % 8
    if mode == 1 and tail_bits and last_byte & ((1 << (8 - tail_bits)) - 1):
        raise ValueError("nonzero monochrome tail padding")


def encode_frame(raster):
    size = payload_size(raster.width, raster.height, raster.mode)
    validate_record_id(raster.record_id)
    if len(raster.payload) != size:
        raise ValueError("payload size does not match dimensions and mode")
    validate_padding(raster.width, raster.height, raster.mode, raster.payload[-1])
    body = HEADER.pack(SYNC, VERSION, raster.mode, raster.width, raster.height,
                       raster.record_id, size) + raster.payload
    return body + hashlib.sha256(body).digest()


def decode_frame(data):
    if len(data) < OVERHEAD:
        raise ValueError("truncated raster frame")
    sync, version, mode, width, height, record_id, size = HEADER.unpack_from(data)
    if sync != SYNC or version != VERSION:
        raise ValueError("missing sync marker or unsupported raster version")
    validate_record_id(record_id)
    if size != payload_size(width, height, mode) or len(data) != OVERHEAD + size:
        raise ValueError("wrong payload or frame length")
    validate_padding(width, height, mode, data[-DIGEST_BYTES - 1])
    if hashlib.sha256(memoryview(data)[:-DIGEST_BYTES]).digest() != data[-DIGEST_BYTES:]:
        raise ValueError("SHA-256 mismatch")
    return Raster(record_id, width, height, mode, bytes(data[HEADER.size:-DIGEST_BYTES]))


def preview(raster):
    """Reconstruct PGM (monochrome/grayscale) or PPM (RGB) for Earth-side use."""
    magic = "P6" if raster.mode == 24 else "P5"
    header = f"{magic}\n{raster.width} {raster.height}\n255\n".encode("ascii")
    if raster.mode != 1:
        return header + raster.payload
    return header + bytes(
        255 * ((raster.payload[index // 8] >> (7 - index % 8)) & 1)
        for index in range(raster.width * raster.height)
    )


def read_frame(path):
    with path.open("rb") as stream:
        return decode_frame(stream.read(MAX_FRAME_BYTES + 1))


def validate_edge(edge):
    if edge is not None and (type(edge) is not int or not 1 <= edge <= MAX_SIDE):
        raise ValueError(f"maximum edge must be between 1 and {MAX_SIDE}")


def scaled_dimensions(width, height, edge):
    validate_edge(edge)
    if edge is None or max(width, height) <= edge:
        return width, height
    longest = max(width, height)
    scaled_width = max(1, (width * edge + longest // 2) // longest)
    scaled_height = max(1, (height * edge + longest // 2) // longest)
    return scaled_width, scaled_height


def load_pillow():
    try:
        from PIL import Image, ImageOps, __version__, features
    except ImportError as error:
        raise ValueError("image preparation needs Pillow (pip install -r requirements-raster.txt)") from error
    return Image, ImageOps, __version__, features


def prepare_photo(source, edge):
    Image, ImageOps, _, _ = load_pillow()
    with Image.open(source) as photo:
        pixel_count(*photo.size)
        if (photo.mode not in ("RGB", "L") or photo.info.get("icc_profile")
                or getattr(photo, "n_frames", 1) != 1):
            raise ValueError("expected a single image in RGB or L mode without an embedded ICC profile")
        oriented = ImageOps.exif_transpose(photo)
        dimensions = scaled_dimensions(*oriented.size, edge)
        rgb = oriented.convert("RGB")
        if rgb.size != dimensions:
            rgb = rgb.resize(dimensions, Image.Resampling.BOX)
        return dimensions[0], dimensions[1], rgb.tobytes()


def gray_samples(rgb):
    return bytes((299 * red + 587 * green + 114 * blue + 500) // 1000
                 for red, green, blue in zip(rgb[0::3], rgb[1::3], rgb[2::3]))


def pack_monochrome(gray):
    result = bytearray((len(gray) + 7) // 8)
    for index, sample in enumerate(gray):
        if sample >= 128:
            result[index // 8] |= 1 << (7 - index % 8)
    return bytes(result)


def derivatives(source, record_id, modes, edge):
    width, height, rgb = prepare_photo(source, edge)
    payloads = {24: rgb}
    if 1 in modes or 8 in modes:
        payloads[8] = gray_samples(rgb)
    if 1 in modes:
        payloads[1] = pack_monochrome(payloads[8])
    for mode in modes:
        yield Raster(record_id, width, height, mode, payloads[mode])


def archive_selections(ids):
    plan = json.loads((ROOT / "curation/images-100.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "archive/catalog.json").read_text(encoding="utf-8"))
    catalog_by_path = {record["path"]: record for record in catalog["records"]}
    included = {record["id"]: record for record in plan["records"] if record["status"] == "included"}
    selected = sorted(included if ids is None else ids)
    if len(set(selected)) != len(selected):
        raise ValueError("duplicate photo ID")
    for record_id in selected:
        if record_id not in included or not re.fullmatch(r"IMG-[0-9]{3,}", record_id):
            raise ValueError(f"unknown or unacquired photo ID: {record_id}")
        plan_entry = included[record_id]
        asset = plan_entry["asset"]
        source = ROOT / "archive" / asset
        if not source.resolve().is_relative_to(ROOT / "archive/photos") or not source.is_file():
            raise ValueError(f"{record_id} has an invalid source asset")
        if asset not in catalog_by_path:
            raise ValueError(f"{record_id} lacks catalog provenance")
        yield record_id, source, plan_entry, catalog_by_path[asset]


def external_output(path):
    path = path.resolve()
    if path.is_relative_to(ROOT / "archive"):
        raise ValueError("write derivatives outside the source collection")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_output(path, data):
    path = external_output(path)
    with NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        staging = Path(stream.name)
    try:
        staging.write_bytes(data)
        staging.replace(path)
    finally:
        staging.unlink(missing_ok=True)


def inspect(raster):
    return {
        "version": VERSION, "record_id": raster.record_id,
        "width": raster.width, "height": raster.height, "mode": MODE_NAMES[raster.mode],
        "payload_bytes": len(raster.payload), "frame_bytes": len(raster.payload) + OVERHEAD,
    }


def batch(output, ids, edge, modes):
    validate_edge(edge)
    _, _, pillow_version, features = load_pillow()
    output = external_output(output)
    if output.exists():
        raise ValueError("batch output directory already exists")
    manifest = {
        "version": VERSION, "max_edge": edge,
        "preparation": {
            "pillow": pillow_version, "jpeg_codec": features.version_codec("jpg"),
            "libjpeg_turbo": features.version_feature("libjpeg_turbo"),
            "resize": "Pillow BOX on encoded 8-bit RGB samples",
            "color_assumption": "untagged RGB treated as sRGB; source color fidelity is unverified",
            "grayscale": "(299 R + 587 G + 114 B + 500) // 1000",
            "mono": "grayscale >= 128; continuous MSB-first packing",
        },
        "records": [],
    }
    with TemporaryDirectory(dir=output.parent) as temp:
        staging = Path(temp) / "batch"
        staging.mkdir()
        for record_id, source, plan, catalog in archive_selections(ids):
            frames = []
            for raster in derivatives(source, int(record_id[4:]), modes, edge):
                encoded = encode_frame(raster)
                filename = f"{record_id.lower()}-{MODE_NAMES[raster.mode]}.car"
                (staging / filename).write_bytes(encoded)
                frames.append(dict(inspect(raster), path=filename,
                                   sha256=hashlib.sha256(encoded).hexdigest()))
            manifest["records"].append({
                "id": record_id, "source": plan, "catalog": catalog,
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "derivatives": frames,
            })
        (staging / "manifest.json").write_bytes(
            (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
        )
        staging.rename(output)
    return manifest


def collection_budget(ids, edges):
    Image, _, _, _ = load_pillow()
    for edge in edges:
        validate_edge(edge)
    scenarios = {edge: dict.fromkeys(MODE_CODES, 0) for edge in dict.fromkeys(edges)}
    count = source_bytes = 0
    for _, source, _, _ in archive_selections(ids):
        with Image.open(source) as photo:
            width, height = photo.size
            if photo.getexif().get(274) in (5, 6, 7, 8):
                width, height = height, width
        for edge, totals in scenarios.items():
            dimensions = scaled_dimensions(width, height, edge)
            for mode, code in MODE_CODES.items():
                totals[mode] += OVERHEAD + payload_size(*dimensions, code)
        count += 1
        source_bytes += source.stat().st_size
    return {"photos": count, "source_bytes": source_bytes, "frame_overhead_bytes": OVERHEAD,
            "scenarios": [{"max_edge": edge, "frame_bytes": totals} for edge, totals in scenarios.items()]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    encode = sub.add_parser("encode", help="convert an Earth-side image to one raw frame")
    encode.add_argument("source", type=Path)
    encode.add_argument("output", type=Path)
    encode.add_argument("--record-id", required=True, type=int)
    encode.add_argument("--mode", required=True, choices=MODE_CODES)
    encode.add_argument("--max-edge", type=int)
    decode = sub.add_parser("decode", help="verify the frame and reconstruct PGM or PPM")
    decode.add_argument("source", type=Path)
    decode.add_argument("output", type=Path)
    inspect_command = sub.add_parser("inspect", help="verify and describe a raw frame")
    inspect_command.add_argument("source", type=Path)
    batch_command = sub.add_parser("batch", help="encode acquired photographs with provenance")
    batch_command.add_argument("output", type=Path, help="new directory for frames and manifest")
    batch_command.add_argument("--ids", nargs="+", default=DEMO_IDS)
    batch_command.add_argument("--modes", nargs="+", choices=MODE_CODES, default=tuple(MODE_CODES))
    batch_command.add_argument("--max-edge", type=int, default=256)
    budget = sub.add_parser("budget", help="count raw bytes from current photo dimensions")
    budget.add_argument("--ids", nargs="+")
    budget.add_argument("--max-edge", nargs="+", type=int, default=[64, 256, 512, 1024])
    args = parser.parse_args()
    try:
        if args.command in ("encode", "decode") and args.source.resolve() == args.output.resolve():
            raise ValueError("source and output must be different")
        if args.command == "encode":
            raster = next(derivatives(args.source, args.record_id, [MODE_CODES[args.mode]], args.max_edge))
            write_output(args.output, encode_frame(raster))
        elif args.command == "decode":
            write_output(args.output, preview(read_frame(args.source)))
        elif args.command == "inspect":
            print(json.dumps(inspect(read_frame(args.source)), sort_keys=True))
        elif args.command == "batch":
            modes = sorted({MODE_CODES[mode] for mode in args.modes})
            manifest = batch(args.output, args.ids, args.max_edge, modes)
            print(f"Encoded {len(manifest['records'])} photographs in {args.output}")
        else:
            print(json.dumps(collection_budget(args.ids, [*args.max_edge, None]), indent=2))
    except (OSError, ValueError) as error:
        parser.exit(1, f"photo-raster: {error}\n")


if __name__ == "__main__":
    main()
