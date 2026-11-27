#!/usr/bin/env python3
"""
add_external_listings.py - Enrich the catalog with entries harvested from the
two largest curated Agent Skills lists:

  * VoltAgent/awesome-agent-skills   (1,400+ curated entries)
  * ComposioHQ/awesome-claude-skills (community curated list)

Entries are kept ONLY when:
  * the target GitHub repository exists (GitHub API check), and
  * the entry is not already in the catalog (same normalized name, or same
    repo+path from a cloned source).

These entries are source-linked (`import_status: catalog-only`,
`verification: listing+repo`) - the skill was not cloned, so no copy is
bundled; the installer fetches them from source on demand.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ENTRY_RE = re.compile(
    r"^[-*]\s*\*?\*\*\[([^\]]+)\]\((https?://github\.com/[^)\s]+)\)\*?\*?\s*[-—:]\s*(.+?)\s*$",
    re.M,
)
GITHUB_URL_RE = re.compile(r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)(?:/(?:tree|blob)/[^/]+/(.*))?")


def normalize(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = name.lower().replace("-", " ").replace("_", " ").replace(".", " ")
    return re.sub(r"[^a-z0-9]+", "", name)


def repo_exists(full_name: str) -> bool:
    r = subprocess.run(
        ["gh", "api", f"repos/{full_name}", "--jq", ".full_name"],
        capture_output=True, text=True, timeout=30,
    )
    return r.returncode == 0 and r.stdout.strip() == full_name


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default="catalog/skills.json")
    ap.add_argument("--readmes", nargs="+", default=[
        ".cache/upstream/VoltAgent_awesome-agent-skills/README.md",
        ".cache/upstream/ComposioHQ_awesome-claude-skills/README.md",
    ])
    ap.add_argument("--list-sources", nargs="+", default=[
        "VoltAgent/awesome-agent-skills", "ComposioHQ/awesome-claude-skills",
    ])
    ap.add_argument("--max", type=int, default=300, help="max new entries to add")
    args = ap.parse_args()

    with open(args.catalog, encoding="utf-8") as fh:
        data = json.load(fh)
    skills = data["skills"]
    known_names = {normalize(s["slug"]) for s in skills}
    known_repo_paths = {(s["source_repo"], s["source_path"].rstrip("/")) for s in skills}

    candidates: dict[str, dict] = {}
    for readme, list_source in zip(args.readmes, args.list_sources):
        p = Path(readme)
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in ENTRY_RE.finditer(text):
            name, url, desc = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            gm = GITHUB_URL_RE.search(url)
            if not gm:
                continue
            owner, repo = gm.group(1), gm.group(2)
            path = (gm.group(3) or "").rstrip("/")
            full = f"{owner}/{repo}"
            if full.lower() in ("github/github",):
                continue
            if (full, path) in known_repo_paths:
                continue
            key = f"{full}::{path}"
            if key not in candidates:
                candidates[key] = {
                    "name": name, "description": desc[:300], "repo": full,
                    "owner": owner, "path": path, "url": url, "list_source": list_source,
                }

    # de-duplicate candidate names against the existing catalog
    fresh = []
    seen_names = set()
    for c in candidates.values():
        n = normalize(c["name"])
        if n in known_names or n in seen_names:
            continue
        seen_names.add(n)
        fresh.append(c)
    print(f"candidate entries after dedupe: {len(fresh)}")

    repos = sorted({c["repo"] for c in fresh})
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = dict(zip(repos, ex.map(repo_exists, repos)))
    verified = [c for c in fresh if results.get(c["repo"])]
    print(f"repos verified: {sum(1 for v in results.values() if v)}/{len(repos)}")
    verified = verified[: args.max]

    added = 0
    for c in verified:
        slug = normalize(c["name"]) or normalize(c["path"] or c["repo"])
        if not slug or slug in known_names:
            continue
        skills.append({
            "format": "external-listing",
            "name": c["name"],
            "description": c["description"],
            "source_repo": c["repo"],
            "source_owner": c["owner"],
            "source_path": c["path"],
            "source_commit": "",
            "source_branch": "HEAD",
            "repo_stars": 0,
            "repo_spdx": "",
            "license": "unknown",
            "license_scope": "",
            "upstream_dir": "",
            "skill_md_sha256": "",
            "dir_bytes": 0,
            "file_count": 0,
            "has_binaries": False,
            "largest_binary": 0,
            "upstream_risk": "",
            "upstream_category": "",
            "upstream_source": "",
            "frontmatter": {},
            "slug": slug,
            "alternate_sources": [],
            "import_allowed_license": False,
            "source_url": c["url"],
            "source_commit_url": c["url"],
            "repo_description": "",
            "category": "other",
            "subcategory": "",
            "classification": "external-listing",
            "category_dir": "other",
            "verification": "listing+repo",
            "discovered_via": c["list_source"],
            "import_status": "catalog-only",
            "import_reason": "external-listing:not-cloned",
            "security_scan": "not-scanned",
            "local_path": "",
        })
        known_names.add(slug)
        added += 1

    with open(args.catalog, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(f"added {added} verified external listings -> {args.catalog}")


def _classify_external_entries() -> None:
    """(Re)apply keyword classification to external-listing entries in place."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from classify_skills import CATEGORY_DIRS, classify_text  # noqa: E402

    with open(Path(__file__).parent.parent / "catalog" / "skills.json", encoding="utf-8") as fh:
        data = json.load(fh)
    changed = 0
    for rec in data["skills"]:
        if rec.get("format") != "external-listing":
            continue
        cat, sub, _how = classify_text(rec["name"], rec.get("description", ""), rec["source_repo"])
        rec["category"] = cat
        rec["subcategory"] = sub
        rec["category_dir"] = CATEGORY_DIRS.get(cat, "other")
        changed += 1
    with open(Path(__file__).parent.parent / "catalog" / "skills.json", "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(f"re-classified {changed} external-listing entries")


if __name__ == "__main__":
    main()
    _classify_external_entries()


if __name__ == "__main__":
    main()
