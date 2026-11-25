"""Acquire a bounded, revision-pinned English Wikipedia research sample."""

import argparse
from datetime import date
from hashlib import sha256
from ipaddress import ip_address
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener

from wikipedia_snapshot import HTTPSRedirects, LICENSES, checksum_spec, json_line, positive_id


BASE = "https://en.wikipedia.org"
REST = f"{BASE}/w/rest.php/v1/revision/"
ACTION = f"{BASE}/w/api.php"
LICENSE = LICENSES["CC-BY-SA-4.0"]
LEGALCODE = f"{LICENSE}legalcode"
USER_AGENT = "CentauriArchiveSnapshot/2 (https://github.com/InterstellarNerd8760/centauri-archive)"
REST_BYTE_LIMIT = 4 * 1024 * 1024
HISTORY_BYTE_LIMIT = 512 * 1024


def get(url, maximum):
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with build_opener(HTTPSRedirects()).open(request, timeout=30) as response:
        length = response.headers.get("Content-Length")
        if length is not None and int(length) > maximum:
            raise ValueError("server reports a response exceeding the sample limit")
        data = response.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError("sample response exceeds its byte limit")
    if length is not None and len(data) != int(length):
        raise ValueError("incomplete sample response")
    return data


def revision_entry(item):
    page_id = positive_id(item["page_id"], "page")
    revision = positive_id(item["revision_id"], "revision")
    checksum = checksum_spec(f'sha256:{item["rest_sha256"]}')["digest"]
    url = f"{REST}{revision}/with_html"
    raw = get(url, REST_BYTE_LIMIT)
    if sha256(raw).hexdigest() != checksum:
        raise ValueError(f"observed response checksum differs for revision {revision}")
    source = json.loads(raw)
    page = source["page"]
    if (source["id"] != revision or page["id"] != page_id or page["title"] != item["title"]
            or source["content_model"] != "wikitext"):
        raise ValueError(f"unexpected page or revision metadata for {revision}")
    publisher_license = source["license"]
    license_url = urlsplit(publisher_license["url"])
    if (license_url.scheme != "https" or license_url.netloc != "creativecommons.org"
            or not license_url.path.startswith("/licenses/by-sa/4.0/")):
        raise ValueError(f"unexpected source license for revision {revision}")
    html = source["html"]
    if not isinstance(html, str) or not html.strip():
        raise ValueError(f"response has no complete article HTML for revision {revision}")
    html_bytes = html.encode()
    article = {
        "identifier": page_id,
        "name": page["title"],
        "url": f"{BASE}/wiki/{page['key']}",
        "is_part_of": {"identifier": "enwiki"},
        "namespace": {"identifier": 0},
        "version": {"identifier": revision, "date_modified": source["timestamp"]},
        "article_body": {"html": html},
        "license": [{"identifier": "CC-BY-SA-4.0", "url": LICENSE}],
        "rights": {"publisher_license": publisher_license},
    }
    return article, {
        "page_id": page_id, "revision_id": revision, "revision_timestamp": source["timestamp"],
        "title": page["title"], "rest_url": url, "rest_bytes": len(raw), "rest_sha256": checksum,
        "html_bytes": len(html_bytes), "html_sha256": sha256(html_bytes).hexdigest(),
    }


def legacy_ip(label):
    try:
        ip_address(label)
    except ValueError:
        return False
    return True


def contributors(page_id, revision, limit):
    result = {"page_id": page_id, "revision_id": revision, "history_responses": [],
              "revision_rows": 0, "legacy_anonymous_edit_rows": 0, "withheld_editor_rows": 0}
    if limit == 0:
        return {**result, "status": "not-collected", "visible_labels": []}
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ValueError("each article's history request limit must be an integer from zero to ten")
    query = {"action": "query", "prop": "revisions", "pageids": page_id, "rvstartid": revision,
             "rvdir": "older", "rvlimit": "max", "rvprop": "ids|user", "format": "json", "formatversion": 2}
    continuation = {}
    seen = set()
    labels = {}
    for _ in range(limit):
        url = f"{ACTION}?{urlencode(query | continuation)}"
        raw = get(url, HISTORY_BYTE_LIMIT)
        metadata = json.loads(raw)
        pages = metadata["query"]["pages"]
        if len(pages) != 1 or pages[0]["pageid"] != page_id:
            raise ValueError("history response identifies a different page")
        rows = pages[0]["revisions"]
        if not rows or not seen and rows[0]["revid"] != revision:
            raise ValueError("history response does not start at the pinned revision")
        for row in rows:
            identity = positive_id(row["revid"], "revision")
            if identity in seen:
                raise ValueError("history continuation repeated a revision")
            seen.add(identity)
            user = row.get("user")
            if row.get("userhidden") or not user:
                result["withheld_editor_rows"] += 1
            elif row.get("anon") or legacy_ip(user):
                result["legacy_anonymous_edit_rows"] += 1
            else:
                labels[user] = "temporary-account" if row.get("temp") else "account"
        result["history_responses"].append({"url": url, "bytes": len(raw), "sha256": sha256(raw).hexdigest()})
        continuation = metadata.get("continue")
        if continuation is None:
            break
        if continuation.keys() != {"continue", "rvcontinue"} or not all(
            isinstance(token, str) and token for token in continuation.values()
        ):
            raise ValueError("unexpected revision history pagination token")
    result["revision_rows"] = len(seen)
    result["status"] = "public-pagination-exhausted" if continuation is None else "request-limit-reached"
    result["visible_labels"] = [{"label": label, "kind": labels[label]} for label in sorted(labels)]
    return result


def acquire(config, output):
    if output.exists():
        raise ValueError("output directory already exists")
    if not config["id"] or date.fromisoformat(config["acquisition_date"]).isoformat() != config["acquisition_date"]:
        raise ValueError("expected a sample identifier and ISO date YYYY-MM-DD")
    items = config["articles"]
    if not isinstance(items, list) or not 1 <= len(items) <= 10:
        raise ValueError("sample must list one to ten pinned revisions")
    page_ids = [positive_id(item["page_id"], "page") for item in items]
    if len(page_ids) != len(set(page_ids)):
        raise ValueError("sample lists a page more than once")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temporary:
        stage = Path(temporary) / "sample"
        stage.mkdir()
        articles = []
        credits = []
        sources = []
        for item in sorted(items, key=lambda item: item["page_id"]):
            article, source = revision_entry(item)
            credits.append({"id": f'wiki:enwiki:{source["page_id"]}',
                            **contributors(source["page_id"], source["revision_id"],
                                           item.get("history_request_limit", 0))})
            articles.append(json_line(article))
            sources.append(source)
        license_bytes = get(LEGALCODE, HISTORY_BYTE_LIMIT)
        files = {"rendered.ndjson": b"".join(articles), "attribution.ndjson": b"".join(map(json_line, credits)),
                 "cc-by-sa-4.0-legalcode.html": license_bytes}
        manifest = {
            "format": "centauri-enwiki-revision-sample-v1",
            "sample_id": config["id"], "selection_date": config["acquisition_date"],
            "articles": sources, "license_legalcode": LEGALCODE,
            "attribution_scope": "API-visible editor labels for selected pages and revisions, incomplete for redistribution",
            "files": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest()} for name, data in files.items()},
        }
        for name, data in files.items():
            (stage / name).write_bytes(data)
        (stage / "source-manifest.json").write_bytes(json_line(manifest))
        stage.rename(output)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        manifest = acquire(json.loads(args.config.read_bytes()), args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"wikipedia_sample: {error}\n")
    print(json_line(manifest).decode(), end="")


if __name__ == "__main__":
    main()
