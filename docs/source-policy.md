# Encyclopedia and source reuse policy

Status: research and editorial policy, not legal advice.

The Centauri Archive should be a coherent *explanatory sequence*, not an undifferentiated offline mirror of the internet. Source selection is separate from publication rights. A fact is not copyrightable in the same way as an authored article; an article's distinctive language, arrangement, and media can carry protected rights.

## Wikipedia

Wikipedia article text is normally available under CC BY-SA 4.0, subject to page-specific exceptions and license requirements. Attribution, indication of changes, and share-alike obligations apply when adapting the licensed text. Images embedded in Wikipedia have **separate** per-file rights. Track page revision URLs and attribution records when importing or adapting. We can also use Wikipedia as a discovery index without reproducing its prose.

Reference: https://en.wikipedia.org/wiki/Wikipedia:Reusing_Wikipedia_content

## Grokipedia

The current xAI/SpaceXSI consumer terms designate Grokipedia material under the SpaceXSI Community License Agreement, except where page-specific materials may have other notices. This is not interchangeable with CC0 or public domain. Avoid bulk mirroring or copying Grokipedia pages into a permanent redistribution package until each proposed use and the current license are reviewed. We can use Grokipedia as one research lead and independently verify facts through primary sources.

Terms: https://x.ai/legal/terms-of-service
License referenced in those terms: https://huggingface.co/xai-org/grok-2/blob/main/LICENSE

## Wikidata and Wikimedia Commons

Wikidata is generally CC0 and valuable for structured information (identifiers, coordinates, classifications), though sources still need checking. Wikimedia Commons files are individually licensed; check every file page for author, source, license version and required attribution. Do not assume all Commons material is public domain.

References: https://www.wikidata.org/wiki/Wikidata:Licensing and https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia

## Our source hierarchy

1. Measurements and primary scientific references (mission data, peer-reviewed articles, agency technical reports).
2. Authoritative synthesis and educational sources (NASA, USGS, NCBI Bookshelf, Smithsonian, etc.).
3. Wikipedia, Grokipedia and other tertiary sources as leads or cross-checks.
4. Original archive prose written explicitly for the decoding sequence, with named assumptions, sources, uncertainty and review states.

## Current acquisition workflow

The research protocol in [encyclopedia-sourcing.md](encyclopedia-sourcing.md) distinguishes topic discovery, primary-source verification, new writing and rights tracking. Grokipedia pages were not copied into the development package; example page URLs could not be inspected reliably in the current research session. Any Grokipedia-derived content would require individual licensing and provenance review. The [100-image plan](images-100-plan.md) likewise distinguishes named subjects from media actually present.

## Metadata and responsibility

`archive/catalog.json` is the editorial source of titles, groups, provenance links, review status and rights notes. A manifest's SHA-256 verifies bytes, not historical truth, scientific correctness, cultural representation or copyright compliance. The catalog and records should always be independently reviewed before calling them final.

We have **not** designated a permissive license for the whole collection. The repository being public does not automatically make everything freely reusable. Before publishing imported CC BY-SA or CC BY assets, prepare explicit attribution records and check compatibility with the distribution plan. For a physical message intended for the distant future, prefer original and public-domain materials when they can meet the educational purpose.
