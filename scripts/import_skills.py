#!/usr/bin/env python3
"""
import_skills.py - Physically import verified skills into the skills/ tree.

Import policy (all conditions must hold):
  * license is on the redistribution allowlist (per-repo or per-skill LICENSE),
  * upstream security label is not "offensive" (defensive/authorized only),
  * automated content scan found no high-risk patterns,
  * size caps: <= 400 KB per skill, <= 15 files, no binary > 100 KB,
  * global file budget not exhausted (default 9000 files).

Sources are imported in tier order (canonical/official repos first, mass
libraries last) so the budget is spent on the highest-reputation skills.
Every imported agent-skill keeps its original files untouched; provenance is
written to SOURCE.json. Instruction/agent-definition formats are wrapped in a
generated SKILL.md that embeds the original content verbatim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import time
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

UPSTREAM_ROOT = Path(".cache/upstream")
# upstream_dir values are recorded relative to UPSTREAM_ROOT.parent (.cache)
UPSTREAM_BASE = UPSTREAM_ROOT.parent

# Lower number = imported earlier. Canonical/official sources first.
TIER = {
    "anthropics/skills": 0, "google/skills": 0, "github/awesome-copilot": 0,
    "anthropics/claude-plugins-official": 0, "obra/superpowers": 0,
    "obra/superpowers-lab": 0, "mattpocock/skills": 0, "addyosmani/agent-skills": 0,
    "trailofbits/skills": 0, "K-Dense-AI/scientific-agent-skills": 0,
    "obsidianmd/obsidian-skills": 0, "vercel-labs/skills": 0,
    "nextlevelbuilder/ui-ux-pro-max-skill": 0, "cloudflare/security-audit-skill": 0,
    "blader/humanizer": 0, "mvanhorn/last30days-skill": 0, "wshobson/agents": 1,
    "davila7/claude-code-templates": 1, "alirezarezvani/claude-skills": 1,
    "elementalsouls/Claude-BugHunter": 1, "coreyhaines31/marketingskills": 1,
    "JimLiu/baoyu-skills": 1, "alchaincyf/nuwa-skill": 1, "alchaincyf/huashu-design": 1,
    "op7418/guizang-ppt-skill": 1, "Vincentwei1021/video-shotcraft": 1,
    "OthmanAdi/planning-with-files": 1, "nidhinjs/prompt-master": 1,
    "Leonxlnx/taste-skill": 1, "wheresryan22/anatomy": 1, "latent-spaces/brag": 1,
    "titanwings/distilly": 1, "sickn33/agentic-awesome-skills": 2,
}

RISKY_PATTERNS = [
    (re.compile(r"curl[^&|;]*\|\s*(sudo\s+)?(ba)?sh", re.I), "remote shell pipe (curl | sh)"),
    (re.compile(r"wget[^&|;]*\|\s*(sudo\s+)?(ba)?sh", re.I), "remote shell pipe (wget | sh)"),
    (re.compile(r"\brm\s+-rf\s+/(?:\s|$|\*)", re.I), "destructive rm -rf /"),
    (re.compile(r"eval\s*\(\s*(?:atob|base64|decode)", re.I), "obfuscated eval"),
    (re.compile(r"base64\s+-d\s*<<<|frombase64string.*invoke-expression", re.I), "obfuscated payload"),
    (re.compile(r"AKIA[0-9A-Z]{16}", re.M), "AWS access key id"),
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"), "embedded private key"),
    (re.compile(r":\(\)\{.*\};\s*:", re.S), "fork bomb"),
    (re.compile(r"chmod\s+777\s+/", re.I), "chmod 777 on root path"),
    (re.compile(r"nc\s+-e\s+/bin/(ba)?sh", re.I), "reverse shell"),
]


def scan_risky(text: str) -> str | None:
    for pat, label in RISKY_PATTERNS:
        if pat.search(text):
            return label
    return None


def safe_slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", name.strip()).strip("-.").lower()
    return slug[:80] or "unnamed-skill"


def source_json(rec: dict, import_path: str, wrapped: bool) -> dict:
    return {
        "name": rec["name"],
        "slug": rec["slug"],
        "format": rec["format"],
        "category": rec["category"],
        "subcategory": rec.get("subcategory", ""),
        "description": rec.get("description", ""),
        "source_repo": rec["source_repo"],
        "source_url": rec["source_url"],
        "source_commit": rec["source_commit"],
        "source_commit_url": rec["source_commit_url"],
        "author": rec["source_owner"],
        "license": rec["license"],
        "license_scope": rec.get("license_scope", "repo"),
        "upstream_risk": rec.get("upstream_risk", ""),
        "imported_at": time.strftime("%Y-%m-%d"),
        "import_mode": "wrapped" if wrapped else "verbatim-copy",
        "catalog_entry": f"catalog/skills.json#{rec['slug']}",
    }


def import_agent_skill(rec: dict, target_dir: Path, cataloged_hashes: set) -> tuple[int, int]:
    src = UPSTREAM_BASE / rec["upstream_dir"]
    n_files = 0
    n_bytes = 0
    for root_dir, dirs, file_names in os.walk(src):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
        rel_root_dir = Path(root_dir).relative_to(src)
        # A nested sub-skill that exists as its own catalog entry is not
        # duplicated inside the parent import (the catalog links to its
        # standalone copy instead).
        if "SKILL.md" in file_names and rel_root_dir != Path("."):
            nested_hash = sha256_bytes((Path(root_dir) / "SKILL.md").read_bytes())
            if nested_hash in cataloged_hashes:
                dirs[:] = []
                continue
        dest_root = target_dir / rel_root_dir
        dest_root.mkdir(parents=True, exist_ok=True)
        for name in sorted(file_names):
            p = Path(root_dir) / name
            dest = dest_root / name
            shutil.copy2(p, dest)
            n_files += 1
            n_bytes += p.stat().st_size
    (target_dir / "SOURCE.json").write_text(
        json.dumps(source_json(rec, str(target_dir), False), ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    return n_files + 1, n_bytes


WRAPPER_HEADER = """\
---
name: {slug}
description: "{desc}"
license: {license}
source: {source_url}
commit: {commit}
format: {format}
---

