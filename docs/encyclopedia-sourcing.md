# Editorial acquisition: how to build a deeper encyclopedia without copying noise

Status: research protocol, 22 November 2026. The collection remains incomplete and unreviewed.

The goal is neither to preserve the whole public web nor to translate huge volumes of copyrighted encyclopedia text into binary. An archive built for an unknown future reader should start with intelligible definitions and images, then use concise explanations of the most generalizable facts.

## Why use Grokipedia at all?

Grokipedia, Wikipedia and other tertiary encyclopedias are useful **starting indexes** of subjects, terms and citations. They are not independent confirmation of facts. We can consult a Grokipedia page for a broad topic list and then verify individual statements against primary scientific sources; the final article should be an original, attributed synthesis with clear units, context and limitations.

The current SpaceXSI/xAI terms explicitly designate Grokipedia material under the SpaceXSI Community License, with some articles also marked CC BY-SA 4.0. The licenses are not interchangeable. An automated bulk mirror or wholesale copying is NOT part of this prototype. Each reuse or adaptation requires a rights and attribution check. As of this research pass, direct retrieval of example Grokipedia pages was not reliable; **no Grokipedia prose has been ingested**.

Verified general terms source: https://x.ai/legal/terms-of-service

Wikipedia's CC BY-SA 4.0 material may be reused according to its conditions; each embedded image has separate terms. Wikidata provides structured identifiers under CC0. For direct media, individual Wikimedia Commons files and agency-specific usage rules must be reviewed.

## Article acceptance pipeline

1. Define one question: what must an unfamiliar observer understand?
2. Identify prerequisites: numbers, scales, chemistry, astronomy, cells, etc.
3. Compare two or more overview sources, potentially Wikipedia and Grokipedia, for missing concepts, not for prose to duplicate.
4. Verify quantitative statements and core scientific claims from original measurement sources or authoritative syntheses.
5. Write a fresh explanatory article with diagrams or measurable observations; label disputes, hypotheses and unknowns.
6. Record exact references, timestamps/revisions when relevant, license/attribution obligations, author or editorial status in `archive/catalog.json`.
7. Conduct accuracy and cultural review before marking content released.
8. Test how a reader navigates from the physical primer to this information.

## High-value content backlog

The next editorial expansion should cover the origins and evolution of the Solar System; spectra and measurable stars; atoms, light and the physical units; Earth geology and water; photosynthesis and microbial ecosystems; the origin and evolution of biological diversity; human development and health as scientific observation; agriculture and food; inventions and engineering; the origins and diversity of languages and writing; cultural expression and daily experience; and an explicitly attributed selection of human messages.

These are topics to research, **not assertions that we have already acquired them**.

## Separate media formats

Keep the source/master, the small website derivative and the flight encoding distinct. A high-resolution color JPEG can be useful on Earth, but it does not help an unknown reader unless the decoding primer teaches JPEG or provides a simpler reconstructable representation. The proposed `curation/images-100.json` gives 100 slots, while the actual verified archive includes only three original diagrams. No third-party images or field recordings are represented as acquired.

The near-term test is to reconstruct one simple image from a self-describing physical or raw-bit prototype. The long-term goal is to preserve representative knowledge, not maximize the number of megabytes.
