#!/usr/bin/env python3
"""
install_skill.py - Install skills from the AgentSkills catalog.

Usage:
  python install_skill.py <category/slug>          # e.g. coding/python
  python install_skill.py <slug>                   # unique slug match
  python install_skill.py --search <query>         # search the catalog
  python install_skill.py --list [category]        # list skills
  python install_skill.py --info <category/slug>   # show metadata

Options:
  --target DIR    install destination (default: ~/.claude/skills)
  --force         install even when warnings are present
  --overwrite     replace an already-installed skill

Behavior:
  * imported skills are copied from the local skills/ tree,
  * catalog-only skills are fetched from their GitHub source at the pinned
    commit (blobless sparse clone, with a codeload tarball fallback),
  * missing licenses, flagged security scans and upstream risk labels are
    reported before installing,
  * an existing installation is never silently overwritten.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CATALOG = Path(__file__).parent / "catalog" / "skills.json"
SKILLS_ROOT = Path(__file__).parent / "skills"


def load_catalog() -> list[dict]:
    if not CATALOG.exists():
        sys.exit("catalog/skills.json not found - run scripts/generate_catalog.py first")
    with open(CATALOG, encoding="utf-8") as fh:
        return json.load(fh)["skills"]


def resolve(query: str, skills: list[dict]) -> dict | None:
    query = query.strip().strip("/").lower()
    for s in skills:
        if f"{s['category']}/{s['slug']}" == query or f"{s.get('category_dir', s['category'])}/{s['slug']}" == query:
            return s
    exact = [s for s in skills if s["slug"] == query]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        print(f"'{query}' is ambiguous ({len(exact)} matches). Use category/slug:")
        for s in exact[:10]:
            print(f"  {s['category']}/{s['slug']}  ({s['source_repo']})")
        sys.exit(1)
    return None


def warnings_for(skill: dict) -> list[str]:
    out = []
    if not skill.get("license") or skill.get("license") in ("none", "NOASSERTION"):
        out.append("no license found upstream - redistribution may not be permitted")
    scan = str(skill.get("security_scan", ""))
    if scan.startswith("flagged"):
        out.append(f"security scan flagged this skill: {scan.split(':', 1)[1]}")
    risk = skill.get("upstream_risk", "")
    if risk and risk not in ("safe", "none", "unknown", ""):
        out.append(f"upstream risk label: {risk} (review before use)")
    return out


def copy_local(skill: dict, target: Path) -> bool:
    src = Path(skill["local_path"])
    if not src.is_dir():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, target, dirs_exist_ok=True)
    return True


def fetch_from_source(skill: dict, target: Path) -> bool:
    """Fetch a catalog-only skill from GitHub at the pinned commit."""
    repo = skill["source_repo"]
    rel_path = skill["source_path"]
    commit = skill.get("source_commit", "")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        clone = Path(td) / "repo"
        env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
        base = ["git", "-c", "protocol.version=2", "clone", "--filter=blob:none", "--no-checkout", "--depth", "1"]
        cmds = []
        if commit and commit != "unknown":
            cmds.append(base + [f"https://github.com/{repo}.git", str(clone)])
            cmds.append(["git", "-C", str(clone), "fetch", "--depth", "1", "origin", commit])
            cmds.append(["git", "-C", str(clone), "checkout", commit, "--", rel_path])
        else:
            cmds.append(base + [f"https://github.com/{repo}.git", str(clone)])
            cmds.append(["git", "-C", str(clone), "checkout", "HEAD", "--", rel_path])
        ok = True
        for cmd in cmds:
            r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=300)
            if r.returncode != 0:
                ok = False
                break
        fetched = clone / rel_path
        if ok and fetched.exists():
            if fetched.is_dir():
                shutil.copytree(fetched, target, dirs_exist_ok=True)
            else:
                target.mkdir(parents=True, exist_ok=True)
                shutil.copy2(fetched, target / fetched.name)
            meta = {k: skill.get(k, "") for k in
                    ("slug", "name", "source_repo", "source_url", "source_commit", "license", "upstream_risk")}
            (target / ".agentskills-meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
            return True
    # Fallback: codeload tarball of the default branch
    branch = skill.get("source_branch") or "main"
    url = f"https://codeload.github.com/{repo}/tar.gz/refs/heads/{branch}"
    import tarfile
    import urllib.request
    try:
        with tempfile.TemporaryDirectory() as td:
            tgz = Path(td) / "repo.tar.gz"
            urllib.request.urlretrieve(url, tgz)  # noqa: S310 - fixed https URL
            prefix = repo.split("/")[-1] + "-" + branch.replace("/", "-")
            with tarfile.open(tgz, "r:gz") as tf:
                members = [m for m in tf.getmembers()
                           if m.name.startswith(prefix + "/" + rel_path.rstrip("/") + ("/" if skill.get("is_dir", True) else ""))]
                tf.extractall(td, members=members)  # noqa: S202 - controlled members list
            src = Path(td) / prefix / rel_path
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, target, dirs_exist_ok=True)
                else:
                    target.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, target / src.name)
                return True
    except Exception as e:
        print(f"  fetch failed: {e}")
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Install an AgentSkills catalog skill")
    ap.add_argument("query", nargs="?", help="category/slug or slug")
    ap.add_argument("--search", dest="search", help="search the catalog")
    ap.add_argument("--list", dest="list_cat", nargs="?", const="all", help="list skills [category]")
    ap.add_argument("--info", action="store_true", help="show metadata only")
    ap.add_argument("--target", default=str(Path.home() / ".claude" / "skills"),
                    help="install destination (default ~/.claude/skills)")
    ap.add_argument("--force", action="store_true", help="install despite warnings")
    ap.add_argument("--overwrite", action="store_true", help="replace existing installation")
    args = ap.parse_args()

    skills = load_catalog()

    if args.list_cat:
        cat = None if args.list_cat == "all" else args.list_cat
        for s in sorted(skills, key=lambda x: (x["category"], x["slug"])):
            if cat and s["category"] != cat:
                continue
            mark = "installed-dir" if s["import_status"] == "imported" else "source-fetch"
            print(f"{s['category']}/{s['slug']:<45} [{s['license'] or 'no-license'}] {mark}")
        print(f"\n{len(skills)} skills total. Install with: python install_skill.py <category/slug>")
        return

    if args.search:
        q = args.search.lower()
        hits = [s for s in skills if q in s["slug"].lower() or q in s["name"].lower()
                or q in (s.get("description") or "").lower()][:20]
        for s in hits:
            print(f"{s['category']}/{s['slug']:<45} {s['source_repo']}")
        print(f"\n{len(hits)} result(s)")
        return

    if not args.query:
        ap.print_help()
        return

    skill = resolve(args.query, skills)
    if not skill:
        print(f"skill '{args.query}' not found. Try --search.")
        sys.exit(1)

    if args.info:
        print(json.dumps({k: v for k, v in skill.items() if k != "frontmatter"}, indent=1, ensure_ascii=False)[:4000])
        return

    warns = warnings_for(skill)
    if warns:
        for w in warns:
            print(f"WARNING: {w}")
        if not args.force:
            print("Re-run with --force to install anyway.")
            sys.exit(2)

    target = Path(args.target) / skill["slug"]
    if target.exists():
        if args.overwrite:
            shutil.rmtree(target)
        else:
            print(f"already installed: {target} (use --overwrite to replace)")
            sys.exit(0)

    print(f"installing {skill['category']}/{skill['slug']} -> {target}")
    if skill["import_status"] == "imported" and copy_local(skill, target):
        print("  copied from local library (verified copy)")
    else:
        print(f"  fetching from source {skill['source_repo']} @ {skill.get('source_commit', '')[:10]}")
        if not fetch_from_source(skill, target):
            print("  FAILED to fetch from source")
            sys.exit(1)
    print("done. Restart your agent session to pick up the new skill.")


if __name__ == "__main__":
    main()