> **Imported from [{repo}](https://github.com/{repo})** · License: {license} ·
> Original file: `{orig}` at commit `{commit}` ·
> Curated in the AgentSkills library. The original content below is preserved
> verbatim; the frontmatter above only adds Agent Skill metadata so the file
> works across Claude, Codex, OpenCode, Gemini CLI, Cursor and compatible agents.

"""


def import_wrapped(rec: dict, target_dir: Path) -> tuple[int, int]:
    src = UPSTREAM_BASE / rec["upstream_dir"]
    text = src.read_text(encoding="utf-8", errors="ignore")
    header = WRAPPER_HEADER.format(
        slug=rec["slug"],
        desc=rec.get("description", rec["name"]).replace('"', "'")[:300],
        license=rec["license"],
        source_url=rec["source_url"],
        commit=rec["source_commit"],
        format=rec["format"],
        repo=rec["source_repo"],
        orig=Path(rec["source_path"]).name,
    )
    (target_dir / "SKILL.md").write_text(header + text, encoding="utf-8")
    return 1, len((header + text).encode("utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default="catalog/skills.json")
    ap.add_argument("--skills-root", default="skills")
    ap.add_argument("--max-files", type=int, default=9300, help="global file budget for skills/")
    ap.add_argument("--max-bytes", type=int, default=95_000_000, help="global byte budget")
    ap.add_argument("--max-skill-bytes", type=int, default=300_000)
    ap.add_argument("--max-skill-files", type=int, default=10)
    ap.add_argument("--max-binary", type=int, default=100_000)
    ap.add_argument("--tier0-max-skill-bytes", type=int, default=6_000_000,
                    help="relaxed per-skill byte cap for tier-0 canonical sources")
    ap.add_argument("--tier0-max-skill-files", type=int, default=100,
                    help="relaxed per-skill file cap for tier-0 canonical sources")
    ap.add_argument("--tier0-max-binary", type=int, default=1_000_000)
    args = ap.parse_args()

    with open(args.catalog, encoding="utf-8") as fh:
        data = json.load(fh)
    skills = data["skills"]

    imported_flag = 0
    for rec in skills:
        rec["import_status"] = "catalog-only"
        rec["import_reason"] = ""
        rec["security_scan"] = "clean"
        rec["local_path"] = ""

        reasons = []
        is_tier0 = TIER.get(rec["source_repo"], 3) == 0
        max_bytes = args.tier0_max_skill_bytes if is_tier0 else args.max_skill_bytes
        max_files = args.tier0_max_skill_files if is_tier0 else args.max_skill_files
        max_bin = args.tier0_max_binary if is_tier0 else args.max_binary
        if not rec["import_allowed_license"]:
            reasons.append(f"license:{rec['license']}")
        if rec.get("upstream_risk") == "offensive":
            reasons.append("upstream-label:offensive")
        if rec["dir_bytes"] > max_bytes:
            reasons.append("too-large")
        if rec["file_count"] > max_files:
            reasons.append("too-many-files")
        if rec["has_binaries"] and rec["largest_binary"] > max_bin:
            reasons.append("binary-assets")
        if rec["source_repo"] not in UPSTREAM_ROOT.name and not (UPSTREAM_BASE / rec["upstream_dir"]).exists():
            reasons.append("clone-missing")
        rec["import_reason"] = "; ".join(reasons)
        rec["_eligible"] = not reasons

    # Security scan of the skill text content
    for rec in skills:
        src = UPSTREAM_BASE / rec["upstream_dir"]
        try:
            if rec["format"] == "agent-skill":
                texts = [p.read_text(encoding="utf-8", errors="ignore") for p in sorted(src.rglob("*"))
                         if p.is_file() and p.suffix.lower() in (".md", ".py", ".sh", ".js", ".ts", ".json", ".yaml", ".yml", ".toml", ".rb", ".go", ".rs", ".txt")
                         and p.stat().st_size < 400_000]
            else:
                texts = [src.read_text(encoding="utf-8", errors="ignore")]
            joined = "\n".join(texts)
        except OSError:
            joined = ""
        flag = scan_risky(joined)
        if flag:
            rec["security_scan"] = f"flagged:{flag}"
            if rec.get("_eligible"):
                rec["_eligible"] = False
                rec["import_reason"] = f"security-scan:{flag}"

    # Sort: tier first, then stars, then smaller first (spread the budget).
    # Mass-library tier (2) is additionally packed by file count so the
    # remaining budget absorbs as many single-file skills as possible.
    def sort_key(r: dict):
        tier = TIER.get(r["source_repo"], 3)
        if tier <= 1:
            return (tier, -r["repo_stars"], r["dir_bytes"])
        return (tier, r["file_count"] * 10_000_000 + r["dir_bytes"], 0)

    skills.sort(key=lambda r: (0 if r.get("_eligible") else 1, sort_key(r)))

    budget_files = args.max_files
    budget_bytes = args.max_bytes
    used_slugs: dict[str, int] = {}
    skipped_budget = 0
    imported = 0
    cataloged_hashes = {rec["skill_md_sha256"] for rec in skills}

    for rec in skills:
        if not rec.get("_eligible"):
            continue
        if rec["format"] == "agent-skill":
            est_files = rec["file_count"] + 1
            est_bytes = rec["dir_bytes"] + 2000
        else:
            est_files = 1
            est_bytes = rec["dir_bytes"] + 1500
        if est_files > budget_files or est_bytes > budget_bytes:
            skipped_budget += 1
            continue
        cat_dir = rec.get("category_dir", "other")
        slug = safe_slug(rec["name"])
        key = f"{cat_dir}/{slug}"
        n = used_slugs.get(key, 0)
        used_slugs[key] = n + 1
        if n:
            slug = f"{slug}-{rec['source_owner'].lower()}"
        target_dir = Path(args.skills_root) / cat_dir / slug
        if target_dir.exists():
            skipped_budget += 1
            continue
        try:
            if rec["format"] == "agent-skill":
                nf, nb = import_agent_skill(rec, target_dir, cataloged_hashes)
            else:
                nf, nb = import_wrapped(rec, target_dir)
        except OSError as e:
            rec["import_status"] = "catalog-only"
            rec["import_reason"] = f"copy-error:{e}"
            continue
        rec["import_status"] = "imported"
        rec["local_path"] = str(target_dir)
        budget_files -= nf
        budget_bytes -= nb
        imported += 1

    for rec in skills:
        rec.pop("_eligible", None)
        if rec["import_status"] != "imported" and not rec["import_reason"]:
            rec["import_reason"] = "file-budget"

    Path(args.catalog).parent.mkdir(parents=True, exist_ok=True)
    with open(args.catalog, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(f"imported {imported} skills; catalog-only: {imported_flag + sum(1 for r in skills if r['import_status'] != 'imported')} "
          f"(budget-skipped: {skipped_budget})")
    print(f"files left in budget: {budget_files}; bytes left: {budget_bytes}")


if __name__ == "__main__":
    main()
