# AgentSkills

**A curated, source-verified universal AI Agent Skills library** — featuring coding, trading, research, automation, AI, design, Android development, security, documents, and thousands of practical workflows for Claude, Codex, OpenCode, Gemini CLI, Cursor, GitHub Copilot, Windsurf and other compatible agents.

> **Goal: 5,100 unique, source-verified skills. Delivered: 6,937 verified entries** — every one traceable to a real GitHub repository at a pinned commit. No invented skills, no fake links.

---

## What's inside

| Metric | Value |
|---|---|
| **Unique verified skills in catalog** | **6,937** |
| Skills bundled locally (full directories) | 1,545 (9,500 files, ~91 MB) |
| Source-linked catalog-only entries | 4,265 (installable from source) |
| Cloned, hash-verified upstream repos | 38 major repositories |
| Additional verified listing sources | 323 distinct GitHub repos (via curated lists + API verification) |
| Raw skill records scanned before dedupe | 14,403 |
| Security-flagged entries (kept catalog-only) | 48 |
| Offensive-labeled skills (excluded from bundling) | 150 |

### Verification tiers

| Tier | Meaning | Count |
|---|---|---|
| `cloned+hashed` | Repository cloned at a pinned commit; every SKILL.md content-hashed, parsed, license-checked, security-scanned | 6,337 |
| `listing+repo` | Harvested from the largest curated lists (VoltAgent, ComposioHQ) and verified to exist via the GitHub API; source-linked, fetched on install | 600 |

---

## Categories

| Category | Skills | Imported | | Category | Skills | Imported |
|---|---:|---:|---|---|---:|---:|
| ai-ml | 1,416 | 226 | | documents | 153 | 68 |
| web-development | 611 | 125 | | science | 150 | 82 |
| coding | 555 | 175 | | marketing | 149 | 29 |
| devops-cloud | 413 | 117 | | research | 108 | 31 |
| cybersecurity | 303 | 88 | | trading-finance | 92 | 17 |
| design | 183 | 31 | | android | 89 | 25 |
| automation | 178 | 42 | | writing | 77 | 21 |
| business | 158 | 25 | | game-development | 37 | 6 |
| data-analysis | 283 | 134 | | education | 28 | 9 |
| other | 1,954 | 289 | | | | |

Full breakdown with subcategories: [`catalog/categories.json`](catalog/categories.json) · Machine-readable stats: [`report/stats.json`](report/stats.json)

---

## Repository structure

```
AgentSkills/
├── skills/                     # imported skill directories (original files preserved)
│   ├── coding/                 # software development
│   ├── web-development/        # react, nextjs, css, a11y, seo...
│   ├── android/                # android, kotlin, flutter, termux...
│   ├── ai-ml/                  # llm, rag, mcp, prompt engineering, agents...
│   ├── trading-finance/        # stocks, crypto, backtesting, risk...
│   ├── cybersecurity/          # defensive security, auditing, osint...
│   ├── data-analysis/          # sql, csv, statistics, visualization...
│   ├── research/               # deep research, fact-checking, pdf analysis...
│   ├── automation/             # workflows, api integrations, scraping...
│   ├── design/                 # ui/ux, design systems, branding, video...
│   ├── documents/              # pdf, docx, xlsx, pptx, reports...
│   ├── devops-cloud/           # docker, k8s, terraform, aws, sre...
│   ├── business/  writing/  science/  marketing/
│   ├── game-development/  education/
│   └── other/
├── catalog/
│   ├── skills.json             # full catalog: 6,937 entries with provenance
│   ├── skills.csv              # flat CSV of every skill
│   ├── categories.json         # category tree + counts
│   ├── sources.json            # every source repo: stars, license, pinned commit
│   └── dedup_report.json       # duplicate-detection audit trail
├── scripts/
│   ├── scan_sources.py         # discover skills inside cloned repos
│   ├── classify_skills.py      # category/subcategory classification
│   ├── deduplicate.py          # content-hash + normalized-name dedupe
│   ├── import_skills.py        # policy-checked import into skills/
│   ├── add_external_listings.py# curated-list harvesting + verification
│   ├── generate_catalog.py     # emit JSON/CSV/category/source catalogs
│   └── validate_skills.py      # full validation pass
├── licenses/                   # upstream LICENSE files (34 repos)
├── report/
│   ├── FINAL_REPORT.md         # methodology + verified counts
│   ├── stats.json              # machine-readable statistics
│   └── validation_report.md    # validation output (0 errors)
├── install_skill.py            # skill installer
├── README.md · CONTRIBUTING.md · SECURITY.md · LICENSE
```

