# Fermi Explorer: source-based mission constraints and archive implications

Status: research notes (22 November 2026); **not flight requirements for Centauri Archive**. This project remains independent and has no approved Fermi Explorer payload slot. This brief records what the mission team and its external feasibility analyst published, and explicitly separates source versions.

## Three sources, three sets of ground rules

| Source | Arrival objective | Budget | What it is |
| --- | --- | --- | --- |
| PSI, *Interstellar Precursor Mission to Alpha Centauri: Technical Feasibility Assessment* (July 2026), cover and Table 3 (printed pp. 6–7) | Pass within 2,600 AU of Alpha Centauri AB barycenter within **500,000 years** | Initial **<$10M** study target | 81-page external mathematical feasibility assessment, prepared for Fermi Explorer; produced by PSI's autonomous research platform; the report states **no comprehensive human peer review** |
| Fermi Explorer official FAQ (accessed 22 November 2026) | Within 1% of target separation, about 2,600 AU, **within 80,000 years** | **<$15M** current primary objective | Public mission objectives and solicitation descriptions |
| Fermi Explorer open engineering calculator, build 185 (accessed 22 November 2026) | Within 2,600 AU **within 100,000 years** | Interactive architectural trade studies | Explicitly preliminary first-order calculator; not flight hardware requirements |

Do not silently merge these into a single allegedly confirmed design requirement. For our future flight proposal, obtain written confirmation of the currently applicable version. Even the official FAQ is public intent, not an interface control document (ICD).

Links:
- Official mission FAQ: https://www.fermiexplorer.org/faqs
- Public calculator: https://fermiexplorer.github.io/
- Calculator code, audit comparisons and simulation model: https://github.com/fermiexplorer/fermi
- PSI final report is linked from the official FAQ and appears in the mission repository's `audit/psi/` reference collection. The 81-page July PDF was separately provided to project review; **do not copy or redistribute that uploaded PDF without permission**.

## What PSI's assessment actually finds

- The minimum Earth-departure impulse for the modeled geometry occurs at a roughly **73,012-year** arrival epoch: heliocentric cruise speed **23.64 km/s**, **2.48 degrees below** the ecliptic (printed Executive Summary and Sections 2.4 and 9).
- Multi-revolution solar-electric **perihelion pumping**, with repeated powered arcs near **0.42 AU**, reaches a viable escape trajectory in the model; the study assumes a thermal power cap and says that the specific component configuration still requires qualification.
- The **100-kg vehicle does not close from LEO** on any 12-year operational trajectory the analysis found. From a **GTO** rideshare the approximately **100–110 kg** configuration closes in the studied model, with margins. GTO is a *recommended deviation* from PSI's original LEO ground rule.
- The estimated median conventional program cost is **$15.7–16.6 million**, not the initial $10 million study target. The report describes the dominant gap as operations, bus and program margin.
- The PDF explicitly models **at least 1 kg / 1U as the mission's total payload**, not as a slot awarded to this archive. It does not specify where our artifact could mount or how it would be retrieved or read.
- The report's propulsion/trajectory model does **not** design or qualify a passive archive. In particular, it does not certify archival material survival, decoding, impact resistance, mounting or allocated media storage.

## The newer calculator is not numerically identical to the July paper

The mission calculator and current FAQ describe a ~**77,500-year** preferred pumped-architecture arrival epoch, rather than simply adopting the PSI report's 73,012-year impulsive/departure optimum. The calculator models a different within-class epoch trade and thermal conditions. The webpage labels its model preliminary; its simulations must not be mistaken for an approved flight profile.

Read the precise version, architectural assumptions, and constraint before citing any single arrival time, spacecraft mass or thermal value.

## Implications for Centauri Archive

1. **Passive-first is sensible, not yet required.** Fermi says the spacecraft will likely lose power and communication after leaving the Solar System. A durable engraved first-read primer could remain interpretable without a surviving controller, unlike a digital reader that needs power and circuitry.
2. **Do not claim the entire 1U/1kg.** The public goal is shared among scientific, donor and artistic candidates; the archive's allocation is completely unknown. Establish a tiny mass/volume target only after Fermi specifies it.
3. **The thermal/structural envelope remains unknown.** Repeated passes near 0.42 AU, launch loads, radiation, micrometeoroids, and ultra-long-duration exposure make exposure and mounting central risks. The temperature of the archive carrier itself is **not** supplied by the trajectory report.
4. **An encounter is not a handoff.** The spacecraft may pass thousands of AU from the system barycenter, not land or park near an observer. Design for discoverability, potential retrieval and physically legible information without assuming a future receiver exists.
5. **A browser ZIP is not a flight format.** Prioritize a visible physical primer, a minimal raw encoding with examples, recovery tests, physically justified redundancy, and source/rights tracking for media. Supplemental digital storage is optional until its long-term readout can be explained.
6. **Media curation and payload selection are separate.** We can assemble more images/audio in the digital archive without promising that every byte will fit on the spacecraft.

## Questions for the mission team (only after message approval)

- Is there an opening for an independent passive scientific/cultural archive, and which solicitation would cover it?
- What is the current mass/volume/geometry allowance **for a single contributor**, not the whole spacecraft?
- Will the artifact be externally visible and directly inspectable, or protected inside a structure?
- What are the payload location's expected thermal, vibration, radiation and particle-exposure bounds?
- Can an etched passive plate or layered optical medium be considered, and how are safety, cleanliness and provenance reviewed?
- What are the actual proposal dates, test milestones, documentation and integration rules?

**Contact policy:** No emails, direct messages, applications or external submissions are authorized by this document.
