"""Import a reviewed batch of real JPEGs into the archive and photo plan.

Run from the repository root:
  python3 tools/import_photo_batch.py curation/batches/nasa-01.json

This makes local changes only. Every entry must have a source page, direct
asset URL, credit, descriptive caption and rights basis. The binary is copied
into archive/photos; never hotlinked in the final gallery.
"""
import argparse
import json
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MAX_DOWNLOAD = 20_000_000
MAX_OUTPUT = 3_000_000
MAX_DIMENSION = 1800
MAX_ARCHIVE_BYTES = 80_000_000


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def checked_url(value):
    url = urlparse(value)
    if url.scheme != "https" or url.hostname not in {
        "assets.science.nasa.gov", "images-assets.nasa.gov", "eol.jsc.nasa.gov",
        "science.nasa.gov", "eoimages.gsfc.nasa.gov", "cdn.eso.org", "upload.wikimedia.org"
    }:
        raise ValueError(f"Not a permitted NASA media host: {value}")
    return value


def retrieve(url):
    request = Request(checked_url(url), headers={"User-Agent": "CentauriArchive/0.6 (+https://github.com/InterstellarNerd8760/centauri-archive)"})
    with urlopen(request, timeout=35) as response:
        content = response.read(MAX_DOWNLOAD + 1)
        if len(content) > MAX_DOWNLOAD:
            raise ValueError("Image exceeds 20 MB source download limit")
        if response.headers.get("Content-Type", "").lower().startswith("text/"):
            raise ValueError("Server returned text instead of a JPEG")
    if not (8_000 <= len(content) <= MAX_DOWNLOAD and (
            (content[:2] == b"\xff\xd8" and content[-2:] == b"\xff\xd9")
            or content[:8] == b"\x89PNG\r\n\x1a\n"
            or (content[:4] == b"RIFF" and content[8:12] == b"WEBP"))):
        raise ValueError("Invalid or suspicious source image")
    # Keep the acquisition JPEG high quality while enforcing the small
    # prototype ZIP budget. Original source URL stays in provenance metadata.
    from PIL import Image, ImageOps
    with Image.open(BytesIO(content)) as original:
        original.load()
        image = ImageOps.exif_transpose(original).convert("RGB")
        image.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
        output = BytesIO()
        image.save(output, format="JPEG", quality=87, optimize=True)
        converted = output.getvalue()
    if len(converted) > MAX_OUTPUT:
        raise ValueError("Downsampled JPEG exceeds 3 MB payload budget")
    return converted


def import_batch(batch_path):
    batch = read_json(batch_path)
    if not isinstance(batch.get("images"), list) or not batch["images"]:
        raise ValueError("Batch must contain at least one image")
    plan_path = ROOT / "curation/images-100.json"
    catalog_path = ROOT / "archive/catalog.json"
    plan = read_json(plan_path)
    catalog = read_json(catalog_path)
    slots = {item["id"]: item for item in plan["records"]}
    paths = {item["path"] for item in catalog["records"]}
    imported = []
    binaries = {}
    for entry in batch["images"]:
        required = ("slot", "filename", "asset_url", "source_page", "title", "summary",
                    "alt", "caption", "credit", "date", "rights", "processing")
        if any(not isinstance(entry.get(key), str) or not entry[key].strip() for key in required):
            raise ValueError(f"Incomplete provenance for {entry.get('slot')}")
        slot = slots.get(entry["slot"])
        if slot is None:
            raise ValueError(f"Unknown slot: {entry['slot']}")
        filename = entry["filename"]
        if not filename.endswith(".jpg") or "/" in filename or "\\" in filename or filename.startswith("."):
            raise ValueError(f"Invalid filename: {filename}")
        path = "photos/" + filename
        if slot["status"] == "included" and slot["asset"] == path and path in paths:
            # Already imported by a previous successful batch run.
            continue
        if slot["status"] != "planned" or slot["asset"] is not None or path in paths or path in binaries:
            raise ValueError(f"Duplicate or unavailable image: {path}")
        if urlparse(entry["source_page"]).scheme != "https":
            raise ValueError("Source page must use HTTPS")
        print(f"Retrieving {entry['slot']}: {filename}", flush=True)
        binaries[path] = retrieve(entry["asset_url"])
        slot.update(status="included", asset=path, source_url=entry["source_page"],
                    curation_note="Source and acquisition documented; independent editorial review pending.")
        catalog["records"].append({
            "path": path, "title": entry["title"], "summary": entry["summary"],
            "group": "photos", "alt": entry["alt"], "caption": entry["caption"],
            "status": "Photograph acquired; editorial review pending",
            "rights": entry["rights"], "photographer": entry["credit"],
            "date": entry["date"], "derivative": entry["processing"],
            "sources": [{"label": "Source description and credits", "url": entry["source_page"]},
                        {"label": "Source image before documented JPEG derivative", "url": entry["asset_url"]}],
        })
        imported.append((entry["slot"], path, entry["source_page"]))
    # Check bytes before changing on-disk state. The existing prototype uses
    # stored/uncompressed media, so allow headroom for ZIP headers and metadata.
    archive_bytes = sum(p.stat().st_size for p in (ROOT / "archive").rglob("*") if p.is_file())
    if archive_bytes + sum(map(len, binaries.values())) > MAX_ARCHIVE_BYTES - 250_000:
        raise ValueError("Batch would exceed the development ZIP size budget")
    for path, content in binaries.items():
        target = ROOT / "archive" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    write_json(plan_path, plan)
    write_json(catalog_path, catalog)
    print("Imported " + ", ".join(f"{slot} ({path})" for slot, path, _ in imported))
    print(f"Photo count: {sum(r['status'] == 'included' for r in plan['records'])}/{len(plan['records'])}")
    return imported


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path)
    args = parser.parse_args()
    import_batch(args.batch)
