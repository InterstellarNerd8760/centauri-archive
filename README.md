# Centauri Archive

**A record of Earth, life, and human civilization for interstellar spacecraft.**

Centauri Archive is an independent, open engineering and curation project developing a compact archive that could be adapted for an interstellar mission. The initial target for a *proposed* contribution is **Fermi Explorer**. There is **no affiliation, flight approval, payload allocation, or integration agreement**.

The project has two horizons: a deliberately small **Fermi Edition** for a constrained spacecraft and a future, much larger **Ark Edition** for missions capable of carrying richer records.

## What v0.6 actually is

- A reproducible, inspectable **digital development package** containing original introductory records about mathematics, astronomy, matter, biology, humanity, and a provisional message; three original scientific SVG diagrams; and credited documentary images, including an ultrasound.
- A manifest with file lengths and SHA-256 digests. These detect changes; they **do not correct corruption**.
- A documented proposal for a **physical decoding primer**, not yet fabricated or validated. An experimental panel diagram and 8×8 reference raster/decoder demonstrate a small part of the learning ladder.
- A public multimedia site with a beginner-level binary primer, an interactive 8×8 decoding lab, and a navigable editorial atlas of **100 proposed photographs in ten categories**. The image atlas does not claim planned images are archived.

**Not yet demonstrated:** decoding without knowledge of human languages and computing, radiation survival, error recovery, archive-health telemetry, physical carrier manufacture, or Fermi Explorer compatibility. The ZIP container is a convenient development transport, **not a proposed alien-readable flight format**.

The prose, original SVG diagrams and draft message are provisional content, not a comprehensive or representative encyclopedia. Real photographs have been added; recorded audio is not yet included. The image plan defines an original goal of 100 images and currently names 104 subjects. As of November 23, 2026, all 104 are marked included in `curation/images-100.json`; actual package integrity and independent editorial review remain separate checks. Only records marked `included` are counted as acquired. The three original scientific SVGs are separate explanatory assets, not counted as photographs. Content selection, review, rights and permission tracking remain active work.

## Reading the collection

The two public collection interfaces are the [Encyclopedia](https://interstellarnerd8760.github.io/centauri-archive/encyclopedia.html) and [Image Library](https://interstellarnerd8760.github.io/centauri-archive/images.html). The encyclopedia organizes 29 introductory drafts and links all 104 planned photographic records and the earlier supplementary text files. The legacy raw-file reader remains available at `library.html` for compatibility. The binary explanation and 8×8 decoding laboratory at `guide.html` are separate engineering resources.
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

## Experimental raw binary image frame

The separate, deliberately minimal raster experiment packs 1-bit images into
byte-framed records without ZIP, JSON, JPEG or UTF-8. It includes a fixed
8-by-8 sample vector, simple complement-based corruption detection, a parser
and a human-side PGM preview:

```sh
python3 tools/raw_raster.py encode archive/primer/raster-example.txt build/example.bin
python3 tools/raw_raster.py decode build/example.bin build/example.pgm
```

This is **not an alien-readable format**. A real physical primer still needs
to establish how to identify the frame, measure its units, interpret bits and
reconstruct images. See [raw raster experiment](docs/raw-raster-experiment.md).

An independent JavaScript implementation can be exercised with `node tests/raw_raster_independent.cjs`. A separate [text-free panel and blind-test protocol](docs/blind-primer-experiment.md) proposes a first human interpretation trial; no trial results exist yet.

## Repository map

| Path | Purpose |
| --- | --- |
| `archive/primer/` | Explicit reader assumptions and mathematical/format foundations |
| `curation/images-100.json` | Editorial plan for 100 authentic photographs; separate from the verified ZIP |
| `archive/catalog.json` | Editorial metadata, record titles, sources, rights and review status |
| `archive/visuals/` | Original explanatory SVG diagrams (not documentary photos) |
| `archive/photos/` | Genuine sourced photographs packaged as JPEGs and documented in the catalog |
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

See [engineering validation gates](docs/engineering-validation-plan.md), [roadmap](docs/roadmap.md), [acquired photo provenance](docs/photographic-acquisitions.md), [100-photograph plan](docs/images-100-plan.md), [content source workflow](docs/encyclopedia-sourcing.md), [physical primer](docs/physical-primer.md), [plain-language decoding explanation](docs/decoding-in-plain-language.md), [source policy](docs/source-policy.md), and [media candidates](docs/media-candidates.md).