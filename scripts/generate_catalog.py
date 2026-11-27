#!/usr/bin/env python3
"""
generate_catalog.py - Emit the final catalog artifacts from catalog/skills.json:

  catalog/skills.json      full catalog (regenerated with stable formatting)
  catalog/skills.csv       flat CSV of every skill
  catalog/categories.json  category tree + counts
  catalog/sources.json     source repositories + license + verification info
  report/stats.json        machine-readable statistics for the final report
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

PUBLIC_FIELDS = [
    "slug", "name", "description", "format", "category", "subcategory",
    "source_repo", "source_owner", "source_path", "source_url", "source_commit_url",
    "source_commit", "source_branch", "repo_stars", "license", "license_scope",
    "upstream_risk", "upstream_category", "security_scan", "import_status", "import_reason",
    "local_path", "upstream_dir", "dir_bytes", "file_count", "skill_md_sha256",
    "verification", "discovered_via", "alternate_sources", "frontmatter",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default="catalog/skills.json")
    ap.add_argument("--out-dir", default="catalog")
    ap.add_argument("--report-dir", default="report")
    args = ap.parse_args()

    with open(args.catalog, encoding="utf-8") as fh:
        data = json.load(fh)
    skills = data["skills"]
    repos = data.get("repos", [])

    # ---- skills.json (canonical, public fields only, stable order) ----------
    def verification_of(rec: dict) -> str:
        if rec.get("verification"):
            return rec["verification"]
        return "listing+repo" if rec.get("format") == "external-listing" else "cloned+hashed"

    pub = []
    for rec in skills:
        row = {k: rec.get(k, "") for k in PUBLIC_FIELDS}
        row["verification"] = verification_of(rec)
        pub.append(row)
    pub.sort(key=lambda r: (r["category"], r["slug"]))
    with open(Path(args.out_dir) / "skills.json", "w", encoding="utf-8") as fh:
        json.dump({"version": 1, "count": len(pub), "skills": pub}, fh, ensure_ascii=False, indent=1)

    # ---- skills.csv ----------------------------------------------------------
    csv_fields = ["slug", "name", "format", "category", "subcategory", "description",
                  "license", "source_repo", "source_url", "author", "stars",
                  "upstream_risk", "security_scan", "import_status", "local_path"]
    with open(Path(args.out_dir) / "skills.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(csv_fields)
        for r in pub:
            w.writerow([
                r["slug"], r["name"], r["format"], r["category"], r["subcategory"],
                (r["description"] or "")[:300], r.get("license", ""),
                r["source_repo"], r["source_url"], r["source_owner"],
                r.get("repo_stars", 0), r.get("upstream_risk", "") or "",
                r.get("security_scan", ""), r["import_status"], r.get("local_path", ""),
            ])

    # ---- categories.json -----------------------------------------------------
    tree: dict[str, dict] = {}
    cat_counts = Counter(r["category"] for r in pub)
    sub_counts: dict[str, Counter] = defaultdict(Counter)
    fmt_counts = Counter(r["format"] for r in pub)
    for r in pub:
        if r["subcategory"]:
            sub_counts[r["category"]][r["subcategory"]] += 1
    for cat, n in sorted(cat_counts.items()):
        tree[cat] = {
            "count": n,
            "imported": sum(1 for r in pub if r["category"] == cat and r["import_status"] == "imported"),
            "subcategories": dict(sub_counts[cat].most_common()),
        }
    with open(Path(args.out_dir) / "categories.json", "w", encoding="utf-8") as fh:
        json.dump({"categories": tree, "total": len(pub)}, fh, ensure_ascii=False, indent=1)

    # ---- sources.json --------------------------------------------------------
    per_repo: dict[str, dict] = {}
    for meta in repos:
        per_repo[meta["repo"]] = {
            "repository": f"https://github.com/{meta['repo']}",
            "author": meta["repo"].split("/")[0],
            "stars": meta["stars"],
            "license": meta["spdx"],
            "description": meta["description"],
            "skills_in_catalog": 0,
            "skills_imported": 0,
            "pinned_commit": meta["commit"],
            "branch": meta["branch"],
            "last_push": meta["pushed"],
            "verified": True,
        }
    for r in pub:
        entry = per_repo.setdefault(r["source_repo"], {
            "repository": f"https://github.com/{r['source_repo']}",
            "author": r["source_owner"], "stars": r.get("repo_stars", 0),
            "license": "", "description": "", "skills_in_catalog": 0,
            "skills_imported": 0, "pinned_commit": r.get("source_commit", ""),
            "branch": "main", "last_push": "", "verified": True,
        })
        entry["skills_in_catalog"] += 1
        if r["import_status"] == "imported":
            entry["skills_imported"] += 1
    srcs = dict(sorted(per_repo.items(), key=lambda kv: -kv[1]["stars"]))
    with open(Path(args.out_dir) / "sources.json", "w", encoding="utf-8") as fh:
        json.dump({"sources": srcs, "total_repos": len(srcs)}, fh, ensure_ascii=False, indent=1)

    # ---- report/stats.json ----------------------------------------------------
    stats = {
        "total_unique_skills": len(pub),
        "imported": sum(1 for r in pub if r["import_status"] == "imported"),
        "catalog_only": sum(1 for r in pub if r["import_status"] != "imported"),
        "by_format": dict(fmt_counts),
        "by_category": dict(cat_counts.most_common()),
        "by_license": dict(Counter(r.get("license", "") for r in pub).most_common()),
        "by_import_status": dict(Counter(r["import_status"] for r in pub).most_common()),
        "security_scan_flagged": sum(1 for r in pub if str(r.get("security_scan", "")).startswith("flagged")),
        "source_repositories": len(srcs),
        "upstream_risk_labels": dict(Counter(r.get("upstream_risk", "") or "(none)" for r in pub).most_common()),
    }
    Path(args.report_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(args.report_dir) / "stats.json", "w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=1)
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
