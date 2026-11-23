# Digital transport package v1

**This format is a human development and exchange format, NOT the proposed
physical or alien-decoding format.**

The container is a single-disk unencrypted ZIP with stored, uncompressed
members. `manifest.json` is UTF-8 JSON at the root. Every record lives under
`content/`. The current edition's records are UTF-8 English text.

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
10,000,000-byte container and total member-byte limit.

This format requires prior knowledge of ZIP, bits/bytes and UTF-8. The
physical decoding and standalone raw framing scheme are future research
milestones. Neither CRC nor SHA-256 is a substitute for explaining encoding.

The 10 MB limit is a **software prototype cap**, not a physical payload
allocation. A compact package may use fewer bytes without artificial padding.
