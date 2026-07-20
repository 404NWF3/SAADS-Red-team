from __future__ import annotations

import csv
import email.utils
import fnmatch
import hashlib
import io
import json
import re
import time
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

import httpx
import yaml
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "corpus_sources.yaml"
DEFAULT_MANIFEST = ROOT / "reports" / "corpus_manifest.csv"
DEFAULT_CORPUS_JSON = ROOT / "input" / "_corpus.json"
USER_AGENT = "llm-defense-graphrag/0.1 (+local research corpus)"

MANIFEST_FIELDS = [
    "id",
    "path",
    "raw_path",
    "title",
    "source",
    "source_type",
    "published_at",
    "security_domain",
    "trust_level",
    "canonical_url",
    "document_version",
    "license",
    "word_count",
    "byte_count",
    "sha256",
    "retrieved_at",
]


@dataclass(slots=True)
class Document:
    id: str
    title: str
    source: str
    source_type: str
    published_at: str
    security_domain: str
    trust_level: str
    canonical_url: str
    document_version: str
    license: str
    text: str
    path: str
    raw_path: str
    retrieved_at: str

    def json_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "source": self.source,
            "source_type": self.source_type,
            "published_at": self.published_at,
            "security_domain": self.security_domain,
            "trust_level": self.trust_level,
            "canonical_url": self.canonical_url,
            "document_version": self.document_version,
            "license": self.license,
            "path": self.path,
        }

    def manifest_record(self) -> dict[str, Any]:
        payload = self.text.encode("utf-8")
        return {
            "id": self.id,
            "path": self.path,
            "raw_path": self.raw_path,
            "title": self.title,
            "source": self.source,
            "source_type": self.source_type,
            "published_at": self.published_at,
            "security_domain": self.security_domain,
            "trust_level": self.trust_level,
            "canonical_url": self.canonical_url,
            "document_version": self.document_version,
            "license": self.license,
            "word_count": word_count(self.text),
            "byte_count": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "retrieved_at": self.retrieved_at,
        }


class Downloader:
    def __init__(self) -> None:
        self.client = httpx.Client(
            follow_redirects=True,
            timeout=httpx.Timeout(40.0),
            headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
        )

    def close(self) -> None:
        self.client.close()

    def get(self, url: str) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = self.client.get(url)
                response.raise_for_status()
                return response
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(2**attempt)
        raise RuntimeError(f"download failed after 3 attempts: {url}: {last_error}")

    def json(self, url: str) -> dict[str, Any]:
        return self.get(url).json()


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE))


def slugify(value: str, *, max_length: int = 90) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "document"
    if len(normalized) <= max_length:
        return normalized
    suffix = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    return f"{normalized[: max_length - 9].rstrip('-')}-{suffix}"


def metadata_markdown(metadata: dict[str, Any], body: str) -> str:
    frontmatter = yaml.safe_dump(
        metadata, allow_unicode=True, sort_keys=False, default_flow_style=False
    ).strip()
    return f"---\n{frontmatter}\n---\n\n{body.strip()}\n"


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_document(document: Document) -> None:
    path = ROOT / document.path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document.text, encoding="utf-8", newline="\n")


