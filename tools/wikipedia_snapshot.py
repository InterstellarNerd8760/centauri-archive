"""Optional research workflow for pinned Wikimedia Enterprise article snapshots."""

import argparse
from contextlib import closing, contextmanager
from datetime import date
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sqlite3
import tarfile
from tempfile import NamedTemporaryFile, TemporaryDirectory
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


CHUNK_BYTES = 1024 * 1024
MAX_LINE_BYTES = 128 * CHUNK_BYTES
FORMAT = "centauri-wikipedia-derivative-v1"
LICENSES = {
    "CC-BY-SA-4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
}
VOID = set("area base br col embed hr img input link meta param source track wbr".split())
OMIT = set("head nav script style noscript iframe audio video object embed svg".split())
CHROME = set("navbox vertical-navbox mw-editsection mw-jump-link vector-menu noprint-navigation".split())
HEADINGS = set("h1 h2 h3 h4 h5 h6".split())
BLOCKS = {
    "p": "paragraph", "li": "list-item", "dt": "term", "dd": "definition",
    "blockquote": "quotation", "pre": "preformatted", "figcaption": "caption",
    "caption": "caption",
}
DISPLAY_NONE = re.compile(r"(?:^|;)\s*display\s*:\s*none\b", re.IGNORECASE)


def json_line(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def require_https(value):
    target = urlsplit(value)
    if (target.scheme != "https" or not target.hostname or target.username is not None
            or target.password is not None):
        raise ValueError("source URLs must use HTTPS without embedded credentials")
    return value


def checksum_spec(value):
    algorithm, _, digest = value.partition(":")
    lengths = {"md5": 32, "sha1": 40, "sha256": 64}
    if algorithm not in lengths or not re.fullmatch(r"[a-fA-F0-9]+", digest) or len(digest) != lengths[algorithm]:
        raise ValueError("expected md5:, sha1: or sha256: followed by a full hexadecimal digest")
    return dict(algorithm=algorithm, digest=digest.lower())


def copy_and_hash(source, destination=None, expected=None, maximum=None):
    sha256 = hashlib.sha256()
    extra = hashlib.new(expected["algorithm"], usedforsecurity=False) if expected else None
    size = 0
    while chunk := source.read(CHUNK_BYTES):
        size += len(chunk)
        if maximum is not None and size > maximum:
            raise ValueError("input exceeds the explicit download byte limit")
        sha256.update(chunk)
        if extra:
            extra.update(chunk)
        if destination is not None:
            destination.write(chunk)
    if extra and extra.hexdigest() != expected["digest"]:
        raise ValueError("checksum mismatch")
    return {"bytes": size, "sha256": sha256.hexdigest(), "expected_checksum": expected}


class HTTPSRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        require_https(new_url)
        return super().redirect_request(request, response, code, message, headers, new_url)


def fetch(url, output, maximum, expected):
    require_https(url)
    if maximum <= 0:
        raise ValueError("download byte limit must be positive")
    output.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "CentauriArchiveSnapshot/1 (open archival research)"})
    with build_opener(HTTPSRedirects()).open(request, timeout=60) as response, NamedTemporaryFile(
        dir=output.parent
    ) as staging:
        length = response.headers.get("Content-Length")
        if length is not None and int(length) > maximum:
            raise ValueError("server reports a file larger than the download byte limit")
        result = copy_and_hash(response, staging, expected, maximum)
        if length is not None and result["bytes"] != int(length):
            raise ValueError("incomplete response")
        staging.flush()
        # Publish the verified file and fail if the destination already exists.
        output.hardlink_to(staging.name)
    return result


class Node:
    def __init__(self, tag, attrs=()):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []

    @property
    def classes(self):
        return set((self.attrs.get("class") or "").split())

    @property
    def types(self):
        return set((self.attrs.get("typeof") or "").split())

    def find(self, tag):
        if self.tag == tag:
            return self
        for child in self.children:
            if isinstance(child, Node) and (found := child.find(tag)) is not None:
                return found
        return None

    def markup(self):
        attrs = "".join(f' {name}="{escape(value or "", quote=True)}"' for name, value in self.attrs.items())
        contents = "".join(escape(child) if isinstance(child, str) else child.markup() for child in self.children)
        return f"<{self.tag}{attrs}>{contents}</{self.tag}>"


