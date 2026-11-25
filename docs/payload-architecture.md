# Payload architecture — decision record (preliminary)

Status: research options. Material selection, fabrication and flight integration remain open. [Centauri Core and Extended edition definitions](archive-editions.md) · [Carrier trade study](mission-integration.md)

## Separate three artifacts

The public website is a **human-readable exhibition**. It may use HTML, fonts, JavaScript, search and navigation. It is for people on Earth and is not a spacecraft payload.

The development package is a **reproducible ZIP** of records plus metadata and SHA-256 checksums. Those checksums detect a mismatch but do not repair damaged bytes. English, UTF-8, JSON and ZIP are assumed. This is not an extraterrestrial-readable format.

The proposed flight archive would be a **physical information artifact** with a non-language-first primer and a suitable carrier. Whether it includes electronics is undecided.

## Candidate implementation

1. Exterior, passive: inspectable orientation marks, counting patterns, physical reference phenomena, an example of a reconstructed image, and how to access the rest.
2. Core, passive: micro-etched diagrams, pictures and/or encoded data on a material selected for the actual exposure conditions. Magnification requirements, accessibility and readout demonstrations matter at least as much as capacity.
3. Optional digital archive: investigate at least two independently protected copies if a payload allocation permits. A simple, clearly specified low-complexity digital edition and a richer compressed edition could coexist. Distinguish *two encoded versions* from *two physical copies*. All media, readout, redundancy, mounting, controller dependencies and environmental survivability remain unselected, untested and subject to engineering review.

The engineering page includes a conceptual exploded view, cross-section and placement study. These drawings illustrate relative component placement and have no physical scale. [Engineering page](https://interstellarnerd8760.github.io/centauri-archive/engineering.html)

## Candidate digital redundancy study (not a hardware decision)

Two different meanings must be separated:

- **Copies:** two or more independent physical specimens carrying the same verified data, ideally avoiding a single common failure.
- **Representations:** a transparent, easily described raw-format core alongside a denser, more convenient multimedia version, potentially with different encoding and error-correction methods.

These approaches can be combined. A prospective configuration could have one permanently inspectable engraved primer, a small raw-data edition with demonstrated image reconstruction, and two independently stored instances of an expanded digital edition. Such a proposal must be evaluated against mass and volume limits, radiation-induced bit errors, thermal and shock exposure, readout-interface obsolescence, long-term material changes, and whether a reader can identify and access the storage without power from the original spacecraft.

A duplicated USB device is *not* an independently interpretable archive. Neither is an error-correcting code a guarantee that data survives tens of thousands of years. Engineers must determine medium and shielding, and the decoding research must establish its interpretation separately.

### Digital volume isn't the same as engraved marks

If 100 images are each 1,000 by 1,000 pixels, the uncompressed image data alone are 12.5 MB at one bit per pixel, 100 MB at eight-bit grayscale, or 300 MB at 24-bit color (decimal MB). Compression and resolution selection change those figures, and metadata and redundancy add overhead. Dense physical digital storage can encode many bits in microscopic areas, while a directly inspectable engraving prioritizes interpretability over bit density. The ZIP is the reproducible Earth-side development format. The carrier trade study gives sizing equations and the protected-record prototype gives record-level encoded sizes. [Photo raster specification and collection measurements](raw-raster-v2.md) · [Protection format](error-correction.md)

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

The Fermi Explorer mission publicly describes a spacecraft-wide payload objective of at least 1 kg and 10 × 10 × 10 cm. Its published plans include a Golden Record copy and solicitation for scientific and artistic contributions. Centauri Archive's potential allocation and integration requirements remain unknown. [Official Fermi Explorer FAQ](https://www.fermiexplorer.org/faqs) · [September 1, 2026 announcement](https://www.fermiexplorer.org/news/fermi-explorer-set-to-launch-humanitys-first-journey-to-another-star)

Sources for design precedents:
- NASA Voyager Golden Record cover: https://science.nasa.gov/mission/voyager/golden-record-cover/
- The Long Now Rosetta Disk: https://rosettaproject.org/disk/technology/
- Fermi Explorer: https://www.fermiexplorer.org/
- Fermi Explorer September 2026 announcement: https://www.fermiexplorer.org/news/fermi-explorer-set-to-launch-humanitys-first-journey-to-another-star

Next gate: a dimensioned, testable primer specimen and an independently recovered image. No flight claims before actual mission requirements and physical testing.
