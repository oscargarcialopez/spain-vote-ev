"""Fetch every source into data/raw/ with a generic User-Agent and write data/raw/MANIFEST.tsv:
file, SHA-256, size, retrieval time (UTC), URL and, for Wikipedia pages, the revision id, so
a later run can be compared byte for byte or pinned to the same revisions."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from .sources import RAW, SOURCES, USER_AGENT

MANIFEST = RAW / "MANIFEST.tsv"
HEADER = "file\tsha256\tbytes\tretrieved_utc\turl\tnote\n"


def fetch(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_manifest() -> dict[str, dict]:
    if not MANIFEST.exists():
        return {}
    rows = MANIFEST.read_text().splitlines()[1:]
    keys = HEADER.strip().split("\t")
    return {r.split("\t")[0]: dict(zip(keys, r.split("\t"), strict=True)) for r in rows if r}


def write_manifest(entries: dict[str, dict]) -> None:
    keys = HEADER.strip().split("\t")
    lines = [HEADER] + ["\t".join(str(e[k]) for k in keys) + "\n"
                        for _, e in sorted(entries.items())]
    MANIFEST.write_text("".join(lines))


def download(only: list[str] | None = None, refresh_polls: bool = True,
             force: bool = False) -> None:
    """Download what is missing. Wikipedia poll pages are refetched by default (they change
    daily during a campaign); official documents are fetched once."""
    RAW.mkdir(parents=True, exist_ok=True)
    entries = read_manifest()
    for src in SOURCES:
        if only and not any(o in src.file for o in only):
            continue
        path = RAW / src.file
        again = force or (src.kind == "wiki" and refresh_polls)
        if path.exists() and not again and src.file in entries:
            continue
        data = fetch(src.url)
        note = ""
        if src.kind == "wiki":
            parsed = json.loads(data)
            if "error" in parsed:
                raise SystemExit(f"{src.file}: {parsed['error']}")
            note = f"revid={parsed['parse']['revid']}"
        if data[:15].lower().startswith(b"<!doctype html") and src.kind == "file" and \
                not src.file.endswith((".html", ".xml")):
            raise SystemExit(f"{src.url} returned an HTML page instead of {src.file}")
        path.write_bytes(data)
        entries[src.file] = {
            "file": src.file, "sha256": sha256(path), "bytes": len(data),
            "retrieved_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "url": src.url, "note": note,
        }
        print(f"  {src.file:75s} {len(data):>10,d} B  {note}")
        time.sleep(1.0)  # be gentle with public servers
    write_manifest(entries)
    print(f"-> {MANIFEST}")


def verify() -> list[str]:
    """Files whose SHA-256 no longer matches the manifest (or are missing)."""
    bad = []
    for name, e in read_manifest().items():
        path = RAW / name
        if not path.exists() or sha256(path) != e["sha256"]:
            bad.append(name)
    return bad
