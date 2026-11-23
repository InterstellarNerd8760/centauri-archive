# Payload architecture — decision record (preliminary)

Status: research options; no hardware selected, fabricated, integrated or flight-approved.

## Separate three artifacts

The public website is a **human-readable exhibition**. It may use HTML, fonts, JavaScript, search and navigation. It is for people on Earth and is not a spacecraft payload.

The development package is a **reproducible ZIP** of records plus metadata and SHA-256 checksums. Those checksums detect a mismatch but do not repair damaged bytes. English, UTF-8, JSON and ZIP are assumed. This is not an extraterrestrial-readable format.

The proposed flight archive would be a **physical information artifact** with a non-language-first primer and a suitable carrier. Whether it includes electronics is undecided.

## Candidate implementation

1. Exterior, passive: inspectable orientation marks, counting patterns, physical reference phenomena, an example of a reconstructed image, and how to access the rest.
2. Core, passive: micro-etched diagrams, pictures and/or encoded data on a material selected for the actual exposure conditions. Magnification requirements, accessibility and readout demonstrations matter at least as much as capacity.
3. Optional, active or dense digital: a memory module only when its physical interface, acquisition process, error correction, mounting and readout can be clearly specified and are justified by mission constraints.

The carrier drawing on the homepage is an artistic **concept study**. It is not a dimensioned schematic or a proof of decodeability.

## Experimental primer ladder

- Notice repeated marks and orient the pattern.
- Infer quantities and relationships from groups.
- Establish a reproducible reference for length or time.
- Demonstrate a binary distinction with physical symbols.
- Pair a known grid image with its ordered symbol sequence.
- Establish framing, length, boundaries and error-control encoding of larger records.
- Build scientific concepts from measured physical relationships toward Earth, biology and cultural information.

Recognizing the data is not the same as understanding human language. Independent reading experiments must measure each step separately.

## Flight-design questions

- What mass and envelope may an independent passive archive occupy?
- Is the payload externally inspectable, or enclosed deep inside the spacecraft?
- Does retrieval depend on electricity, memory technology or a surviving controller?
- What are the thermal, radiation, vibration and impact environments?
- How might a damaged or rotated specimen be detected and interpreted?
- What is the redundancy plan and how will erasure correction be demonstrated?
- What experiments could validate readability and data recovery within the available schedule?

The Fermi Explorer mission publicly describes a goal for at least a 1 kg, 10x10x10 cm payload **for the spacecraft**, not for this project. Its published plans also include a Golden Record copy and a solicitation for other scientific and artistic contributions. Do not infer a payload slot or approval from those announcements.

Sources for design precedents:
- NASA Voyager Golden Record cover: https://science.nasa.gov/mission/voyager/golden-record-cover/
- The Long Now Rosetta Disk: https://rosettaproject.org/disk/technology/
- Fermi Explorer: https://www.fermiexplorer.org/
- Fermi Explorer September 2026 announcement: https://www.fermiexplorer.org/news/fermi-explorer-set-to-launch-humanitys-first-journey-to-another-star

Next gate: a dimensioned, testable primer specimen and an independently recovered image. No flight claims before actual mission requirements and physical testing.