class ArticleHTML(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]
        self.feed(html)
        self.close()

    def append_tag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        return node

    def handle_starttag(self, tag, attrs):
        node = self.append_tag(tag, attrs)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.append_tag(tag, attrs)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def visible_text(node):
    return "".join(child if isinstance(child, str) else visible_text(child) for child in node.children)


def compact(value):
    return " ".join(value.split())


def omit(node):
    return (node.tag in OMIT or bool(node.classes & CHROME) or "hidden" in node.attrs
            or DISPLAY_NONE.search(node.attrs.get("style") or "") is not None)


class ArticleContent:
    def __init__(self, source_url):
        self.source_url = source_url
        self.blocks = []
        self.citations = []
        self.references = []
        self.formulae = []
        self.links = []
        self.fragments = []
        self.list_depth = 0

    def flush(self, kind="paragraph", node=None):
        raw = "".join(self.fragments)
        self.fragments.clear()
        value = raw.strip("\n") if kind == "preformatted" else compact(raw)
        if value.strip():
            block = {"kind": kind, "text": value}
            if node and node.attrs.get("id"):
                block["anchor"] = node.attrs["id"]
            if kind == "heading":
                block["level"] = int(node.tag[1])
            if self.list_depth:
                block["list_depth"] = self.list_depth
            self.blocks.append(block)

    def url(self, raw):
        target = urljoin(self.source_url, raw)
        return target if urlsplit(target).scheme in ("http", "https") else None

    def formula(self, node):
        math = node.find("math")
        tex = next((visible_text(child) for child in descendants(math)
                    if child.tag == "annotation" and child.attrs.get("encoding") == "application/x-tex"),
                   None) if math else None
        if not tex and node.attrs.get("data-mw"):
            try:
                definition = json.loads(node.attrs["data-mw"])
                source_tex = definition["body"]["extsrc"]
                tex = source_tex if isinstance(source_tex, str) else None
            except (KeyError, TypeError, ValueError):
                pass
        image = node.find("img")
        alt = (math and math.attrs.get("alttext")) or (image and image.attrs.get("alt")) or None
        if not (math or tex or alt):
            raise ValueError("math element has no MathML, TeX or alternate text")
        index = len(self.formulae) + 1
        self.formulae.append({"index": index, "tex": tex, "mathml": math.markup() if math else None, "alt": alt})
        self.fragments.append(f"⟦math:{index}⟧")

    def reference_list(self, node):
        items = [child for child in descendants(node) if child.tag == "li"
                 and (child.attrs.get("id") or "").startswith("cite_note")]
        for item in items or [node]:
            links = [url for child in descendants(item) if child.tag == "a" and child.attrs.get("href")
                     if (url := self.url(child.attrs["href"]))]
            body = next((child for child in descendants(item) if child.classes & {"mw-reference-text",
                         "reference-text"}), item)
            text = " ".join(block["text"] for block in self.capture(body))
            self.references.append({"anchor": item.attrs.get("id"), "text": text,
                                    "links": list(dict.fromkeys(links))})

    def capture(self, node):
        """Read a container's child blocks without mixing them into the surrounding text."""
        blocks, fragments = self.blocks, self.fragments
        self.blocks, self.fragments = [], []
        try:
            for child in node.children:
                self.walk(child)
            self.flush()
            return self.blocks
        finally:
            self.blocks, self.fragments = blocks, fragments

    def table_row(self, node):
        self.flush()
        cells = []
        for child in node.children:
            if not isinstance(child, Node) or child.tag not in ("th", "td") or omit(child):
                continue
            cell = {"kind": "header" if child.tag == "th" else "data", "blocks": self.capture(child)}
            for attr in ("id", "headers", "scope"):
                if child.attrs.get(attr):
                    cell[attr] = child.attrs[attr]
            for attr in ("colspan", "rowspan"):
                raw = child.attrs.get(attr) or ""
                if re.fullmatch(r"[0-9]{1,5}", raw) and (attr == "rowspan" or int(raw) > 0):
                    cell[attr] = int(raw)
            cells.append(cell)
        if cells:
            self.blocks.append({"kind": "table-row",
                                "text": " | ".join(" ".join(block["text"] for block in cell["blocks"])
                                                   for cell in cells), "cells": cells})

    def inline(self, node):
        """Return true when an element has already been handled."""
        if omit(node):
            return True
        if "mw:Extension/ref" in node.types or "mw-ref" in node.classes or "reference" in node.classes:
            anchor = node.find("a")
            target = anchor.attrs.get("href") if anchor else None
            self.citations.append({"marker": compact(visible_text(node)), "anchor": node.attrs.get("id"),
                                   "target": self.url(target) if target else None})
            return True
        if node.classes & {"references", "reflist"} or "mw:Extension/references" in node.types:
            self.reference_list(node)
            return True
        if node.tag == "math" or "mw:Extension/math" in node.types or node.classes & {"mwe-math-element"}:
            self.formula(node)
            return True
        if node.tag == "a" and node.attrs.get("href") and (url := self.url(node.attrs["href"])):
            self.links.append({"url": url, "text": compact(visible_text(node))})
        if node.tag == "br":
            self.fragments.append("\n")
        return node.tag in VOID

    def walk(self, node):
        if isinstance(node, str):
            self.fragments.append(node)
            return
        if self.inline(node):
            return
        if node.tag == "tr":
            self.table_row(node)
            return
        kind = "heading" if node.tag in HEADINGS else BLOCKS.get(node.tag)
        container = node.tag in ("div", "section", "table", "ul", "ol", "dl")
        if kind or container:
            self.flush()
        if node.tag in ("ul", "ol"):
            self.list_depth += 1
        if node.tag in ("sub", "sup"):
            self.fragments.append("_(" if node.tag == "sub" else "^(")
        for child in node.children:
            self.walk(child)
        if node.tag in ("sub", "sup"):
            self.fragments.append(")")
        if kind:
            self.flush(kind, node)
        elif container:
            self.flush()
        if node.tag in ("ul", "ol"):
            self.list_depth -= 1

    def extract(self, root):
        self.walk(root.find("body") or root)
        self.flush()
        return {name: getattr(self, name) for name in ("blocks", "citations", "references", "formulae", "links")}


