# Engineering and editorial validation plan

Status: research and development plan, 2026-11-22. This is an independent project with no flight allocation or approval.

## Sources of truth

- archive/ plus archive/catalog.json: actually packaged binary records and metadata.
- curation/images-100.json: exactly 104 numbered editorial targets, including remaining placeholders. A slot is "included" only when a real file is present and cataloged.
- curation/batches/: evidence of which source assets were acquired, with the original URLs and known transformations.
- website/: a human-facing exhibit; it is not a spacecraft flight reader.
- docs/: design assumptions, experimental protocols, failure reports, engineering decisions.

## Acceptance gates

| Priority | Area | Next deliverable | Acceptance test |
| --- | --- | --- | --- |
| P0 | Content integrity | Repeatable image batches | Every included slot maps to a real archived image, a catalog entry, a source URL and exact ZIP bytes; planned slots retain numbered placeholders |
| P0 | Source review | Provenance audit | Source and creator, exact original URL, date when known, reuse basis, processing, caption, alt text, content accuracy and reviewer status recorded for every image |
| P1 | Website validation | Browser smoke tests | Verify all numbered slots, filters, searching, media links, desktop four-column layout, responsive behavior, keyboard focus and no broken images |
| P1 | Maintainability | CSS and JavaScript cleanup | No accidental visual differences in reference screenshots and no old overrides silently masking edits |
| P1 | Extraterrestrial decoding | Independent raw raster experiment | A second decoder reconstructs an identical image using only a format specification, without ZIP/JSON/UTF-8 |
| P2 | Physical primer | Uncoached human trials | Test orientation, counting, scan order, bit meaning and image reconstruction independently; publish wrong answers and ambiguities |
| P2 | Fault tolerance | Damage simulation | Quantify recovery after flipped bits, erased ranges and partial loss; separate error detection from correction |
| P3 | Flight interface | Hardware evidence and actual constraints | Measured geometry, mass, medium, durability, access and duplication; no claims of qualification without evidence |

## Milestone 1 — stable repository and image acquisition

- [x] Reproducible development package with manifest and checksum verification.
- [x] One ordered gallery of 104 positions; unfilled positions are numbered placeholders.
- [x] Source-driven metadata for real photographs, with exact archive copies.
- [x] Initial automatic batch importer, used for three additional NASA images.
- [ ] Add a real-browser smoke test instead of relying only on HTML and JavaScript text checks.
- [ ] Review each acquired photo's legal reuse conditions and scientific caption independently.
- [ ] Keep master images separately from size-constrained prototype derivatives.

Exit gate: zero phantom images, successful tests, no broken downloads or images, reproducible manifest, documented image credits.

## Milestone 2 — basic independently reproducible decoding

- [ ] Specify a small raw bitstream frame: sync, dimensions, ordering, pixel mapping and length.
- [ ] Supply a raw binary sample file and a precise expected image.
- [ ] Implement a second decoder, independently of the encoding implementation.
- [ ] Reject bad dimensions, truncated frames, unsupported versions and bitstream damage.
- [ ] Explain each convention that still depends on the engraved physical primer.

Exit gate: two implementations agree byte-for-byte about the resulting image without the ZIP container.

## Milestone 3 — primer interpretation study

- [ ] Draw a text-free primer specimen with asymmetric orientation and repeated examples.
- [ ] Produce a printable specimen and a test protocol that does not disclose the design.
- [ ] Ask several unfamiliar human participants to reconstruct the image.
- [ ] Score each stage separately: recognition, numbers, orientation, length, scan order, contrast.
- [ ] Test rotated and partially erased specimens; log failures and revisions.

Exit gate: documented, repeatable performance in human trials. This does not prove alien understanding.

## Milestone 4 — representative content

- [ ] Acquire remaining slots in verified batches; no copyright or provenance shortcuts.
- [ ] Review scientific, historical and cultural descriptions with relevant expertise.
- [ ] Include ordinary human experiences and a range of ecosystems, not just famous objects.
- [ ] Establish a transparent consent and rights process for identifiable people and culturally sensitive material.
- [ ] Select the subset that fits a measured carrier and readout budget.

Exit gate: every selected image has a purpose, correct description, demonstrable lawful acquisition and exact bytes.

## Milestone 5 — physical engineering and external review

- [ ] Get official spacecraft mass, volume, mechanical, environmental and interface requirements.
- [ ] Compare passive engraved media and independently protected digital-copy candidates.
- [ ] Build physical specimens and measure feature dimensions, optical readability and damage.
- [ ] Demonstrate recovery from damage instead of just detecting corruption.
- [ ] Obtain independent scientific, archival, cultural and engineering review.

Exit gate: measured evidence and documented limitations sufficient for a proposal, not an implied flight approval.

## Rules for claims and results

- A universal binary notation does not exist simply because there are two distinguishable states.
- JPEG, ZIP, Unicode, modern file systems and microcontrollers are human-specific conventions.
- A checksum detects changed data; it cannot reconstruct a lost file without a separate recovery scheme.
- Human blind tests are useful engineering evidence, not proof of extraterrestrial readability.
- Proposed architecture, encoded prototype, manufactured artifact and flight-qualified hardware are separate milestones.
- Every release must distinguish included source records from planned editorial subjects.

Review this plan before allocating effort to new website effects. Reliability, semantics, sourcing and independent interpretability outrank decorative complexity.

See roadmap.md for earlier project history and broader release staging.
