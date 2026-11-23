# Centauri Archive

**A record of Earth, life, and human civilization for interstellar spacecraft.**

Centauri Archive is an independent, open engineering and curation project developing a compact archive that could be adapted for an interstellar mission. The initial target for a *proposed* contribution is **Fermi Explorer**. There is **no affiliation, flight approval, payload allocation, or integration agreement**.

The project has two horizons: a deliberately small **Fermi Edition** for a constrained spacecraft and a future, much larger **Ark Edition** for missions capable of carrying richer records.

## What v0.2 actually is

- A reproducible, inspectable **digital development package** containing original introductory records about mathematics, the Solar System, biology, civilization, and a provisional message.
- A manifest with file lengths and SHA-256 digests. These detect changes; they **do not correct corruption**.
- A documented proposal for a **physical decoding primer**, not yet fabricated or validated. An experimental panel diagram and 8×8 reference raster/decoder demonstrate a small part of the learning ladder.
- A minimalist website following the visual design of [westonrosch.com](https://westonrosch.com).

**Not yet demonstrated:** decoding without knowledge of human languages and computing, radiation survival, error recovery, archive-health telemetry, physical carrier manufacture, or Fermi Explorer compatibility. The ZIP container is a convenient development transport, **not a proposed alien-readable flight format**.

The prose and draft message are original provisional content, not a comprehensive or representative encyclopedia. Content selection, translations, imagery, recordings, and contributors' permissions require later review.

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

See [roadmap](docs/roadmap.md) and [physical primer](docs/physical-primer.md).