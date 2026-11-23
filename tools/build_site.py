"""Assemble a self-contained static site for local preview or Pages."""
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from archive import ROOT, build


def assemble(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "website", output, dirs_exist_ok=True)
    package = output / "downloads" / "centauri.zip"
    manifest = build(package)
    with ZipFile(package) as archive:
        (package.parent / "manifest.json").write_bytes(archive.read("manifest.json"))
        for item in manifest["files"]:
            if item["media_type"].startswith("text/"):
                path = output / "records" / item["path"].removeprefix("content/")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.read(item["path"]))
    shutil.copyfile(ROOT / "docs/engineering.md", output / "engineering.txt")
    index = output / "index.html"
    html = index.read_text(encoding="utf-8")
    html = html.replace("__EDITION__", manifest["archive_version"])
    html = html.replace("__SIZE__", f"{package.stat().st_size / 1_000_000:.2f}")
    index.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    destination = ROOT / "build/site"
    destination.parent.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as temp:
        assembled = Path(temp) / "site"
        assemble(assembled)
        if destination.exists():
            shutil.rmtree(destination)
        assembled.rename(destination)
    print(f"Static site ready in {destination}")
