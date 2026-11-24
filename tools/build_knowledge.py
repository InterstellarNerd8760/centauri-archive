"""Create a compact browser catalog and lazily fetched encyclopedia records."""
import json
from pathlib import Path
import re

from archive import ROOT
from knowledge_budget import compact_json


def publish_knowledge(output):
    directory = Path(output) / "knowledge"
    directory.mkdir(parents=True, exist_ok=True)
    source = json.loads((ROOT / "archive/encyclopedia/index.json").read_text(encoding="utf-8"))
    categories = source["categories"]
    shards = {category["id"]: {} for category in categories}
    summaries = []
    articles = directory / "articles"
    articles.mkdir(exist_ok=True)
    for article in source["articles"]:
        number = article["id"]
        if not re.fullmatch(r"CA-[0-9]{2}\.[0-9]{3}", number):
            raise ValueError(f"invalid encyclopedia filename ID: {number!r}")
        (articles / f"{number}.json").write_bytes(compact_json(article))
        summaries.append({key: article[key] for key in
                          ("id", "title", "category", "subcategory", "review_stage", "prerequisites")})
        shards[article["category"]][number] = " ".join(
            [*article["body"], article["limitations"],
             *(term["term"] for term in article.get("terms", []))]
        ).lower()
    (directory / "catalog.json").write_bytes(compact_json(
        {"version": 1, "categories": categories, "articles": summaries}
    ))
    for category, values in shards.items():
        (directory / f"search-{category}.json").write_bytes(compact_json(values))
    taxonomy = ROOT / "curation/knowledge-backlog.json"
    (directory / "backlog.json").write_bytes(taxonomy.read_bytes())
