"""Assemble a self-contained static site for local preview or Pages."""
import json
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


def presentation_metrics(articles, image_plan, damage, record_count):
    """Derive the public brief's statistics from the same source and experiment."""
    cases = tuple(damage["cases"].values())
    exact = tuple(case for case in cases
                  if len(case["records"]) == record_count and not case["incorrect_accepted_ids"])
    complete = sum(case["map_status"] == "verified" for case in exact)
    unknown = len(exact) - complete
    return {
        "__ARTICLE_COUNT__": len(articles["articles"]),
        "__PHOTO_COUNT__": sum(record["status"] == "included" for record in image_plan["records"]),
        "__SPECIMEN_COUNT__": record_count,
        "__RECOVERY_CASES__": len(cases),
        "__COMPLETE_CASES__": complete,
        "__UNKNOWN_CASES__": unknown,
        "__PARTIAL_CASES__": len(cases) - len(exact),
        "__INCORRECT_FRAMES__": sum(len(case["incorrect_accepted_ids"]) for case in cases),
    }


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
    index = output / "index.html"
    html = index.read_text(encoding="utf-8")
    html = html.replace("__EDITION__", manifest["archive_version"])
    html = html.replace("__SIZE__", f"{package.stat().st_size / 1_000_000:.3f}")
    metrics = presentation_metrics(
        json.loads((ROOT / "archive/encyclopedia/index.json").read_text(encoding="utf-8")),
        json.loads((ROOT / "curation/images-100.json").read_text(encoding="utf-8")),
        damage, len(framed),
    )
    for token, value in metrics.items():
        html = html.replace(token, str(value))
    index.write_text(html, encoding="utf-8")
    proposal = output / "proposal.html"
    proposal_html = proposal.read_text(encoding="utf-8")
    for token, value in metrics.items():
        proposal_html = proposal_html.replace(token, str(value))
    proposal.write_text(proposal_html, encoding="utf-8")
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
