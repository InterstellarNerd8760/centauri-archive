"""Assemble a self-contained static site for local preview or Pages."""
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from archive import ROOT, build
from build_knowledge import publish_knowledge
from knowledge_budget import compact_json, measure
from physical_damage_study import run_study
from physical_recovery import encode_specimen
from physical_surface import Surface, measure as measure_surface
from research_archive import assemble as assemble_records, frame, sample_records


PUBLIC_ARCHIVE = "https://westonrosch.com/archive/"
ARCHIVE_HEADER = "<!-- archive-header -->"
NAVIGATION = (
    ("brief.html", "Project brief"),
    ("encyclopedia.html", "Encyclopedia"),
    ("images.html", "Image library"),
    ("engineering.html", "Decoding and engineering"),
)
SECTION_ROOTS = {
    "proposal.html": "brief.html",
    "library.html": "encyclopedia.html",
    "guide.html": "engineering.html",
    "discovery.html": "engineering.html",
    "vocabulary.html": "engineering.html",
}


def publish_page(page, output):
    html = page.read_text(encoding="utf-8")
    if ARCHIVE_HEADER not in html:
        return
    relative = page.relative_to(output)
    path = relative.as_posix()
    prefix = "../" * (len(relative.parts) - 1)
    overview = ' aria-current="page"' if path == "index.html" else ""
    links = []
    for filename, label in NAVIGATION:
        current = ""
        if path == filename:
            current = ' aria-current="page"'
        elif SECTION_ROOTS.get(path) == filename:
            current = ' aria-current="location"'
        links.append(f'    <a href="{prefix}{filename}"{current}>{label}</a>')
    header = "\n".join((
        '<header class="header">',
        f'  <a class="brand" href="{prefix}index.html"{overview}>Centauri Archive<span class="brand-dot">.</span></a>',
        '  <nav aria-label="Centauri Archive">',
        *links,
        '  </nav>',
        '</header>',
    ))
    route = path.removesuffix("index.html") if relative.name == "index.html" else path.removesuffix(".html")
    canonical = f'<link rel="canonical" href="{PUBLIC_ARCHIVE}{route}">'
    html = html.replace(ARCHIVE_HEADER, header).replace("</head>", f"{canonical}\n</head>")
    page.write_text(html, encoding="utf-8")


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
    publish_knowledge(output)
    (output / "knowledge/budget.json").write_bytes(compact_json(measure()))
    sample = sample_records()
    framed = {record.id: frame(record) for record in sample}
    (package.parent / "phase-ii.cax").write_bytes(assemble_records(sample))
    (package.parent / "phase-ii.cas").write_bytes(encode_specimen(framed))
    damage = run_study(framed, logical_index_id=506)
    damage["geometry"] = measure_surface(Surface(40_000, 40_000, 80))
    (output / "surface-study.json").write_bytes(compact_json(damage))
    public_documents = (
        "archive-editions", "blind-primer-experiment", "engineering", "error-correction",
        "fermi-explorer-proposal", "mission", "mission-integration", "physical-primer",
        "primer-ladder", "raw-raster-v2", "roadmap", "visual-vocabulary",
        "knowledge-architecture", "knowledge-budget", "physical-recovery", "primer-c2",
        "research-archive-format",
    )
    for name in public_documents:
        shutil.copyfile(ROOT / f"docs/{name}.md", output / f"{name}.txt")
    primer_panels = (
        "primer-panel", "primer-blind-panel", "primer-ladder",
        "primer-ladder-annotated", "primer-ladder-trial",
        "primer-c2", "primer-c2-annotated",
    )
    for name in primer_panels:
        shutil.copyfile(ROOT / f"docs/{name}.svg", output / f"{name}.svg")
    shutil.copyfile(ROOT / "docs/encyclopedia-mvp.md", output / "encyclopedia.txt")
    shutil.copyfile(ROOT / "docs/primer-c2-conventions.json", output / "primer-c2-conventions.json")
    vector_directory = package.parent / "raster-vectors"
    vector_directory.mkdir(exist_ok=True)
    for vector in sorted((ROOT / "tests/fixtures/photo-raster-v2").glob("*.car")):
        shutil.copyfile(vector, vector_directory / vector.name)
    for page in output.rglob("*.html"):
        publish_page(page, output)


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
