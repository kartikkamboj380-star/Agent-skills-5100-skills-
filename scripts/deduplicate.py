#!/usr/bin/env python3
"""
deduplicate.py - Collapse duplicate skills into single catalog entries.

Duplicate detection (per repository curation policy):
  1. Exact content duplicates: identical SKILL.md SHA-256 (e.g. mirrored
     copies inside one repo, or the same skill vendored across repos).
  2. Same normalized name across repos: the spec treats "normalized skill
     name" as a duplicate signal - the best-maintained version wins and all
     other sources are preserved as alternate source links.

Canonical-source priority: higher GitHub stars first, then import-friendly
license, then alphabetically stable tie-break.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

NO_LICENSE_REPOS = set()  # filled from scan (repo_spdx == "none")


def normalize_name(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = name.lower().replace("-", " ").replace("_", " ").replace(".", " ")
    name = re.sub(r"[^a-z0-9]+", "", name)
    return name


def source_priority(rec: dict) -> tuple:
    """Higher = better canonical candidate."""
    spdx = rec.get("license", "none")
    license_bonus = 1 if spdx in {
        "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Unlicense",
        "CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0", "MPL-2.0", "Zlib",
    } else 0
    return (rec.get("repo_stars", 0), license_bonus, rec.get("source_path", ""))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=".cache/build/classified.json")
    ap.add_argument("--output", default="catalog/skills.json")
    ap.add_argument("--report", default="catalog/dedup_report.json")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as fh:
        data = json.load(fh)

    records = data["skills"]
    repos_meta = {r["repo"]: r for r in data["repos"]}
    for rec in records:
        if rec.get("license") in (None, "none", "NOASSERTION"):
            rec["license"] = rec.get("repo_spdx", "NOASSERTION")

    records.sort(key=lambda r: (-source_priority(r)[0],
                                0 if r["source_path"].startswith("skills/") else 1,
                                r["source_path"].count("/"),
                                r["source_repo"], r["source_path"]))

    by_content: dict[str, dict] = {}
    by_name: dict[str, dict] = {}
    final: list[dict] = []
    dup_content = 0
    dup_name = 0
    dup_report = []

    for rec in records:
        chash = rec["skill_md_sha256"]
        nname = normalize_name(rec["name"])
        alt: dict | None = None
        reason = ""
        if chash in by_content:
            alt = by_content[chash]
            reason = "identical-content"
            dup_content += 1
        elif nname and nname in by_name:
            alt = by_name[nname]
            reason = "same-normalized-name"
            dup_name += 1
        if alt is not None:
            alt.setdefault("alternate_sources", []).append({
                "repo": rec["source_repo"],
                "url": f"https://github.com/{rec['source_repo']}/tree/{rec['source_branch']}/{rec['source_path']}",
                "author": rec["source_owner"],
                "reason": reason,
            })
            dup_report.append({
                "duplicate_of": alt["slug"],
                "reason": reason,
                "repo": rec["source_repo"],
                "path": rec["source_path"],
            })
            continue
        slug = nname or ("skill-" + chash[:12])
        rec["slug"] = slug
        rec["alternate_sources"] = []
        final.append(rec)
        if chash not in by_content:
            by_content[chash] = rec
        if nname and nname not in by_name:
            by_name[nname] = rec

    # Catalog-level flags
    for rec in final:
        rec["import_allowed_license"] = rec["license"] in {
            "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "BSD-4-Clause",
            "ISC", "Unlicense", "CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0", "MPL-2.0", "Zlib",
        }
        repo = repos_meta.get(rec["source_repo"], {})
        rec["source_url"] = f"https://github.com/{rec['source_repo']}/tree/{rec.get('source_branch', 'main')}/{rec['source_path']}"
        rec["source_commit_url"] = f"https://github.com/{rec['source_repo']}/tree/{rec['source_commit']}/{rec['source_path']}"
        rec["repo_description"] = repo.get("description", "")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump({"repos": data["repos"], "skills": final}, fh, ensure_ascii=False, indent=1)
    with open(args.report, "w", encoding="utf-8") as fh:
        json.dump({
            "raw_records": len(records),
            "unique_skills": len(final),
            "exact_content_duplicates_removed": dup_content,
            "same_name_duplicates_removed": dup_name,
            "duplicates": dup_report[:500],
        }, fh, ensure_ascii=False, indent=1)
    print(f"{len(records)} raw -> {len(final)} unique ({dup_content} exact-content dupes, {dup_name} same-name dupes)")


if __name__ == "__main__":
    main()
