"""Build, inspect or verify a Centauri Archive v1 package."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from tempfile import NamedTemporaryFile
from zipfile import BadZipFile, ZIP_STORED, ZipFile, ZipInfo

from plate import plate

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 10_000_000
PATH = re.compile(r"content/(?:[a-z0-9][a-z0-9._-]*/)*[a-z0-9][a-z0-9._-]*")
TYPES = {".txt": "text/plain", ".csv": "text/csv", ".pgm": "image/x-portable-graymap"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build(output):
    source = ROOT / "archive"
    records = {}
    for file in sorted(source.rglob("*")):
        if file.is_symlink():
            raise ValueError(f"symlink in source: {file}")
        if file.is_file():
            name = "content/" + file.relative_to(source).as_posix()
            records[name] = file.read_bytes()
    generated = "content/primer/plate.pgm"
    if generated in records:
        raise ValueError("plate path is reserved for the generated raster")
    records[generated] = plate()
    entries = []
    for name, data in sorted(records.items()):
        entries.append(dict(path=name, size=len(data), sha256=digest(data),
                            media_type=TYPES.get(Path(name).suffix, "application/octet-stream")))
    manifest = dict(format_version=1, archive_version="0.1.0", files=entries)
    header = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    output = Path(output).resolve()
    if output.is_relative_to(source):
        raise ValueError("write packages outside the source collection")
    output.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=output.parent, delete=False) as temp:
        staging = Path(temp.name)
    try:
        with ZipFile(staging, "w") as package:
            for name, data in [("manifest.json", header), *sorted(records.items())]:
                member = ZipInfo(name)
                member.create_system = 3
                member.external_attr = 0o100644 << 16
                package.writestr(member, data)
        examine(staging, verify=True)
        os.replace(staging, output)
    finally:
        staging.unlink(missing_ok=True)
    return manifest


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def examine(path, verify=False):
    if Path(path).stat().st_size > LIMIT:
        raise ValueError("package exceeds byte budget")
    with ZipFile(path) as package:
        members = package.infolist()
        names = {m.filename for m in members}
        if len(names) != len(members) or "manifest.json" not in names:
            raise ValueError("duplicate members or missing manifest")
        if sum(m.file_size for m in members) > LIMIT or any(
            m.compress_type != ZIP_STORED or m.compress_size != m.file_size or m.flag_bits & 1
            for m in members
        ):
            raise ValueError("unsupported member encoding or size")
        manifest = json.loads(package.read("manifest.json").decode("utf-8"), object_pairs_hook=unique_keys)
        if not isinstance(manifest, dict) or type(manifest.get("format_version")) is not int or manifest["format_version"] != 1:
            raise ValueError("unsupported manifest version")
        version = manifest.get("archive_version")
        entries = manifest.get("files")
        if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
            raise ValueError("invalid archive version")
        if not isinstance(entries, list) or not entries:
            raise ValueError("empty or invalid inventory")
        remaining = names - {"manifest.json"}
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError("invalid file record")
            name = entry.get("path")
            if not isinstance(name, str) or not PATH.fullmatch(name) or name not in remaining:
                raise ValueError(f"unexpected or invalid record: {name!r}")
            remaining.remove(name)
            checksum = entry.get("sha256")
            media = entry.get("media_type")
            size = entry.get("size")
            if not isinstance(checksum, str) or not re.fullmatch("[0-9a-f]{64}", checksum):
                raise ValueError(f"invalid digest: {name}")
            if not isinstance(media, str) or not re.fullmatch(r"[a-zA-Z0-9.+-]+/[a-zA-Z0-9.+-]+", media):
                raise ValueError(f"invalid media type: {name}")
            if type(size) is not int or size != package.getinfo(name).file_size:
                raise ValueError(f"size mismatch: {name}")
            if verify and digest(package.read(name)) != checksum:
                raise ValueError(f"checksum mismatch: {name}")
        if remaining:
            raise ValueError("unlisted package members")
        return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "inspect", "verify"))
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "build":
            build(args.package)
            print(f"Built {args.package} ({args.package.stat().st_size} bytes)")
        else:
            manifest = examine(args.package, verify=args.command == "verify")
            if args.command == "inspect":
                print(json.dumps(manifest, indent=2))
            else:
                print(f"Verified {len(manifest['files'])} records in {args.package}")
    except (ValueError, OSError, BadZipFile, RuntimeError, EOFError) as error:
        parser.exit(1, f"archive: {error}\n")


if __name__ == "__main__":
    main()