def descendants(node):
    for child in node.children:
        if isinstance(child, Node):
            yield child
            yield from descendants(child)


def positive_id(value, label):
    if type(value) is not int or not 0 < value < 2**63 - 1:
        raise ValueError(f"invalid {label} identifier")
    return value


def parse_article(article, project, snapshot_id, snapshot_date):
    if article["is_part_of"]["identifier"] != project:
        raise ValueError("article project differs from snapshot configuration")
    if type(article["namespace"]["identifier"]) is not int:
        raise ValueError("invalid namespace identifier")
    if article["namespace"]["identifier"] != 0:
        return None, None, "outside-main-namespace", None
    page = positive_id(article["identifier"], "page")
    event = article.get("event", {}).get("type", "update")
    if event in ("delete", "visibility-change"):
        return page, None, "visibility-or-deletion", None
    revision = positive_id(article["version"]["identifier"], "revision")
    if article.get("redirect") is True:
        return page, revision, "redirect", None
    html = article["article_body"]["html"]
    if not isinstance(html, str) or not html.strip():
        raise ValueError("article has no full HTML body")
    root = ArticleHTML(html).root
    if any("mw:PageProp/redirect" in (child.attrs.get("rel") or "").split() for child in descendants(root)):
        return page, revision, "redirect", None
    title = article["name"]
    if not isinstance(title, str) or not title.strip():
        raise ValueError("article has no title")
    source = require_https(article["url"])
    if project == "enwiki" and urlsplit(source).hostname != "en.wikipedia.org":
        raise ValueError("English Wikipedia article has an unexpected source hostname")
    licenses = article["license"]
    if not isinstance(licenses, list):
        raise ValueError("article licenses must be a list")
    allowed = {"CC0-1.0"} if project == "syntheticwiki" else {"CC-BY-SA-4.0"}
    license_urls = {entry["identifier"]: entry["url"] for entry in licenses}
    if not any(license_urls.get(name) == LICENSES[name] for name in allowed):
        raise ValueError("article lacks expected source license information")
    content = ArticleContent(source).extract(root)
    if not content["blocks"]:
        raise ValueError("no article text survives extraction")
    attribution = {key: article[key] for key in ("attribution", "copyright", "rights") if key in article}
    license_notices = [
        {"text": compact(visible_text(node)), "url": node.attrs.get("href")} for node in descendants(root)
        if set((node.attrs.get("rel") or "").split()) & {"license", "dc:license"}
    ]
    if project == "enwiki":
        revision_url = f"https://en.wikipedia.org/w/index.php?oldid={revision}"
        history_url = f"https://en.wikipedia.org/w/index.php?curid={page}&action=history"
    else:
        revision_url = article["version"]["url"]
        history_url = article["history_url"]
    record = {
        "id": f"wiki:{project}:{page}",
        "title": title,
        "source": {"project": project, "page_id": page, "revision_id": revision, "article_url": source,
                   "snapshot_id": snapshot_id, "snapshot_date": snapshot_date,
                   "revision_url": require_https(revision_url), "history_url": require_https(history_url),
                   "licenses": licenses, "provided_attribution": attribution, "license_notices": license_notices},
        **content,
    }
    if timestamp := article["version"].get("date_modified"):
        record["source"]["revision_timestamp"] = timestamp
    return page, revision, "article", record