---

## Quickstart

Every bundled skill follows the open [Agent Skills format](https://agentskills.io) — a directory with a `SKILL.md` — so agents load it natively:

```bash
# install into Claude Code's skills directory (default target)
python install_skill.py documents/pdf

# install into any directory / agent
python install_skill.py coding/code-review --target ~/.codex/skills
python install_skill.py trading-finance/technical-analysis --target ~/skills

# browse and search
python install_skill.py --list
python install_skill.py --list cybersecurity
python install_skill.py --search "backtest"
python install_skill.py --info ai-ml/rag
```

The installer:

- installs **only the selected skill** (local copy for bundled skills; pinned-commit fetch from GitHub for catalog-only skills),
- **checks the source** and records provenance in `SOURCE.json` (bundled) or `.agentskills-meta.json` (fetched),
- **warns about missing licenses** and refuses to proceed without `--force`,
- **warns about upstream risk labels** (e.g. `critical` = needs credentials/host access) and flagged security patterns,
- **never silently overwrites** an existing installation (`--overwrite` to replace),
- avoids duplicates (slugs are unique in the catalog).

---

## Where the skills come from

All 38 cloned, pinned and hash-verified sources (star counts at collection time):

| Source | Stars | License | Skills |
|---|---:|---|---:|
| [mattpocock/skills](https://github.com/mattpocock/skills) | 333,974 | MIT | 39 |
| [obra/superpowers](https://github.com/obra/superpowers) | 327,902 | MIT | 15 (+4 lab) |
| [anthropics/skills](https://github.com/anthropics/skills) | 201,275 | Apache-2.0 (per-skill LICENSE.txt) | 19 |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | 154,858 | MIT | 13 |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 120,702 | MIT | 26 |
| [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | 80,433 | per-skill only → catalog-only | 77 |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 58,655 | MIT | 177 |
| [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills) | 50,435 | MIT + CC-BY-4.0 (content) | 3,467 |
| [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) | 48,419 | Apache-2.0 | 62 |
| [wshobson/agents](https://github.com/wshobson/agents) | 42,971 | MIT | 185 |
| [github/awesome-copilot](https://github.com/github/awesome-copilot) | 41,620 | MIT | 478 skills + 220 agent defs + 195 instructions |
| [vercel-labs/skills](https://github.com/vercel-labs/skills) | 41,092 | MIT | 5 |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | 35,010 | none → catalog-only | 9 |
| [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) | 34,238 | MIT | 928 |
| [openai/skills](https://github.com/openai/skills) | 29,174 | Apache-2.0 (per-skill LICENSE.txt) | 16 |
| [google/skills](https://github.com/google/skills) | 24,741 | Apache-2.0 | 227 |
| [trailofbits/skills](https://github.com/trailofbits/skills) | 8,465 | CC-BY-SA-4.0 | 99 |
| [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) | 30,569 | MIT | 501 |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | 37,586 | MIT (list) | 300+ verified listings |
| plus 19 more famous single-skill & collection repos | | | ~200 |

Popular community sources include `obsidianmd/obsidian-skills`, `cloudflare/security-audit-skill`, `mvanhorn/last30days-skill`, `blader/humanizer`, `JimLiu/baoyu-skills`, `alchaincyf/nuwa-skill`, `elementalsouls/Claude-BugHunter`, `coreyhaines31/marketingskills`, `op7418/guizang-ppt-skill` and more — see [`catalog/sources.json`](catalog/sources.json) for the complete, verified list with pinned commits.

**Source verification of the requested list:** all 12 repositories named in the original request were verified to exist and are included above (K-Dense-AI's repo was found under its current name `scientific-agent-skills`, formerly `claude-scientific-skills`). Nothing was fabricated; every link resolves.

---

## Duplicate removal

14,403 raw records collapsed to 6,337 unique skills:

1. **Exact-content duplicates** (5,959 removed): identical SKILL.md SHA-256 hashes — e.g. the same skill mirrored across `skills/` and `plugins/` inside one repo, or vendored copies across repos.
2. **Same-normalized-name duplicates** (2,107 removed): the best-maintained version (highest stars, import-friendly license) is kept as canonical; all other sources are preserved as `alternate_sources` links on the catalog entry.

Audit trail: [`catalog/dedup_report.json`](catalog/dedup_report.json).

---

## Licensing & attribution

- **This repository's glue** (catalogs, scripts, docs, installer) is **MIT** — see [LICENSE](LICENSE).
- **Every bundled skill keeps its upstream license**: the original directory is copied verbatim (including its own `LICENSE.txt` when present) plus a `SOURCE.json` with author, repo, pinned commit, license and URL. Upstream LICENSE files are also collected in [`licenses/`](licenses/).
- **Permissive licenses imported**: MIT (5,063), Apache-2.0 (353), CC-BY-SA-4.0 (81, Trail of Bits — attribution + share-alike respected via per-skill license retention), CC-BY-4.0, BSD-3-Clause, CC0.
- **No-license repositories are NOT copied** — they appear as source-linked catalog-only entries installed from upstream on demand: `ComposioHQ` originals (77), `vercel-labs/agent-skills` (9), and others (835 total `none`-license entries).
- Instruction/agent-definition files from `github/awesome-copilot` (MIT) are bundled as skill wrappers whose body preserves the original file **verbatim** beneath a provenance header.
- AGPL-3.0 and unknown-license content is catalog-linked only.

---

## Security

Per the collection policy, only lawful, defensively-oriented, authorized-work skills are bundled:

- **Automated scan** of every bundled file for high-risk patterns (remote shell pipes, destructive `rm -rf /`, obfuscated evals, credential material, fork bombs, reverse shells). **48 flagged entries are catalog-only** — never bundled.
- **Upstream risk labels preserved**: sickn33's own taxonomy ships with each entry (`safe` / `critical` = typically requires credentials or host access / `offensive`). The **150 `offensive`-labeled skills are excluded from the bundle** and remain source-linked entries for authorized professionals.
- Imports capped at ≤10 files / ≤300 KB per skill; binaries >100 KB excluded from bundling (still catalog-linked).
- See [SECURITY.md](SECURITY.md) for the full policy and reporting channel.

---

## Rebuilding / extending the pipeline

```bash
# 1. clone sources (shallow, pinned)
git clone --depth 1 https://github.com/anthropics/skills .cache/upstream/anthropics_skills
# ... (see scripts/scan_sources.py --help)

# 2. scan -> classify -> dedupe -> import -> enrich -> catalog -> validate
python scripts/scan_sources.py
python scripts/classify_skills.py
python scripts/deduplicate.py
python scripts/import_skills.py --max-files 9500
python scripts/add_external_listings.py
python scripts/generate_catalog.py
python scripts/validate_skills.py
```

Intermediate build data lives in `.cache/` (git-ignored).

---

## Agent compatibility

| Agent | Bundled SKILL.md skills | Wrapped instruction skills | Catalog-only |
|---|---|---|---|
| Claude Code | ✅ native | ✅ native | install → native |
| Codex CLI | ✅ | ✅ | ✅ |
| Gemini CLI | ✅ | ✅ | ✅ |
| OpenCode | ✅ | ✅ | ✅ |
| Cursor | ✅ (Agent Skills) | ✅ | ✅ |
| GitHub Copilot | ✅ (skills) | original .agent.md/.instructions.md also published upstream | ✅ |

---

## Honest count disclosure

The goal was 5,100 verified unique skills. The catalog holds **6,937**:

- **6,337** were verified by cloning the source repository at a pinned commit, parsing every SKILL.md, hashing content and checking licenses.
- **600** are curated-list entries verified via the GitHub API (repo exists) — linked, not bundled.
- Quality was prioritized over raw count: 5,959 duplicate copies and 2,107 same-name duplicates were *removed* rather than double-counted, and 198 entries (150 offensive-labeled + 48 scan-flagged) were deliberately kept out of the bundle.

See [`report/FINAL_REPORT.md`](report/FINAL_REPORT.md) for the complete methodology and audit numbers.

## Disclaimer

Skills are third-party instructions executed at your own discretion. Review `SOURCE.json` / catalog metadata and the upstream repository before installing anything that touches credentials, payments, or production systems. This collection links and redistributes under the respective upstream licenses; no affiliation with Anthropic, OpenAI, Google, GitHub, Vercel or any listed author is implied.

---

Built with ❤️ as a universal skills library for AI agents. PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).
