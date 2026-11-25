"""Prepare compact canonical raster exhibits from credited archive photographs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from photo_raster import (ROOT, archive_selections, derivatives, encode_frame,
                          inspect, load_pillow)
from protect_archive import BLOCK_PAYLOAD, RS_TOTAL, protect_record

SELECTION = {
    "IMG-019": ("Earth", (16, 32, 64, 128)),
    "IMG-050": ("Biological specimen", (16, 32, 64)),
    "IMG-036": ("Landscape", (16, 32, 64)),
    "IMG-073": ("Human group", (16, 32, 64)),
    "IMG-011": ("Astronomical observation", (16, 32, 64)),
}
DEFAULT_OUTPUT = ROOT / "website/photo-reconstruction"
PROTECTED_RAW = "img-019-e32-rgb.car"
PROTECTED_FILE = "img-019-e32-rgb.caec"


def write_exhibit(target):
    _, _, pillow_version, features = load_pillow()
    target.mkdir(parents=True, exist_ok=True)
    records = []
    selected = {item[0]: item[1:] for item in archive_selections(SELECTION)}
    for identifier, (subject, edges) in SELECTION.items():
        source, plan, catalog = selected[identifier]
        variants = []
        record_id = int(identifier[4:])
        for edge in edges:
            for raster in derivatives(source, record_id, (1, 8, 24), edge):
                encoded = encode_frame(raster)
                info = inspect(raster)
                name = f"{identifier.lower()}-e{edge}-{info['mode']}.car"
                (target / name).write_bytes(encoded)
                variants.append(dict(info, file=name, edge=edge,
                                     sha256=sha256(encoded).hexdigest()))
        records.append({
            "id": identifier, "subject": subject, "asset": plan["asset"],
            "sha256": sha256(source.read_bytes()).hexdigest(),
            "title": catalog["title"], "alt": catalog["alt"],
            "credit": catalog["photographer"], "rights": catalog["rights"],
            "source_derivative": catalog["derivative"], "sources": catalog["sources"],
            "preparation": "Uncropped experimental derivatives resized with BOX, stored in raw RGB, grayscale and thresholded black and white.",
            "variants": variants,
        })

    raw = (target / PROTECTED_RAW).read_bytes()
    protected = b"".join(protect_record(19, raw))
    (target / PROTECTED_FILE).write_bytes(protected)
    manifest = {
        "version": 1,
        "encoder": {
            "pillow": pillow_version,
            "jpeg_codec": features.version_codec("jpg"),
            "libjpeg_turbo": features.version_feature("libjpeg_turbo"),
        },
        "records": records,
        "protection": {
            "file": PROTECTED_FILE, "raw": PROTECTED_RAW, "record_id": 19,
            "raw_bytes": len(raw), "encoded_bytes": len(protected),
            "block_bytes": RS_TOTAL, "payload_bytes_per_block": BLOCK_PAYLOAD,
            "block_count": len(protected) // RS_TOTAL,
            "sha256": sha256(protected).hexdigest(),
        },
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, nargs="?", default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    manifest = write_exhibit(arguments.output)
    print(f"Prepared {sum(len(record['variants']) for record in manifest['records'])} "
          f"raw frames and one protected record in {arguments.output}")


if __name__ == "__main__":
    main()