@contextmanager
def input_lines(stream, input_format):
    if input_format == "ndjson":
        yield stream
        return
    with tarfile.open(fileobj=stream, mode="r|gz") as archive:
        member = archive.next()
        while member is not None and member.isdir():
            member = archive.next()
        if member is None or not member.isreg() or not member.name.endswith(".ndjson"):
            raise ValueError("expected one regular NDJSON member in snapshot tarball")
        with archive.extractfile(member) as extracted:
            yield extracted
        while (member := archive.next()) is not None:
            if not member.isdir():
                raise ValueError("snapshot tarball contains more than one data file")


def ingest(lines, database, project, snapshot_id, snapshot_date):
    database.execute("CREATE TABLE pages (page INTEGER PRIMARY KEY, revision INTEGER NOT NULL, record BLOB)")
    counts = {"input_rows": 0, "outside-main-namespace": 0, "redirect": 0, "visibility-or-deletion": 0,
              "article": 0}
    uncompressed = 0
    while raw := lines.readline(MAX_LINE_BYTES + 1):
        line_number = counts["input_rows"] + 1
        if len(raw) > MAX_LINE_BYTES:
            raise ValueError(f"line {line_number} exceeds the per-record byte limit")
        try:
            page, revision, kind, record = parse_article(
                json.loads(raw.decode("utf-8")), project, snapshot_id, snapshot_date
            )
        except (ValueError, KeyError, TypeError, AttributeError, RecursionError) as error:
            raise ValueError(f"invalid snapshot article on line {line_number}: {error}") from error
        counts["input_rows"] += 1
        counts[kind] += 1
        uncompressed += len(raw)
        if page is None:
            continue
        # A visibility event excludes that page even if the same snapshot repeats it.
        # SQLite's largest integer is reserved as a tombstone revision.
        revision = revision if revision is not None else 2**63 - 1
        payload = json_line(record) if record else None
        existing = database.execute("SELECT revision, record FROM pages WHERE page = ?", (page,)).fetchone()
        if existing and existing[0] == revision and existing[1] != payload:
            raise ValueError(f"conflicting content for page {page}, revision {revision}")
        database.execute(
            "INSERT INTO pages VALUES (?, ?, ?) ON CONFLICT(page) DO UPDATE SET "
            "revision = excluded.revision, record = excluded.record WHERE excluded.revision > pages.revision",
            (page, revision, payload),
        )
    database.commit()
    return counts, uncompressed


