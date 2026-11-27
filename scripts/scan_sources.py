#!/usr/bin/env python3
"""
scan_sources.py - Discover Agent Skills inside cloned upstream repositories.

A "skill" is any directory containing a SKILL.md file (Agent Skill format),
or (for select sources) a standalone agent instruction/definition file.

Reads:
  --upstream-dir   directory containing shallow clones named <owner>_<repo>
  --repo-meta      TSV produced from the GitHub API: full_name, stars, license_spdx,
                   pushed_at, default_branch, description, owner_login
  --out            where to write the raw scan JSON

Writes a JSON list of skill records with content hashes, license info and
provenance (commit, branch, GitHub URLs). No upstream file is modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

IGNORE_DIRS = {
    ".git", "node_modules", "dist", "build", "target", "vendor", ".venv",
    "__pycache__", "tests", "spec", "fixtures", "__snapshots__", ".github",
}

# Binary extensions that should never be imported even when small
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".tar",
    ".gz", ".tgz", ".7z", ".rar", ".mp3", ".mp4", ".mov", ".avi", ".wav",
    ".woff", ".woff2", ".ttf", ".otf", ".eot", ".exe", ".dll", ".so", ".dylib",
    ".pyc", ".class", ".jar", ".wasm", ".bin", ".dat", ".db", ".sqlite",
    ".pptx", ".docx", ".xlsx", ".parquet", ".h5", ".hdf5", ".npy", ".npz",
    ".pt", ".pth", ".ckpt", ".safetensors", ".onnx",
}

# SPDX licenses that clearly permit redistribution with attribution/license retention.
IMPORTABLE_LICENSES = {
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "BSD-4-Clause",
    "ISC", "Unlicense", "CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0", "MPL-2.0",
    "Zlib",
}

LICENSE_PATTERNS = [
    ("Apache-2.0", re.compile(r"Apache License\s*(?:,)?\s*Version 2", re.I)),
    ("MPL-2.0", re.compile(r"Mozilla Public License", re.I)),
    ("CC-BY-SA-4.0", re.compile(r"Creative Commons Attribution-ShareAlike 4|Attribution-ShareAlike 4", re.I)),
    ("CC-BY-4.0", re.compile(r"Creative Commons Attribution 4|Attribution 4\.0 International|CC BY 4\.0", re.I)),
    ("CC0-1.0", re.compile(r"CC0|No Rights Reserved|public domain.*waive", re.I | re.S)),
    ("Unlicense", re.compile(r"This is free and unencumbered software released into the public domain", re.I)),
    ("ISC", re.compile(r"ISC License|Permission to use, copy, modify, and/or distribute this software", re.I)),
    ("MIT", re.compile(r"MIT License|Permission is hereby granted, free of charge", re.I)),
    ("BSD-3-Clause", re.compile(r"Redistribution and use in source and binary forms.*Redistributions of source code.*Redistributions in binary form.*neither the name", re.I | re.S)),
    ("BSD-2-Clause", re.compile(r"Redistribution and use in source and binary forms.*Redistributions of source code.*Redistributions in binary form", re.I | re.S)),
    ("Zlib", re.compile(r"This software is provided 'as-is', without any express or implied", re.I)),
    ("GPL-3.0", re.compile(r"GNU GENERAL PUBLIC LICENSE\s*Version 3", re.I)),
    ("GPL-2.0", re.compile(r"GNU GENERAL PUBLIC LICENSE\s*Version 2", re.I)),
    ("LGPL-3.0", re.compile(r"GNU LESSER GENERAL PUBLIC LICENSE\s*Version 3", re.I)),
    ("AGPL-3.0", re.compile(r"GNU AFFERO GENERAL PUBLIC LICENSE", re.I)),
]

# Repos whose extra instruction-file formats should also be cataloged.
INSTRUCTION_SPECS = {
    "github/awesome-copilot": [
        ("agents", "agent-definition", "*.agent.md"),
        ("instructions", "instruction", "*.instructions.md"),
    ],
}

# Repos that ship a machine-readable index with upstream category / risk labels.
UPSTREAM_INDEX_FILES = {
    "sickn33/agentic-awesome-skills": "skills_index.json",
}

# Path fragments never treated as skills (meta/template content, not real skills).
PATH_EXCLUDES = ("/spec/", "/template/", "/skill_categorization/", "/docs/")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sniff_license(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")[:6000]
    except OSError:
        return "none"
    for spdx, pat in LICENSE_PATTERNS:
        if pat.search(text):
            return spdx
    return "NOASSERTION"


def find_license(start: Path, stop: Path) -> Path | None:
    """Look for a LICENSE file in `start` walking up to (not including) `stop`."""
    cur = start
    while cur != stop and cur != cur.parent:
        for child in cur.iterdir():
            if child.is_file() and child.name.upper().startswith(("LICENSE", "LICENSE.MD", "COPYING")):
                if child.name.upper().startswith("LICENSE"):
                    return child
        for child in cur.iterdir():
            if child.is_file() and child.name.upper().startswith("COPYING"):
                return child
        cur = cur.parent
    return None


def parse_frontmatter(text: str) -> dict:
    """Parse a simple YAML frontmatter block, including block scalars (>|)."""
    meta = {}
    m = re.match(r"\A---\s*\n(.*?)\n---\s*(\n|\Z)", text[:16000], re.S)
    if not m:
        return meta
    lines = m.group(1).splitlines()
    i = 0
    while i < len(lines):
        km = re.match(r"^([A-Za-z_-]+)\s*:\s*(.*)$", lines[i])
        if km:
            k = km.group(1).strip().lower()
            v = km.group(2).strip()
            if v in ("|", ">", "|-", ">-", "|+", ">+", "|2", ">2", "|1", ">1"):
                block = []
                i += 1
                while i < len(lines) and (lines[i][:1] in (" ", "\t")):
                    block.append(lines[i].strip())
                    i += 1
                v = " ".join(b for b in block if b)
            else:
                v = v.strip()
                if v.startswith("[") and v.endswith("]"):
                    v = ", ".join(p.strip(" \"'") for p in v[1:-1].split(",") if p.strip())
                else:
                    v = v.strip("\"'").rstrip()
                i += 1
            if v:
                meta[k] = v
            continue
        i += 1
    return meta


def fallback_description(text: str) -> str:
    """First meaningful paragraph after frontmatter."""
    body = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", text[:8000], flags=re.S)
    for para in body.split("\n\n"):
        clean = re.sub(r"[#>*`\[\]]", "", para).strip()
        if len(clean) > 40:
            return clean[:300].replace("\n", " ")
    return ""


def git_commit(repo_dir: Path) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_dir, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return "unknown"


def git_branch(repo_dir: Path) -> str:
    try:
        return subprocess.run(
            ["git", "branch", "--show-current"], cwd=repo_dir, capture_output=True, text=True, check=True
        ).stdout.strip() or "HEAD"
    except Exception:
        return "HEAD"


def scan_skill_dir(skill_md: Path, upstream: Path, meta: dict, commit: str, branch: str) -> dict:
    skill_root = skill_md.parent
    rel_root = skill_root.relative_to(upstream).as_posix()
    files = []
    total_bytes = 0
    largest_binary = 0
    has_binaries = False
    for p in sorted(skill_root.rglob("*")):
        if p.is_dir() or ".git" in p.parts or "node_modules" in p.parts:
            continue
        rel = p.relative_to(skill_root).as_posix()
        size = p.stat().st_size
        is_bin = p.suffix.lower() in BINARY_EXT
        if is_bin:
            has_binaries = True
            largest_binary = max(largest_binary, size)
        files.append({"path": rel, "bytes": size, "binary": is_bin})
        total_bytes += size

    try:
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        text = ""
    fm = parse_frontmatter(text)
    name = fm.get("name") or skill_root.name
    desc = fm.get("description") or fallback_description(text)
    # Repo-relative path (strip the <owner>_<repo> prefix) - this is what
    # appears in GitHub URLs and in upstream index lookups.
    repo_rel = rel_root
    source_path = repo_rel.split("/", 1)[1] if "/" in repo_rel else repo_rel
    # Attach upstream-provided category/risk labels when the repo ships an index.
    idx = meta.get("path_index") or {}
    up = idx.get(source_path) or {}
    upstream_risk = (up.get("risk") or "") if up else ""
    upstream_category = (up.get("category") or "") if up else ""
    upstream_source = (up.get("source") or "") if up else ""

    skill_license_file = None
    for child in skill_root.iterdir():
        if child.is_file() and child.name.upper().startswith("LICENSE"):
            skill_license_file = child
            break
    skill_license = sniff_license(skill_license_file) if skill_license_file else None
    license_spdx = skill_license if skill_license and skill_license not in ("none", "NOASSERTION") else meta["spdx"]

    return {
        "format": "agent-skill",
        "name": name.strip(),
        "description": (desc or "").strip(),
        "source_repo": meta["full_name"],
        "source_owner": meta["owner"],
        "source_path": source_path,
        "source_commit": commit,
        "source_branch": branch,
        "repo_stars": meta["stars"],
        "repo_spdx": meta["spdx"],
        "license": license_spdx,
        "license_scope": "skill" if skill_license_file else "repo",
        "upstream_dir": skill_root.relative_to(upstream.parent).as_posix(),
        "skill_md_sha256": sha256_bytes(text.encode("utf-8", "ignore")),
        "dir_bytes": total_bytes,
        "file_count": len(files),
        "has_binaries": has_binaries,
        "largest_binary": largest_binary,
        "upstream_risk": upstream_risk,
        "upstream_category": upstream_category,
        "upstream_source": upstream_source,
        "frontmatter": {k: v for k, v in fm.items() if k in ("version", "license", "metadata", "allowed-tools")},
    }


def scan_instruction_files(upstream_root: Path, upstream: Path, meta: dict, commit: str, branch: str) -> list:
    repo_key = meta["full_name"]
    specs = INSTRUCTION_SPECS.get(repo_key, [])
    out = []
    for subdir, fmt, pattern in specs:
        base = upstream / subdir
        if not base.is_dir():
            continue
        for p in sorted(base.rglob(pattern[2:].replace("*", "*") if False else pattern)):
            if not p.is_file():
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if len(text) < 200:
                continue
            fm = parse_frontmatter(text)
            name = fm.get("name") or p.stem.replace(".", "-")
            desc = fm.get("description") or fallback_description(text)
            out.append({
                "format": fmt,
                "name": name.strip(),
                "description": (desc or "").strip(),
                "source_repo": meta["full_name"],
                "source_owner": meta["owner"],
                "source_path": p.relative_to(upstream).as_posix(),
                "source_commit": commit,
                "source_branch": branch,
                "repo_stars": meta["stars"],
                "repo_spdx": meta["spdx"],
                "license": meta["spdx"],
                "license_scope": "repo",
                "upstream_dir": p.relative_to(upstream_root.parent).as_posix(),
                "skill_md_sha256": sha256_bytes(text.encode("utf-8", "ignore")),
                "dir_bytes": p.stat().st_size,
                "file_count": 1,
                "has_binaries": False,
                "largest_binary": 0,
                "frontmatter": {},
            })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream-dir", default=".cache/upstream")
    ap.add_argument("--repo-meta", default=".cache/build/repo_meta.tsv")
    ap.add_argument("--out", default=".cache/build/raw_skills.json")
    args = ap.parse_args()

    meta_by_dir = {}
    with open(args.repo_meta, newline="", encoding="utf-8") as fh:
        for row in csv.reader(fh, delimiter="\t"):
            if len(row) < 7:
                continue
            full_name, stars, spdx, pushed, branch, desc, owner = row[0], int(row[1]), row[2], row[3], row[4], row[5], row[6]
            key = full_name.replace("/", "_")
            meta_by_dir[key] = {
                "full_name": full_name, "stars": stars, "spdx": spdx,
                "pushed": pushed, "default_branch": branch, "description": desc, "owner": owner,
            }

    upstream_root = Path(args.upstream_dir)
    records = []
    repos_scanned = []
    for repo_dir in sorted(upstream_root.iterdir()):
        if not repo_dir.is_dir():
            continue
        meta = meta_by_dir.get(repo_dir.name)
        if not meta:
            print(f"  ! no metadata for {repo_dir.name}, skipping")
            continue
        commit = git_commit(repo_dir)
        branch = git_branch(repo_dir)
        idx_file = UPSTREAM_INDEX_FILES.get(meta["full_name"])
        if idx_file:
            idx_path = repo_dir / idx_file
            if idx_path.exists():
                try:
                    entries = json.loads(idx_path.read_text(encoding="utf-8"))
                    meta = dict(meta)
                    meta["path_index"] = {
                        e.get("path", ""): e for e in entries if isinstance(e, dict) and e.get("path")
                    }
                    print(f"  index loaded for {meta['full_name']}: {len(meta['path_index'])} entries")
                except Exception as e:
                    print(f"  ! index unreadable for {meta['full_name']}: {e}")
        repos_scanned.append({
            "repo": meta["full_name"], "dir": repo_dir.name, "commit": commit,
            "branch": branch, "stars": meta["stars"], "spdx": meta["spdx"],
            "pushed": meta["pushed"], "description": meta["description"],
            "default_branch": meta["default_branch"],
        })
        count = 0
        for skill_md in repo_dir.rglob("SKILL.md"):
            rel = skill_md.relative_to(repo_dir).as_posix()
            relposix = "/" + rel
            if any(seg in IGNORE_DIRS for seg in skill_md.parts):
                continue
            if any(exc in relposix for exc in PATH_EXCLUDES):
                continue
            records.append(scan_skill_dir(skill_md, upstream_root, meta, commit, branch))
            count += 1
        records.extend(scan_instruction_files(upstream_root, repo_dir, meta, commit, branch))
        print(f"  {meta['full_name']}: {count} skills")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"repos": repos_scanned, "skills": records}, fh, ensure_ascii=False)
    print(f"scanned {len(repos_scanned)} repos -> {len(records)} raw skill records -> {args.out}")


if __name__ == "__main__":
    main()
