# Digital transport package v1

**This format is a human development and exchange format, NOT the proposed
physical or alien-decoding format.**

The container is a single-disk unencrypted ZIP with stored, uncompressed
members. `manifest.json` is UTF-8 JSON at the root. Every record lives under
`content/`. The current edition contains UTF-8 English texts, editorial metadata in JSON, original SVG diagrams, and sourced JPEG photographs. The development tool can also package PNG, WebP, WAV and Ogg media. Recorded audio has not yet been included.

| Field | Meaning |
| --- | --- |
| format_version | Integer 1; unknown versions rejected |
| archive_version | Three dot-separated decimal integers |
| files | Nonempty array of record metadata |
| path | Unique case-sensitive ASCII path under content/ |
| media_type | Nonempty media type of the record |
| size | Nonnegative number of bytes |
| sha256 | Hexadecimal digest of the exact record bytes |

The manifest inventories every ZIP member other than the manifest itself.
The verifier rejects missing, unlisted or duplicate members, invalid
metadata, unsupported compression/encryption, changed lengths and digest
mismatches. It detects corruption; it does not correct data.

## Reproducibility

Order files by ASCII path. Write the manifest first, followed by content in
path order. Serialize JSON with sorted keys, two-space indentation and a final
LF. ZIP member timestamp is 1980-01-01 00:00:00, Unix creator and regular-file
mode 0100644. Omit comments and extras. Reference readers enforce a
80,000,000-byte container and total member-byte limit.

This format requires prior knowledge of ZIP, bits/bytes and UTF-8. An experimental raw monochrome-image frame now exists separately from this ZIP
(see [raw raster experiment](raw-raster-experiment.md)), but its byte conventions
have been implemented independently in software. Physical teaching and carrier readout still require experiments.
Physical decoding remains a research milestone. Neither CRC nor SHA-256 is a substitute for explaining encoding.

All verified files are now copied to the static site's records directory, so the browser reader can display SVG and common image/audio files without changing source bytes. The catalog is stored at `content/catalog.json` in the ZIP. The browser interface is not a flight reader.

The 80 MB limit is a **software prototype cap**, not a physical payload
allocation. A compact package may use fewer bytes without artificial padding.