def write_records(database, output):
    digest = hashlib.sha256()
    size = count = text_bytes = 0
    with output.open("wb") as records:
        for (line,) in database.execute("SELECT record FROM pages WHERE record IS NOT NULL ORDER BY page"):
            records.write(line)
            digest.update(line)
            size += len(line)
            record = json.loads(line)
            text_bytes += sum(len(block["text"].encode()) for block in record["blocks"])
            count += 1
    if not count:
        raise ValueError("snapshot extraction produced no articles")
    return {"path": output.name, "records": count, "bytes": size, "body_text_utf8_bytes": text_bytes,
            "sha256": digest.hexdigest()}


def transform(path, output, *, input_format, project, snapshot_id, snapshot_date, source_url, expected=None):
    if project not in ("enwiki", "syntheticwiki"):
        raise ValueError("expected enwiki or syntheticwiki project")
    if not snapshot_id.strip() or date.fromisoformat(snapshot_date).isoformat() != snapshot_date:
        raise ValueError("expected a snapshot identifier and ISO date YYYY-MM-DD")
    require_https(source_url)
    if output.exists():
        raise ValueError("output directory already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    with path.open("rb") as source, TemporaryDirectory(dir=output.parent) as staging:
        source_file = copy_and_hash(source, expected=expected)
        source.seek(0)
        stage = Path(staging)
        package = stage / "package"
        package.mkdir()
        with closing(sqlite3.connect(stage / "index.sqlite")) as database:
            with input_lines(source, input_format) as lines:
                counts, uncompressed = ingest(lines, database, project, snapshot_id, snapshot_date)
            records = write_records(database, package / "articles.ndjson")
        manifest = {
            "format": FORMAT,
            "inclusion": "main-namespace non-redirect articles; highest present revision for each page",
            "changes": ["extract rendered article text and heading levels", "omit site navigation and media",
                        "separate citation markers and references", "preserve formulae and source attribution"],
            "reuse_review": "additional per-page notices, attributed imports and redistribution terms require review",
            "snapshot": {"id": snapshot_id, "date": snapshot_date, "project": project,
                         "source_url": source_url, "input_format": input_format, **source_file,
                         "uncompressed_ndjson_bytes": uncompressed},
            "counts": counts,
            "articles": records,
        }
        (package / "manifest.json").write_bytes(json_line(manifest))
        package.rename(output)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    acquire = commands.add_parser("fetch", help="download a specific HTTPS object to a new path")
    acquire.add_argument("url")
    acquire.add_argument("output", type=Path)
    acquire.add_argument("--max-bytes", required=True, type=int)
    extract = commands.add_parser("transform", help="extract articles from a local pinned snapshot or chunk")
    extract.add_argument("input", type=Path)
    extract.add_argument("output", type=Path)
    extract.add_argument("--input-format", required=True, choices=("ndjson", "enterprise-tar-gz"))
    extract.add_argument("--project", default="enwiki", choices=("enwiki", "syntheticwiki"))
    extract.add_argument("--snapshot-id", required=True)
    extract.add_argument("--snapshot-date", required=True)
    extract.add_argument("--source-url", required=True)
    for command in (acquire, extract):
        command.add_argument("--expect", metavar="ALGORITHM:HEX", help="published or separately pinned checksum")
    args = parser.parse_args()
    try:
        expected = checksum_spec(args.expect) if args.expect else None
        if args.command == "fetch":
            result = fetch(args.url, args.output, args.max_bytes, expected)
        else:
            result = transform(args.input, args.output, input_format=args.input_format, project=args.project,
                               snapshot_id=args.snapshot_id, snapshot_date=args.snapshot_date,
                               source_url=args.source_url, expected=expected)
        print(json_line(result).decode(), end="")
    except (OSError, RuntimeError, ValueError, tarfile.TarError, sqlite3.Error) as error:
        parser.exit(1, f"wikipedia_snapshot: {error}\n")


if __name__ == "__main__":
    main()
