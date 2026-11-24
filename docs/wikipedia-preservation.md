# Wikipedia preservation research for Centauri Extended

Centauri Extended could preserve current English Wikipedia article text alongside a complete, separately recoverable Centauri Core. The preferred coverage is the main namespace, at predictable revisions, including article bodies and useful equations and references. The 64 GB logical study target is provisional. The source download, cleaned derivative, and protected carrier image have separate storage requirements.

## Source comparison

Metadata checked on 2026-11-24. Sizes below describe specific upstream objects, where available. No full snapshot was downloaded and the uncompressed English totals for the compared snapshots remain unmeasured.

| Source | Compressed bytes or published size | Coverage and acquisition | Decode and reproduction |
| --- | --- | --- | --- |
| Wikimedia legacy `enwiki-20261101-pages-articles-multistream.xml.bz2` | 25.2 GB as displayed by Wikimedia | Current wikitext revisions, including several support namespaces. Filter namespace 0 and select non-redirect pages. The dump run publishes MD5 and SHA-1. | bzip2, multistream XML and MediaWiki-specific markup. Reproducing rendered article text requires a renderer, templates, modules and a versioned configuration. The original byte stream is independently identifiable by checksum. |
| Wikimedia monthly MediaWiki Content File Exports, `mediawiki_content_current` | Exact size to inventory by dated part. The English 2026-11-01 run publishes SHA-256 for each part. | Current revisions at the documented cutoff. Includes non-article pages. Use the `current` dataset and retain its manifest. | bzip2 and MediaWiki XML. Rendered text has the same template and module dependency as the legacy export. The fixed cutoff makes source selection easier to reproduce. |
| Kiwix `wikipedia_en_all_nopic_2026-06.zim` | 52,690,706,555 bytes (52.69 GB, 49.07 GiB) per Metalink | Kiwix describes `nopic` as full articles without pictures. The `mini` file contains introductions and infoboxes and is unsuitable for the intended coverage. Count actual article entries and verify revision provenance before reuse. | ZIM clusters, indexes, media types, and rendered HTML. Extract with openZIM tools and retain the ZIM metadata. The dated `.meta4` publishes a SHA-256. Exact expanded size depends on whether counting content entries alone or every file. |
| Wikimedia Enterprise `enwiki_namespace_0` Snapshot API | Wikimedia describes the full English HTML-plus-wikitext snapshot as roughly 150 GB compressed. Use Snapshot Info and HEAD for a selected edition. | Full rendered article HTML plus wikitext, page and revision identifiers and source license metadata. A dated chunk is suitable for the first test. Official documentation describes earlier revisions duplicated in some snapshots and possible deleted entries. | gzip, tar, NDJSON and rendered HTML. The implemented prototype uses this source model and streams one tar member. Source date, manifest and local SHA-256 together identify the material processed. |

Wikimedia legacy dump SHA-1 for the exact file in the table is `bfdb7ead45e262d7b9d55d86c8958789e7efd1ae`. The Kiwix Metalink SHA-256 for the exact file in the table is `441a56d9e05b2d98f8ae9acb7986a513ed47904d73852c92dc6b7d50baa122e5`. The older MD5 and SHA-1 entries can check transfers against their publisher's listing. Use SHA-256 as the archive's own integrity identifier.

