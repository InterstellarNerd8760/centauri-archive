# Editorial acquisition: how to build a deeper encyclopedia without copying noise

Editorial protocol and coverage audit, 24 November 2026. Independent human review is pending.

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
6. Add exact references, access dates, supported paragraph numbers, and the consulted version when applicable. Record article credit and rights in `archive/encyclopedia/index.json`. Keep media-specific rights and provenance in `archive/catalog.json`.
7. Conduct accuracy and cultural review before marking content released.
8. Test how a reader navigates from the physical primer to this information.

## Baseline audit and first editorial pass

The baseline includes 29 articles, with source leads on four entries from PR #12. The sections below describe the coverage review and remaining work. Source checks in this pass focused on life, human biology, Earth and physical science.

| Baseline IDs | Finding and editorial work |
| --- | --- |
| CA-01.001–004 | The mathematics sequence sets up count, measure and binary. It needs examples of zero, ratios, positional notation, signed quantities and what an encoded number measures. The experimental physical primer addresses part of that sequence. |
| CA-02.001–005 | Matter, bonding and energy assume terminology a new reader needs defined. The Solar System formation entry now maps claims to sources. The added radiation, stellar evolution and heat entries supply prerequisites for later topics. Cosmology, gravity, quantitative units and chemical reactions need dedicated coverage. |
| CA-03.001–004 | The planetary profile's phrase “solid interior structure” could imply a wholly solid Earth. The revision identifies the liquid outer core. The water entries overlap; one introduces the cycle and the other addresses storage and transport. The numerical water phase examples and the broad atmosphere entry still need independent sources and explicit conditions. |
| CA-04.001–005 | Cells, DNA and the genome entries repeated several concepts and compressed membranes, organelles, metabolism and inheritance into generalizations. Revisions clarify the roles of cells, inherited DNA and gene expression while keeping the stable IDs. Additional entries cover the origins of life, RNA and proteins, energy pathways, organism groups, and biodiversity. Future detail should cover life-history diversity and additional ecosystems. |
| CA-05.001–004 | Two anatomy entries provided overlapping lists of systems with little explanation of how they work. The organization entry now serves as the prerequisite for system-specific articles with a flow schematic and correctly distinguished photographs, models and microscopy records. The older brief development and cognition entries still need substantive claim checks. |
| CA-06.001–002 | The existing history overview compresses milestones into one timeline with few geographic examples. Check date ranges and oral and archaeological evidence independently. Develop regionally balanced accounts of migration, agriculture, writing, institutions, exchange, cooperation and conflict. |
| CA-07.001–003 | Technology entries give broad descriptions. Next passes should explain mechanisms with documented examples of tools, manufacturing, agriculture, energy, communication, medicine, computation and instrumentation. |
| CA-08.001 | A single article covers daily life and expression. Separate music, education, play, household and community life, architecture, philosophical and religious traditions. Obtain culturally informed review and community context where possible. |
| CA-09.001 | Check history against original records and tie mission context to the formal proposal and actual engineering status. |

## Second source-check pass

Edition 0.3 revises and cites the 20 drafts remaining from edition 0.2 and adds 12 related articles. Each of the 56 articles has source references mapped to its body paragraphs and definitions for two terms. Article IDs, photographic links and supplementary records from earlier editions remain available. Original explanations are based on named sources. The record of each change appears in the article's revision history.

- The mathematics entries add worked examples of counting, arithmetic, binary, scale and powers. The physical sciences use those prerequisites to explain the structure of atoms, gravity, spectra, and conservation in chemical reactions.
- The Earth entries distinguish climate from weather and terrestrial water phases from water transport. New articles explain ocean–atmosphere exchanges and the difference between weathering and erosion.
- The human-development and language entries distinguish observations of particular people from claims about humans generally. The history entries use identified evidence from Morocco, North America, Mesopotamia and China, with uncertainties about timing and representativeness stated where relevant.
- The technology and culture entries add instrument calibration, a stored-program model of computing, and the role of communities in documenting living traditions. The mission entry grounds project claims in the published repository proposal and uses NASA material for the historical precedents.

Independent subject and cultural reviewers still need to compare article passages, glossaries and linked media with their references. Priority cases include historical dating, science simplifications and cultural interpretations. The source checks do not determine publication rights or the engineering status of archive experiments.

## Review before release

- Read the exact source for each factual statement and follow references through to their supporting evidence when practical. Record disagreements and limits in the article. Add units, reference conditions and uncertainty for quantitative claims.
- Open each linked photo or diagram and read the catalog provenance. Distinguish specimen, model, processed image and schematic. Add comparable examples when one person's body, language or culture could be treated as representative.
- Record source check, rights and independent review for the same revision. Retain evidence for corrections and unresolved comments.

## Separate media formats

Keep the source/master, website derivative and experimental flight encoding distinct. JPEG decoding requires a convention a future reader would have to reconstruct. The image plan at `curation/images-100.json` tracks 104 photographic records and the catalog links their acquired derivatives and provenance. Drawings and engineering diagrams have separate catalog entries. Recorded audio is a future acquisition task.

The near-term test is to reconstruct one simple image from a self-describing physical or raw-bit prototype. The long-term goal is to preserve representative knowledge, not maximize the number of megabytes.
