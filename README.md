# Centauri Archive

Centauri Archive is an independent engineering and curation project developing a durable record of Earth, life, humanity and foundational knowledge for potential interstellar carriage. Its [Fermi Explorer proposal](docs/fermi-explorer-proposal.md) requests a feasibility collaboration. There is no mission affiliation, approval, payload allocation, integration agreement or verified project-specific spacecraft requirement.

| Proposed edition | Provisional logical content | Purpose |
| --- | --- | --- |
| **Centauri Core** | Approximately 100 MB or less | Recommended baseline. A self-contained mathematical and scientific primer, existing photographs, diagrams, essential encyclopedia, visual vocabulary, selected cultural records and messages, and recovery specifications. |
| **Centauri Extended** | Investigate approximately 64 GB or more | A self-contained copy of Core with optional Wikipedia-derived English article text, broader knowledge and additional media where feasible. |

Physical framing, correction overhead, copy count, mounting and shielding need separate accounting. [Edition definitions](docs/archive-editions.md) · [Integration and questionnaire](docs/mission-integration.md)

## Current development package

The uncompressed ZIP contains 104 curated, credited photographic records, 44 encyclopedia drafts, four original science diagrams, preliminary records, one draft message and an experimental visual vocabulary. Its manifest inventories every member by length and SHA-256. The development package uses an 80 MB software ceiling and assumes conventional Earth-side tools.

Separate experiments reconstruct real photos from a versioned raster, decode a codeword with parity and recover damaged records within bounded Reed–Solomon guarantees. A generated visual primer proposes a path from observable structure to raster reconstruction. The encyclopedia records its editorial status per article. Physical fabrication, first-read trials, independent editorial review and mission qualification remain open.

The static site presents the encyclopedia, image library, decoding experiments, engineering study and mission proposal. Read the deployed [Centauri Archive website](https://interstellarnerd8760.github.io/centauri-archive/) or build a preview of the current branch locally.

## Build and verify

Python 3.10+ builds the package and site with the standard library. Install the optional pinned Pillow dependency to generate photographic derivatives and run full photograph tests. Node.js runs independent decoders and calculator checks.

```sh
python3 tools/archive.py build build/centauri.zip
python3 tools/archive.py inspect build/centauri.zip
python3 tools/archive.py verify build/centauri.zip
python3 tools/build_site.py
python3 -m http.server 8000 --directory build/site
```

After extracting the ZIP, start at `content/primer/start.txt` for the transport package's assumptions. The website is optional for examining the contents.

## Reproduce the experiments

```sh
python3 -m pip install -r requirements-raster.txt
python3 -m unittest discover -s tests -v
node tests/raw_raster_independent.cjs
node tests/capacity.cjs
```

- Build one or more derivative representations of the four selected photographs. Inspect and reconstruct them in Python and Node.js. Recompute sizes across all 104 source photos at multiple resolutions. [Raw raster v2 specification and commands](docs/raw-raster-v2.md)
- Reproduce the annotated and text-free A–E primer panels from structured data. Use the separate held-out exercise and protocol for an interpretation trial. [Mathematical primer and instructions](docs/primer-ladder.md) · [Visual vocabulary](docs/visual-vocabulary.md)
- Encode a record, recover bounded errors and erasures, and rerun the seeded corruption scenarios. [Correction specification and commands](docs/error-correction.md)
- Transform an attributed synthetic snapshot separately from the normal build. [Optional Wikipedia research and reproduction procedure](docs/wikipedia-preservation.md)

The original [monochrome raster v1 experiment](docs/raw-raster-experiment.md) remains available.

## Repository map

| Path | Contents |
| --- | --- |
| `archive/` | Catalog, preserved photographs, diagrams, encyclopedia, vocabulary, draft texts and message |
| `curation/images-100.json` | Stable numbered photographic plan, including acquired assets and status |
| `docs/` | Mission proposal, editorial policies, engineering studies and experimental specifications |
| `tools/`, `tests/` | Reproduction tools, independent implementations and automated validation |
| `website/` | Static presentation site, assembled to `build/site` |

Photo credits, source links and rights statements are recorded in the catalog. Editorial drafts and project artwork with pending licensing decisions carry that status. See the [roadmap](docs/roadmap.md), [encyclopedia editorial framework](docs/encyclopedia-mvp.md), [photo provenance](docs/photographic-acquisitions.md) and [source policy](docs/source-policy.md).