- [Wikimedia English 2026-11-01 dump index](https://dumps.wikimedia.org/enwiki/20261101/) · [published SHA-1 list](https://dumps.wikimedia.org/enwiki/20261101/enwiki-20261101-sha1sums.txt) · [Wikimedia dump contents](https://meta.wikimedia.org/wiki/Data_dumps/What's_available_for_download)
- [Wikimedia Content File Exports documentation](https://wikitech.wikimedia.org/wiki/MediaWiki_Content_File_Exports) · [English 2026-11-01 current export SHA-256 list](https://dumps.wikimedia.org/other/mediawiki_content_current/enwiki/2026-11-01/xml/bzip2/SHA256SUMS)
- [Kiwix snapshot index](https://download.kiwix.org/zim/wikipedia/) · [exact Kiwix Metalink](https://download.kiwix.org/zim/wikipedia/wikipedia_en_all_nopic_2026-06.zim.meta4) · [Kiwix content variants](https://get.kiwix.org/en/faq-items/what-do-mini-nopic-and-maxi-mean-in-the-wikipedia-zim-files/) · [openZIM tools](https://github.com/openzim/zim-tools)
- [Wikimedia Enterprise Snapshot API](https://enterprise.wikimedia.com/docs/snapshot/) · [article schema](https://enterprise.wikimedia.com/docs/data-dictionary/) · [English snapshot size guidance](https://enterprise.wikimedia.com/project-data/wikipedia-api/)

A 52.69 GB ZIM would leave about 11.31 GB of a decimal 64 GB logical target before other logical content and indexes. This arithmetic applies to the upstream ZIM only. Article text can be much smaller than rendered HTML, while article structure, citations, and repeated provenance add storage. Take a stratified article sample and measure actual UTF-8 output and compression ratios before sizing a full derivative. Include short and long articles and collections with formulae, lists, tables, dense citation lists and several scripts. Record the total expanded upstream bytes, normalized body text bytes, full article record bytes, ancillary index bytes and protected storage separately.

## Reuse and attribution

Review the Wikimedia Foundation Terms of Use section 7 and CC BY-SA 4.0 before distribution. For Wikipedia text, the applicable license commonly permits modification and redistribution with credit, preserved required notices, an indication of changes and compatible share-alike licensing for adaptations. The Wikimedia Terms provide attribution through a link to the reused article, a qualifying stable copy or a list of authors. Imported contributions and page-specific notices can entail additional obligations. Avoid assuming a Kiwix packaging license covers all its contents or that every text revision is available under GFDL. Scan for non-free or separately licensed material, including quoted text and contributions imported from outside the project.

The research format retains original license objects, canonical article, revision and history URLs, provided rights/attribution fields, visible article prose (including in-article notices) and HTML license link relations. Full capture of special notices and upstream contributor histories requires a separate review and export. For a physical copy intended to operate without access to the web, preserve contributor and imported-work attribution and license text that meets the applicable requirements offline. Budget for those records. Document omissions and version-specific changes and attach notices to their records. Do this review before publishing or manufacturing any Wikipedia derivative.

- [Wikimedia Foundation Terms of Use, section 7](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use#7._Licensing_of_Content) · [CC BY-SA 4.0 license text](https://creativecommons.org/licenses/by-sa/4.0/legalcode) · [Wikipedia reuse guidance](https://en.wikipedia.org/wiki/Wikipedia:Reusing_Wikipedia_content)

## Reproduce the small experiment

The fixture contains original test-only prose, dedicated to the public domain under CC0 1.0, and identifiers under `example.invalid`. It uses the input schema without copying a Wikipedia article. The fixture includes example mathematics, navigation, references, a redirect, a discussion entry and superseded or suppressed revisions. The ordinary site and archive builds never download or ingest Wikipedia. Tests use local input and a simulated HTTP response.

```sh
python -m unittest discover -s tests -p 'test_wikipedia_snapshot.py' -v
python tools/wikipedia_snapshot.py transform \
  tests/fixtures/wikipedia-synthetic.ndjson build/wikipedia-experiment \
  --input-format ndjson --project syntheticwiki \
  --snapshot-id centauri-fixture-v1 --snapshot-date 2026-11-24 \
  --source-url https://archive-fixture.example.invalid/snapshot/centauri-fixture-v1 \
  --expect sha256:31d1a70e4bb2f24c946b575050d4b337e8a4af2627af356b0ddbe51bdda34f70
```

Measured on Python 3.12.14 with `--expect` as shown:

| Quantity | Result |
| --- | ---: |
| Fixture bytes, UTF-8 NDJSON | 5,154 |
| Fixture bytes with gzip level 9 and `mtime=0` | 1,166 |
| Input rows | 7 |
| Extracted article records | 2 |
| Extracted body blocks, UTF-8 bytes | 202 |
| `articles.ndjson` bytes | 2,792 |
| `articles.ndjson` bytes with gzip level 9 and `mtime=0` | 915 |
| `manifest.json` bytes | 1,130 |
| Total uncompressed derivative including manifest | 3,922 |

The SHA-256 of `articles.ndjson` was `82e3f5bde31f935fc4cdd7d56d4b428a8c8a5648991962ba2dff108e2629987e`. The tiny fixture's ratio is specific to these inputs. A separate live acquisition check fetched only the 248,160-byte Wikimedia legacy checksum list using `fetch --max-bytes 1000000`, then located the source checksum listed above.

## Acquire and process a future source

1. Choose the project, namespace, release date, snapshot or chunk identifier, stable source URL and exact bytes. For Enterprise, use `enwiki_namespace_0` in Snapshot Info to inspect the date, size and chunk availability. Save the returned metadata and HTTP size before obtaining content. Prefer a small representative chunk for the next experiment. An Enterprise chunk may itself be large and require suitable hardware.
2. Save the applicable publisher checksum, checksum algorithm, and source manifest when available. Use the exact dated permalink. For a public HTTPS object, run `python tools/wikipedia_snapshot.py fetch "$URL" "$SOURCE" --max-bytes "$MEASURED_BYTES" --expect "$ALGORITHM_AND_HEX"`. Omit `--expect` only when there is no expected digest, then pin the tool's observed SHA-256 in the research record. For an Enterprise download requiring authentication, obtain the tarball with the documented API and store the provider metadata separately. Keep bearer credentials and expiring signed URLs out of the archive manifest.
3. Keep that immutable local file alongside the source metadata, source licensing material and checksum evidence. The Enterprise snapshot or individual chunk is a gzip-compressed tar with one NDJSON member. A plain NDJSON member can also be supplied. Run the following once the values identify the selected release.

```sh
python tools/wikipedia_snapshot.py transform "$SOURCE" "$NEW_OUTPUT_DIRECTORY" \
  --input-format enterprise-tar-gz --project enwiki \
  --snapshot-id "$PINNED_SNAPSHOT_IDENTIFIER" --snapshot-date "$YYYY_MM_DD" \
  --source-url "$STABLE_SOURCE_URL" --expect "sha256:$PINNED_SHA256"
```

4. Preserve the exact source separately. Check extracted records and measure expansion and compression locally. Use a pinned project checkout and retain the interpreter and compression tool versions with benchmark results. Provision disk for the compressed file, SQLite staging index and normalized output at the same time. The temporary index sorts by numeric page ID and keeps the highest revision. A snapshot-wide selection should process a complete input, or use a future merger that also handles duplicates and tombstones across independently processed chunks.
5. To study a raw XML alternative, use checksummed parts, an XML reader, and a pinned MediaWiki rendering setup. To study Kiwix, verify the Metalink checksum, inspect version and MIME information, and extract articles with `zimdump` or libzim. Both routes need a tested adapter mapping page and revision IDs, license notices, and article HTML to the same record model. Do not use titles as surrogate page IDs for entries whose upstream identity cannot be recovered.

## Experimental record format

The output directory contains a manifest and an article stream. The stream is one UTF-8 JSON object per LF-terminated line. Lines are ordered by numeric source page ID. Object keys are sorted and JSON punctuation uses compact separators. Input is UTF-8 NDJSON or a tar.gz snapshot carrying one NDJSON file. No tar member is written to the filesystem.

| Field | Meaning |
| --- | --- |
| `id`, `title` | ID `wiki:<project>:<page_id>` is stable across title or revision changes that keep that page ID. The title is the source title at this revision. |
| `source` | Project, page and revision IDs, snapshot identifier/date, source and revision/history URLs, source license objects, provided attribution fields and captured license notices. |
| `blocks` | Ordered text blocks with `kind` and `text`; heading blocks have levels 1–6, and source anchors and list depth appear when available. Table rows use vertical-bar separators. Inline sub/superscripts use `_(…)` and `^(…)`. |
| `formulae` | One-based entries associated with `⟦math:N⟧` tokens. Preserve available TeX, MathML and alternate text. Markup is source data. A consumer should treat it as inert unless it supplies a safe renderer. |
| `citations`, `references`, `links` | Ordered citation marker observations (text, source anchor, target URL), separate source references (anchor, text, links), and links encountered in the reading content. |

The manifest identifies the source bytes and SHA-256, expected checksum if one was supplied, uncompressed input NDJSON bytes, input/category counts, transformation notes and article stream byte count and SHA-256. The `article` input count includes duplicate candidates before deduplication. Records are a labeled derivative of rendered text. A source page appearing with a delete or visibility-change event in the same input is omitted. Conflicting payloads for one page and revision produce an error instead of an arbitrary selection.

This research pass exercises a renderer-facing adapter with synthetic input. A broad source review still needs to find template loss, hidden notices, ambiguous markup, multi-column tables, layout-dependent formulae, redirects and missing revisions or links. Nested list depth is retained, while row and column spanning, reference placement within paragraphs and rich inline formatting have reduced fidelity. Review exception handling on a representative pinned sample, profile full-corpus disk space and runtime, and evaluate simple compression only after fidelity and attribution have been established.
