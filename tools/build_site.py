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
    # The curation plan is published alongside the development package.
    shutil.copyfile(ROOT / "curation/images-100.json", output / "image-plan.json")
    package = output / "downloads" / "centauri.zip"
    manifest = build(package)
    with ZipFile(package) as archive:
        (package.parent / "manifest.json").write_bytes(archive.read("manifest.json"))
        for item in manifest["files"]:
            # Every verified record is copied, including graphics and recordings.
            path = output / "records" / item["path"].removeprefix("content/")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(archive.read(item["path"]))
    public_documents = (
        "archive-editions", "blind-primer-experiment", "engineering", "error-correction",
        "fermi-explorer-proposal", "mission", "mission-integration", "physical-primer",
        "primer-ladder", "raw-raster-v2", "roadmap", "visual-vocabulary",
    )
    for name in public_documents:
        shutil.copyfile(ROOT / f"docs/{name}.md", output / f"{name}.txt")
    primer_panels = (
        "primer-panel", "primer-blind-panel", "primer-ladder",
        "primer-ladder-annotated", "primer-ladder-trial",
    )
    for name in primer_panels:
        shutil.copyfile(ROOT / f"docs/{name}.svg", output / f"{name}.svg")
    shutil.copyfile(ROOT / "docs/encyclopedia-mvp.md", output / "encyclopedia.txt")
    vector_directory = package.parent / "raster-vectors"
    vector_directory.mkdir(exist_ok=True)
    for vector in sorted((ROOT / "tests/fixtures/photo-raster-v2").glob("*.car")):
        shutil.copyfile(vector, vector_directory / vector.name)
    index = output / "index.html"
    html = index.read_text(encoding="utf-8")
    html = html.replace("__EDITION__", manifest["archive_version"])
    html = html.replace("__SIZE__", f"{package.stat().st_size / 1_000_000:.3f}")
    index.write_text(html, encoding="utf-8")
    brief = output / "brief.html"
    brief.write_text(brief.read_text(encoding="utf-8").replace("__EDITION__", manifest["archive_version"]), encoding="utf-8")


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
