"""Measure source records and project an independently protected curated collection."""
import argparse
from collections import Counter
import json
from pathlib import Path

from archive import ROOT
from protect_archive import encoded_size
from research_archive import COUNT, HEADER, INDEX_ENTRY

PLANS = (100, 300, 1000, 3000, 5000)
FRAME_BYTES = HEADER.size + 32


def compact_json(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def text_size(article):
    text = [article["title"], *article["body"], article["limitations"]]
    return sum(len(part.encode("utf-8")) for part in text)


def projection(articles, fixed, count, copies):
    sizes = sorted(len(compact_json(article)) for article in articles)
    # Resample ordered observed sizes at equally spaced quantiles. This retains
    # the measured distribution instead of treating every future text as average.
    selected = [sizes[min(len(sizes) - 1, (i * len(sizes)) // count)] for i in range(count)]
    index_bytes = COUNT.size + INDEX_ENTRY.size * (len(fixed) + count)
    logical_bytes = sum(fixed) + sum(selected) + index_bytes
    record_lengths = [*fixed, *selected, index_bytes]
    framed = logical_bytes + FRAME_BYTES * len(record_lengths)
    protected = sum(encoded_size(size + FRAME_BYTES) for size in record_lengths)
    return dict(articles=count, article_bytes=sum(selected), index_bytes=index_bytes,
                logical_bytes=logical_bytes, framed_bytes=framed, protected_bytes=protected,
                redundant_copy_bytes=protected * (copies - 1), encoded_bytes=protected * copies)


def measure(root=ROOT, copies=2):
    if type(copies) is not int or not 1 <= copies <= 8:
        raise ValueError("choose from one to eight copies")
    archive = root / "archive"
    source_index = archive / "encyclopedia/index.json"
    source_data = json.loads(source_index.read_text(encoding="utf-8"))
    articles = source_data["articles"]
    sizes = sorted(text_size(article) for article in articles)
    if not sizes:
        raise ValueError("no encyclopedia articles")
    totals = Counter()
    fixed = []
    all_sizes = []
    for path in sorted(archive.rglob("*")):
        if not path.is_file():
            continue
        length = path.stat().st_size
        all_sizes.append(length)
        if path == source_index:
            continue
        fixed.append(length)
        match = path.relative_to(archive).parts[0]
        if path.suffix.lower() in (".jpg", ".jpeg"):
            totals["photographs"] += length
        elif path.suffix == ".svg":
            totals["diagrams"] += length
        elif match in ("primer", "vocabulary"):
            totals[match] += length
        else:
            totals["other_records"] += length
    projection_fixed = fixed + [len(compact_json({k: v for k, v in source_data.items() if k != "articles"}))]
    source = dict(totals, article_utf8_text=sum(sizes),
                  encyclopedia_metadata=source_index.stat().st_size - sum(sizes))
    protected = sum(encoded_size(length + FRAME_BYTES) for length in all_sizes)
    return dict(
        articles=len(articles), copies=copies, source_bytes=source,
        logical_source_bytes=sum(all_sizes), protected_source_model_bytes=protected,
        redundant_source_model_bytes=protected * (copies - 1),
        complete_source_model_bytes=protected * copies,
        article_text_bytes={"minimum": sizes[0], "median_lower": sizes[(len(sizes) - 1) // 2],
                            "p90_lower": sizes[(len(sizes) - 1) * 9 // 10], "maximum": sizes[-1]},
        scenarios=[projection(articles, projection_fixed, count, copies) for count in PLANS],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copies", type=int, default=2)
    args = parser.parse_args()
    try:
        print(json.dumps(measure(copies=args.copies), indent=2, sort_keys=True))
    except (ValueError, OSError) as error:
        parser.exit(1, f"knowledge budget: {error}\n")


if __name__ == "__main__":
    main()
