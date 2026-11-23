# Digital package v1

The container is a single-disk, unencrypted ZIP with stored (uncompressed) members. manifest.json is UTF-8 JSON at the root. All record bytes live under content/. No directory entries are necessary. Any standard ZIP reader can list or copy them. This container assumes a recovered byte stream. Physical framing is a separate research question.

| Field | Meaning |
| --- | --- |
| format_version | Integer 1. Readers reject unknown versions. |
| archive_version | Three dot-separated decimal integers identifying the content edition. |
| files | Nonempty array of record objects. |
| path | Unique case-sensitive ASCII path starting with content/. Each component starts with a lowercase letter or digit and contains only lowercase letters, digits, dots, underscores or hyphens. |
| media_type | Nonempty media type string describing the record. |
| size | Nonnegative integer count of the record's bytes. |
| sha256 | SHA-256 digest of those exact bytes in lowercase hexadecimal. |

The files array covers every member except the manifest itself. A verifier rejects missing, unexpected or duplicate members, invalid metadata, unsupported containers, size mismatches and bad digests. Changes to a package and its manifest together require a separately trusted reference digest to detect. Inspection displays the inventory without checking payload digests.

## Reference serialization

Order files by ASCII path, write the manifest first and the records in inventory order. Encode JSON with sorted keys, two-space indentation and a final LF. Set each member's timestamp to 1980-01-01 00:00:00, Unix creator and mode 0100644. Omit archive comments, entry comments and extras. Every record is stored verbatim. Build inputs are archive/ and the integer-only plate recipe in tools/plate.py. For v1 the reference reader limits the container and total member bytes to 10,000,000 each.

Example of a valid entry for a zero-byte text record:

```json
{"path":"content/example.txt","media_type":"text/plain","size":0,"sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}
```