def relation_items(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if any(key in value for key in ("source", "source-id", "target", "target-id")):
            yield value
        for nested in value.values():
            yield from relation_items(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from relation_items(nested)


def atlas_canonical_url(object_type: str, object_id: str) -> str:
    section = {
        "tactic": "tactics",
        "technique": "techniques",
        "mitigation": "mitigations",
        "case-study": "studies",
    }.get(object_type, "resources")
    return f"https://atlas.mitre.org/{section}/{object_id}"


def collect_atlas(
    key: str, source: dict[str, Any], downloader: Downloader, retrieved_at: str
) -> list[Document]:
    url = source["download_url"]
    response = downloader.get(url)
    for _ in range(4):
        pointer = response.text.strip()
        if len(response.content) >= 500 or not pointer.endswith((".yaml", ".yml")):
            break
        url = urljoin(url, pointer)
        response = downloader.get(url)
    data = yaml.safe_load(response.content)
    if not isinstance(data, dict) or "techniques" not in data:
        raise ValueError("MITRE ATLAS download did not contain the expected techniques map")

    version = str(data.get("collection", {}).get("version", "latest"))
    raw_path = Path("data") / "raw" / key / f"ATLAS-{version}.yaml"
    write_bytes(ROOT / raw_path, response.content)
    relations = list(relation_items(data.get("relationships", {})))

    documents: list[Document] = []
    groups = tuple(
        source.get(
            "groups",
            ("tactics", "techniques", "mitigations", "case-studies", "case_studies"),
        )
    )
    seen: set[str] = set()
    for group in groups:
        objects = data.get(group, {})
        values = objects.values() if isinstance(objects, dict) else objects
        if not isinstance(values, Iterable):
            continue
        for item in values:
            if not isinstance(item, dict):
                continue
            object_id = str(item.get("id", "")).strip()
            if not object_id or object_id in seen:
                continue
            seen.add(object_id)
            object_type = str(item.get("object-type") or group.rstrip("s")).replace("_", "-")
            title = str(item.get("name") or object_id).strip()
            description = str(item.get("description") or "").strip()
            related = [rel for rel in relations if object_id in json.dumps(rel, ensure_ascii=False)]
            structured = dict(item)
            structured.pop("description", None)
            body = f"# {object_id}: {title}\n\n## Description\n\n{description}"
            if related:
                body += "\n\n## Explicit ATLAS relationships\n\n```yaml\n"
                body += yaml.safe_dump(related, allow_unicode=True, sort_keys=False).strip()
                body += "\n```"
            body += "\n\n## Structured source fields\n\n```yaml\n"
            body += yaml.safe_dump(structured, allow_unicode=True, sort_keys=False).strip()
            body += "\n```"
            canonical_url = atlas_canonical_url(object_type, object_id)
            published_at = str(item.get("modified-date") or item.get("created-date") or "")
            metadata = {
                "title": title,
                "source": source["name"],
                "source_type": source["source_type"],
                "published_at": published_at,
                "security_domain": source["security_domain"],
                "trust_level": source["trust_level"],
                "canonical_url": canonical_url,
                "document_version": version,
                "license": source["license"],
                "source_id": object_id,
                "object_type": object_type,
            }
            text = metadata_markdown(metadata, body)
            path = Path("input") / "mitre" / slugify(object_type) / f"{slugify(object_id)}.md"
            documents.append(
                Document(
                    id=f"mitre-atlas:{object_id}",
                    title=title,
                    source=source["name"],
                    source_type=source["source_type"],
                    published_at=published_at,
                    security_domain=source["security_domain"],
                    trust_level=source["trust_level"],
                    canonical_url=canonical_url,
                    document_version=version,
                    license=source["license"],
                    text=text,
                    path=path.as_posix(),
                    raw_path=raw_path.as_posix(),
                    retrieved_at=retrieved_at,
                )
            )
    return documents


def html_to_markdown(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup.select("script, style, noscript, nav, header, footer, form, svg"):
        element.decompose()
    content = soup.select_one("article") or soup.select_one("main") or soup.body
    if content is None:
        raise ValueError("HTML page has no readable body")
    heading = content.find("h1")
    title = heading.get_text(" ", strip=True) if heading else ""
    if not title and soup.title:
        title = soup.title.get_text(" ", strip=True).split("|")[0].strip()

    blocks: list[str] = []
    seen: set[str] = set()
    for element in content.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre"]):
        text = re.sub(r"\s+", " ", element.get_text(" ", strip=True)).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        if element.name and element.name.startswith("h"):
            blocks.append(f"{'#' * min(int(element.name[1]), 4)} {text}")
        elif element.name == "li":
            blocks.append(f"- {text}")
        elif element.name == "pre":
            blocks.append(f"```text\n{text}\n```")
        else:
            blocks.append(text)
    return title, "\n\n".join(blocks)


def collect_html_pages(
    key: str, source: dict[str, Any], downloader: Downloader, retrieved_at: str
) -> list[Document]:
    documents: list[Document] = []
    for index, url in enumerate(source["pages"], start=1):
        response = downloader.get(url)
        slug = slugify(Path(urlparse(url).path).name or f"page-{index}")
        raw_path = Path("data") / "raw" / key / f"{slug}.html"
        write_bytes(ROOT / raw_path, response.content)
        title, body = html_to_markdown(response.text)
        if word_count(body) < 100:
            raise ValueError(f"OWASP page contained too little text: {url}")
        metadata = {
            "title": title,
            "source": source["name"],
            "source_type": source["source_type"],
            "published_at": source["published_at"],
            "security_domain": source["security_domain"],
            "trust_level": source["trust_level"],
            "canonical_url": url,
            "document_version": source["document_version"],
            "license": source["license"],
        }
        text = metadata_markdown(metadata, body)
        path = Path("input") / "owasp" / f"{slug}.md"
        documents.append(
            Document(
                id=f"owasp-llm-top10:{slug}",
                title=title,
                source=source["name"],
                source_type=source["source_type"],
                published_at=source["published_at"],
                security_domain=source["security_domain"],
                trust_level=source["trust_level"],
                canonical_url=url,
                document_version=source["document_version"],
                license=source["license"],
                text=text,
                path=path.as_posix(),
                raw_path=raw_path.as_posix(),
                retrieved_at=retrieved_at,
            )
        )
    return documents


SECURITY_TERMS = (
    "attack",
    "defense",
    "detector",
    "evaluation",
    "guardrail",
    "jailbreak",
    "probe",
    "prompt",
    "red_team",
    "risk",
    "security",
    "vulnerability",
)


def strip_existing_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    return text[end + 5 :] if end >= 0 else text


def document_title(text: str, path: str) -> str:
    for line in text.splitlines()[:80]:
        match = re.match(r"^#{1,3}\s+(.+)$", line.strip())
        if match:
            return match.group(1).strip()
    return PurePosixPath(path).stem.replace("_", " ").replace("-", " ").title()


def collect_github_docs(
    key: str, source: dict[str, Any], downloader: Downloader, retrieved_at: str
) -> list[Document]:
    repo = source["repo"]
    branch = source["branch"]
    archive_url = f"https://codeload.github.com/{repo}/zip/refs/heads/{branch}"
    archive_response = downloader.get(archive_url)
    archive_sha = hashlib.sha256(archive_response.content).hexdigest()
    version = f"archive-sha256:{archive_sha}"
    raw_dir = Path("data") / "raw" / key
    archive_path = raw_dir / f"{slugify(repo)}-{archive_sha[:12]}.zip"
    write_bytes(ROOT / archive_path, archive_response.content)
    write_bytes(
        ROOT / raw_dir / "repository.json",
        json.dumps(
            {
                "repository": repo,
                "branch": branch,
                "archive_url": archive_url,
                "archive_sha256": archive_sha,
                "retrieved_at": retrieved_at,
                "etag": archive_response.headers.get("etag", ""),
                "last_modified": archive_response.headers.get("last-modified", ""),
            },
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8"),
    )

    includes = source["include"]
    min_words = int(source.get("min_words", 80))
    candidates: list[tuple[int, str, str]] = []
    with zipfile.ZipFile(io.BytesIO(archive_response.content)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            parts = PurePosixPath(info.filename).parts
            if len(parts) < 2:
                continue
            rel_path = PurePosixPath(*parts[1:]).as_posix()
            lower_path = rel_path.lower()
            if not any(fnmatch.fnmatch(rel_path, pattern) for pattern in includes):
                continue
            if any(
                ignored in lower_path
                for ignored in (
                    "changelog",
                    "contributing",
                    "code_of_conduct",
                    "release_notes",
                    "/test",
                )
            ):
                continue
            text = archive.read(info).decode("utf-8", errors="replace")
            if word_count(text) < min_words:
                continue
            score = sum(term in lower_path for term in SECURITY_TERMS) * 5
            score += sum(
                term.replace("_", " ") in text[:12000].lower() for term in SECURITY_TERMS
            )
            if lower_path == "readme.md":
                score += 20
            candidates.append((score, rel_path, text))

    candidates.sort(key=lambda item: (-item[0], item[1].lower()))
    selected = candidates[: int(source.get("max_documents", 15))]
    if not selected:
        raise ValueError(f"no matching documentation found in {repo}")

    last_modified = archive_response.headers.get("last-modified")
    published_at = retrieved_at[:10]
    if last_modified:
        parsed_date = email.utils.parsedate_to_datetime(last_modified)
        published_at = parsed_date.date().isoformat()
    documents: list[Document] = []
    for _, rel_path, original in selected:
        body = strip_existing_frontmatter(original).strip()
        title = document_title(body, rel_path)
        canonical_url = f"https://github.com/{repo}/blob/{branch}/{rel_path}"
        metadata_fields = {
            "title": title,
            "source": source["name"],
            "source_type": source["source_type"],
            "published_at": published_at,
            "security_domain": source["security_domain"],
            "trust_level": source["trust_level"],
            "canonical_url": canonical_url,
            "document_version": version,
            "license": source["license"],
            "source_path": rel_path,
        }
        if rel_path.lower().endswith(".rst"):
            body = f"# {title}\n\n```text\n{body}\n```"
        text = metadata_markdown(metadata_fields, body)
        suffix = hashlib.sha1(rel_path.encode("utf-8")).hexdigest()[:8]
        file_name = f"{slugify(title, max_length=75)}-{suffix}.md"
        category = "nist" if key.startswith("nist") else "tools"
        path = Path("input") / category / key / file_name
        documents.append(
            Document(
                id=f"github:{repo}:{rel_path}",
                title=title,
                source=source["name"],
                source_type=source["source_type"],
                published_at=published_at,
                security_domain=source["security_domain"],
                trust_level=source["trust_level"],
                canonical_url=canonical_url,
                document_version=version,
                license=source["license"],
                text=text,
                path=path.as_posix(),
                raw_path=archive_path.as_posix(),
                retrieved_at=retrieved_at,
            )
        )
    return documents


def load_config(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("sources"), dict):
        raise ValueError(f"invalid source registry: {path}")
    return data


def validate_documents(documents: list[Document], min_documents: int) -> None:
    if len(documents) < min_documents:
        raise ValueError(f"corpus has {len(documents)} documents; expected at least {min_documents}")
    ids = [doc.id for doc in documents]
    paths = [doc.path for doc in documents]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate document ids detected")
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate output paths detected")
    for doc in documents:
        if not doc.canonical_url.startswith("https://"):
            raise ValueError(f"non-HTTPS canonical URL: {doc.canonical_url}")
        if word_count(doc.text) < 30:
            raise ValueError(f"document is too short: {doc.path}")


def write_outputs(documents: list[Document], errors: list[str]) -> dict[str, Any]:
    expected_paths = {document.path for document in documents}
    if DEFAULT_MANIFEST.exists():
        with DEFAULT_MANIFEST.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                stale_path = row.get("path", "")
                candidate = ROOT / stale_path
                if (
                    stale_path not in expected_paths
                    and candidate.suffix == ".md"
                    and candidate.is_relative_to(ROOT / "input")
                    and candidate.is_file()
                ):
                    candidate.unlink()

    for document in documents:
        write_document(document)

    DEFAULT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with DEFAULT_MANIFEST.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(doc.manifest_record() for doc in documents)

    DEFAULT_CORPUS_JSON.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_CORPUS_JSON.write_text(
        json.dumps([doc.json_record() for doc in documents], ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )

    summary = {
        "generated_at": now_utc(),
        "document_count": len(documents),
        "sources": dict(sorted(Counter(doc.source for doc in documents).items())),
        "source_types": dict(sorted(Counter(doc.source_type for doc in documents).items())),
        "security_domains": dict(
            sorted(Counter(doc.security_domain for doc in documents).items())
        ),
        "errors": errors,
        "manifest": DEFAULT_MANIFEST.relative_to(ROOT).as_posix(),
        "graphrag_input": DEFAULT_CORPUS_JSON.relative_to(ROOT).as_posix(),
    }
    summary_path = ROOT / "reports" / "corpus_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )
    return summary


def collect(config_path: Path, min_documents: int, strict: bool) -> dict[str, Any]:
    config = load_config(config_path)
    retrieved_at = now_utc()
    documents: list[Document] = []
    errors: list[str] = []
    downloader = Downloader()
    try:
        for key, source in config["sources"].items():
            try:
                kind = source["kind"]
                if kind == "atlas_yaml":
                    new_documents = collect_atlas(key, source, downloader, retrieved_at)
                elif kind == "html_pages":
                    new_documents = collect_html_pages(key, source, downloader, retrieved_at)
                elif kind == "github_docs":
                    new_documents = collect_github_docs(key, source, downloader, retrieved_at)
                else:
                    raise ValueError(f"unsupported source kind: {kind}")
                documents.extend(new_documents)
                print(f"{key}: {len(new_documents)} documents")
            except Exception as exc:  # Source-level isolation keeps all failures visible.
                message = f"{key}: {exc}"
                errors.append(message)
                print(f"ERROR {message}")
    finally:
        downloader.close()

    documents.sort(key=lambda doc: (doc.source, doc.id))
    validate_documents(documents, min_documents)
    summary = write_outputs(documents, errors)
    if strict and errors:
        raise RuntimeError(f"{len(errors)} configured source(s) failed; see corpus_summary.json")
    return summary


def validate_existing(min_documents: int) -> dict[str, Any]:
    if not DEFAULT_MANIFEST.exists() or not DEFAULT_CORPUS_JSON.exists():
        raise FileNotFoundError("manifest or input/_corpus.json is missing; run collection first")
    with DEFAULT_MANIFEST.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    records = json.loads(DEFAULT_CORPUS_JSON.read_text(encoding="utf-8"))
    if len(rows) < min_documents:
        raise ValueError(f"manifest has {len(rows)} rows; expected at least {min_documents}")
    if len(records) != len(rows):
        raise ValueError("manifest and input/_corpus.json document counts differ")
    ids = [row["id"] for row in rows]
    paths = [row["path"] for row in rows]
    if len(ids) != len(set(ids)) or len(paths) != len(set(paths)):
        raise ValueError("manifest contains duplicate ids or paths")
    for row in rows:
        missing_fields = [field for field in MANIFEST_FIELDS if not row.get(field)]
        if missing_fields:
            raise ValueError(f"manifest row {row.get('id')} is missing: {missing_fields}")
        if not row["canonical_url"].startswith("https://"):
            raise ValueError(f"non-HTTPS canonical URL: {row['canonical_url']}")
        path = ROOT / row["path"]
        if not path.is_file():
            raise FileNotFoundError(f"manifest path is missing: {row['path']}")
        raw_path = ROOT / row["raw_path"]
        if not raw_path.is_file():
            raise FileNotFoundError(f"raw source snapshot is missing: {row['raw_path']}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != row["sha256"]:
            raise ValueError(f"sha256 mismatch: {row['path']}")
    return {
        "document_count": len(rows),
        "sources": dict(sorted(Counter(row["source"] for row in rows).items())),
        "status": "ok",
    }
