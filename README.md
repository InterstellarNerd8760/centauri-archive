# Centauri Archive

**A record of Earth, life, and human civilization for interstellar spacecraft.**

Centauri Archive is an independent, open engineering and curation project developing a compact archive that could be adapted for an interstellar mission. The initial target for a *proposed* contribution is **Fermi Explorer**. There is **no affiliation, flight approval, payload allocation, or integration agreement**.

The project has two horizons: a deliberately small **Fermi Edition** for a constrained spacecraft and a future, much larger **Ark Edition** for missions capable of carrying richer records.

## What v0.4 actually is

- A reproducible, inspectable **digital development package** containing original introductory records about mathematics, astronomy, matter, biology, humanity, and a provisional message; plus three original scientific SVG diagrams.
- A manifest with file lengths and SHA-256 digests. These detect changes; they **do not correct corruption**.
- A documented proposal for a **physical decoding primer**, not yet fabricated or validated. An experimental panel diagram and 8×8 reference raster/decoder demonstrate a small part of the learning ladder.
- A public multimedia site with a beginner-level binary primer, an interactive 8×8 decoding lab, and a navigable editorial atlas of **100 proposed images in ten categories**. The image atlas does not claim planned images are archived.

**Not yet demonstrated:** decoding without knowledge of human languages and computing, radiation survival, error recovery, archive-health telemetry, physical carrier manufacture, or Fermi Explorer compatibility. The ZIP container is a convenient development transport, **not a proposed alien-readable flight format**.

The prose, original SVG diagrams and draft message are provisional content, not a comprehensive or representative encyclopedia. Photographs and field recordings are not yet included. The image plan defines 100 intended subjects, of which **three project-original diagrams** currently exist. Content selection, review, rights and permission tracking remain active work.

## Reading the collection

The public website includes a human-facing multimedia chapter reader at library.html
and an introductory binary explanation and 8×8 decoding laboratory at guide.html, alongside an explanation of the proposed primer and carrier. The separately published `images.html` inventories proposed imagery without inflating the verified payload.
These pages are deliberately separate from the verified source ZIP; a future
interstellar reader cannot be assumed to understand HTML, text files or USB
storage. For current engineering decisions see
[docs/payload-architecture.md](docs/payload-architecture.md).

## Quick start

Python 3.10+; no third-party packages:

```sh
python3 tools/archive.py build build/centauri.zip
python3 tools/archive.py inspect build/centauri.zip
python3 tools/archive.py verify build/centauri.zip
python3 -m unittest discover -s tests -v
python3 tools/build_site.py
python3 -m http.server 8000 --directory build/site
```

Start reading at `content/primer/start.txt` *after* extracting the ZIP with an existing ZIP reader. The file explains the current limitations. The site is a presentation layer and is not needed to extract the package.

## One decoding exercise

```sh
python3 tools/decode_raster.py archive/primer/raster-example.txt build/raster-example.pgm
```

This converts 8 rows of ASCII 0/1 symbols to a 64-pixel PGM raster.
Compare the rendered result with [the panel concept](docs/primer-panel.svg).
This exercise assumes a human already understands the symbols and the file.
It does **not** establish universal readability.

## Repository map

| Path | Purpose |
| --- | --- |
| `archive/primer/` | Explicit reader assumptions and mathematical/format foundations |
| `curation/images-100.json` | Editorial plan for 100 images; separate from the verified ZIP |
| `archive/catalog.json` | Editorial metadata, record titles, sources, rights and review status |
| `archive/visuals/` | Original SVG diagrams for the human-facing edition |
| `archive/science/`, `archive/experiences/` | Matter, energy and sound foundations |
| `archive/earth/` | Earth and Solar System |
| `archive/biology/` | Life, genetics, diversity and evolution |
| `archive/humanity/` | Human civilization and historical overview |
| `archive/messages/` | Provisional, clearly labeled editorial draft |
| `docs/physical-primer.md` | Proposed non-language-first physical decoding pathway |
| `docs/mission.md` | Mission questions and unverified assumptions |
| `docs/engineering.md` | Data integrity, radiation, redundancy, telemetry |
| `docs/roadmap.md` | Milestones and acceptance criteria |
| `tools/`, `tests/` | Reproducible tools and automated verification |
| `website/` | Static information site, built to `build/site` |

## Development principle

**Meaning before megabytes.** Every item should answer a specific question about how to understand Earth or interpret the remaining archive. Proposed flight hardware must be defined only after obtaining real spacecraft constraints.

See [roadmap](docs/roadmap.md), [100-image plan](docs/images-100-plan.md), [content source workflow](docs/encyclopedia-sourcing.md), [physical primer](docs/physical-primer.md), [plain-language decoding explanation](docs/decoding-in-plain-language.md), [source policy](docs/source-policy.md), and [media candidates](docs/media-candidates.md).