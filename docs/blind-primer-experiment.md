# Blind interpretation experiment B

Status: untested, printable 2D mock-up, not an engraved carrier or proof of extraterrestrial readability.

The text-free specimen is [primer-blind-panel.svg](primer-blind-panel.svg). It pairs quantities (including an empty group) with three two-state positions, pairs the two physical states with image cells, and shows three rectangular rasters with asymmetric patterns. Repeated paired examples are intended to make the row grouping, dimensions and correspondence inferable. They do not demonstrate byte boundaries, frame synchronization, a physical unit of measurement, or the interpretation of a photograph. Black ink is the marked input state (1); the paired output cell is white, consistent with the raw raster v1 convention. The unmarked input state (0) maps to a black output cell. This mapping is illustrated, not proven inferable. Neither panel has been fabricated or tested.

## Blind protocol

Give each participant the specimen only (without the filename, captions, source code, or discussion of binary). Ask them to describe any rules they see and reconstruct an unseen rectangular pattern from a separate grouped stream. Do not confirm guesses before they submit. Use fresh volunteers for subsequent revisions, and record prior familiarity with binary and images, since human conventions bias this test.

Score each of these separately:
- Identifies the two symbol states.
- Associates grouped quantities with corresponding three-position patterns, including zero.
- Infers positional weights and orientation, demonstrated on a previously unseen quantity.
- Infers row length and number of rows from physical marks.
- Reconstructs an unseen asymmetric rectangular image without a hint.
- Explains ambiguities or alternate interpretations.

Record attempted answers, time, hints (if any), alternate interpretations and failure modes. Repeat with rotated, mirrored and partly obscured copies. Pre-register the task and scoring before collecting results. No real participant outcomes are claimed.

## Separate software interoperability test

Run `node tests/raw_raster_independent.cjs`. The JavaScript implementation follows the existing v1 byte layout without importing the Python decoder. It checks the 29-byte reference frame, dimensions, all 128 possible individual bit flips in the payload and complement, truncation, excess bytes, nonzero padding and an explicit common-mode corruption counterexample. The fixed vector and single-bit cases were exercised during development; the full Node test and CI still need to run.

Next: teach the complete frame using physically paired examples, add grayscale and scale demonstrations, and investigate actual error correction with spatially separated redundancy. Preserve the original ZIP and photograph masters.
