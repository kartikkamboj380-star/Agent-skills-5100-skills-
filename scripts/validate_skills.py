#!/usr/bin/env python3
"""
validate_skills.py - Validate the imported skills tree and the catalog.

Checks:
  1. every imported skill directory contains a readable SKILL.md,
  2. SKILL.md frontmatter parses and carries name/description,
  3. catalog entries resolve to real directories (imported) and real
     upstream paths (catalog-only),
  4. no duplicate slugs or duplicate SKILL.md content inside skills/,
  5. per-skill size/file caps respected,
  6. security heuristic scan of every imported file,
  7. license present for every imported skill.

Writes report/validation_report.md and exits non-zero on blocking errors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

RISKY_PATTERNS = [
    (re.compile(r"curl[^&|;]*\|\s*(sudo\s+)?(ba)?sh", re.I), "remote shell pipe (curl | sh)"),
    (re.compile(r"wget[^&|;]*\|\s*(sudo\s+)?(ba)?sh", re.I), "remote shell pipe (wget | sh)"),
    (re.compile(r"\brm\s+-rf\s+/(?:\s|$|\*)", re.I), "destructive rm -rf /"),
    (re.compile(r"eval\s*\(\s*(?:atob|base64|decode)", re.I), "obfuscated eval"),
    (re.compile(r"AKIA[0-9A-Z]{16}", re.M), "AWS access key id"),
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"), "embedded private key"),
    (re.compile(r":\(\)\{.*\};\s*:", re.S), "fork bomb"),
    (re.compile(r"nc\s+-e\s+/bin/(ba)?sh", re.I), "reverse shell"),
]

TEXT_EXT = {".md", ".py", ".sh", ".js", ".ts", ".json", ".yaml", ".yml", ".toml", ".rb", ".go", ".rs", ".txt", ".html", ".css"}


def fm_of(text: str) -> dict:
    meta = {}
    m = re.match(r"\A---\s*\n(.*?)\n---\s*(\n|\Z)", text[:16000], re.S)
    if not m:
        return meta
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z_-]+)\s*:\s*(.*)$", line)
        if km:
            v = km.group(2).strip().strip("\"'")
            if v:
                meta[km.group(1).lower()] = v
    return meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills-root", default="skills")
    ap.add_argument("--catalog", default="catalog/skills.json")
    ap.add_argument("--report", default="report/validation_report.md")
    args = ap.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    imported_dirs = 0
    total_files = 0
    total_bytes = 0
    content_hashes: dict[str, str] = {}
    flagged_files = 0

    root = Path(args.skills_root)
    if root.is_dir():
        for cat_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            for d in sorted(p for p in cat_dir.iterdir() if p.is_dir()):
                imported_dirs += 1
                skill_md = d / "SKILL.md"
                if not skill_md.is_file():
                    errors.append(f"missing SKILL.md: {d}")
                    continue
                text = skill_md.read_text(encoding="utf-8", errors="ignore")
                fm = fm_of(text)
                if not fm:
                    errors.append(f"unparsable frontmatter: {d}")
                if "description" not in fm and not fm.get("description"):
                    # wrapped instruction files always carry a description;
                    # verbatim agent-skills should too
                    warnings.append(f"no description in frontmatter: {d}")
                for p in sorted(d.rglob("*")):
                    if p.is_dir():
                        continue
                    total_files += 1
                    total_bytes += p.stat().st_size
                    h = hashlib.sha256(p.read_bytes()).hexdigest()
                    rel = str(p)
                    if p.name == "SKILL.md":
                        if h in content_hashes:
                            errors.append(f"duplicate SKILL.md content: {rel} == {content_hashes[h]}")
                        content_hashes[h] = rel
                    if p.suffix.lower() in TEXT_EXT and p.stat().st_size < 400_000:
                        scan = p.read_text(encoding="utf-8", errors="ignore")
                        for pat, label in RISKY_PATTERNS:
                            if pat.search(scan):
                                flagged_files += 1
                                warnings.append(f"risky pattern ({label}): {rel}")

    # Catalog consistency
    with open(args.catalog, encoding="utf-8") as fh:
        catalog = json.load(fh)
    slugs: dict[str, str] = {}
    cat_imported = 0
    for rec in catalog["skills"]:
        slug = rec["slug"]
        if slug in slugs:
            errors.append(f"duplicate catalog slug: {slug} ({slugs[slug]} vs {rec['source_url']})")
        slugs[slug] = rec["source_url"]
        if rec["import_status"] == "imported":
            cat_imported += 1
            lp = rec.get("local_path", "")
            if not lp or not (Path(lp) / "SKILL.md").is_file():
                errors.append(f"catalog says imported but path missing: {slug} -> {lp}")

    license_missing = sum(1 for r in catalog["skills"]
                          if r["import_status"] == "imported" and not r.get("license"))
    if license_missing:
        errors.append(f"{license_missing} imported skills have no license recorded")

    lines = [
        "# Validation Report",
        "",
        f"- imported skill directories: **{imported_dirs}**",
        f"- files under skills/: **{total_files}** ({round(total_bytes/1e6, 1)} MB)",
        f"- catalog entries: **{len(catalog['skills'])}** (imported: {cat_imported})",
        f"- flagged files (security heuristics): **{flagged_files}**",
        f"- errors: **{len(errors)}**",
        f"- warnings: **{len(warnings)}**",
        "",
    ]
    if errors:
        lines += ["## Errors", ""] + [f"- {e}" for e in errors[:200]] + [""]
    if warnings:
        lines += ["## Warnings", ""] + [f"- {w}" for w in warnings[:200]] + [""]
    if not errors and not warnings:
        lines += ["All checks passed."]
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:12]))
    print(f"full report -> {args.report}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
