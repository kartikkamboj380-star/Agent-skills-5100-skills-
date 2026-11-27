# Security Policy

## Scope of this collection

AgentSkills redistributes and links to third-party AI agent skills. Security here means **keeping unsafe content out of the bundle and being transparent about what ships**.

## What is done before a skill is bundled

1. **Source pinning** — every bundled skill records the upstream repo, path, branch and exact commit hash (`SOURCE.json`, `catalog/skills.json`).
2. **License gate** — skills from repositories without a redistribution-permitting license are **never copied**; they remain source-linked catalog entries.
3. **Automated content scan** — all bundled text files are scanned for high-risk patterns, including:
   - remote code execution pipes (`curl … | sh`, `wget … | sh`)
   - destructive commands (`rm -rf /`)
   - obfuscated payloads (`eval(base64…)`, `base64 -d <<<`)
   - embedded credentials (`AKIA…` AWS keys, private key blocks)
   - fork bombs and reverse shells
   - `chmod 777 /` on system paths
   
   Flagged skills (currently **48**) are excluded from the bundle and marked `security_scan: flagged:<reason>` in the catalog.
4. **Upstream risk labels preserved** — sources that publish their own risk taxonomy (e.g. `sickn33/agentic-awesome-skills` with `safe` / `critical` / `offensive`) have those labels copied verbatim into catalog entries and `SOURCE.json`. Skills labeled **`offensive` are never bundled** (150 entries stay catalog-only, for authorized professionals). Skills labeled `critical` (typically "requires API keys / cloud credentials / host paths") may be bundled but the installer warns before installing.
5. **Size & content caps** — bundles are limited to ≤10 files and ≤300 KB per skill; binary assets >100 KB are not bundled.
6. **Post-import validation** — `scripts/validate_skills.py` re-scans the whole `skills/` tree (frontmatter validity, duplicate detection, pattern scan, catalog↔tree consistency) and must report **0 errors**.

## What is NOT done (limitations)

- No skill is manually reviewed line-by-line; the scan is heuristic. Treat every skill as untrusted third-party input.
- No sandboxing: installing a skill only copies files, but **executing** an agent skill runs its instructions with your agent's permissions.
- Upstream repositories can change after our pinned commit; re-verify before use in sensitive environments.

## Safe usage recommendations

- Install skills individually (`python install_skill.py <category/slug>`) rather than bulk-copying, and read the `SKILL.md` first.
- Prefer skills whose `security_scan` is `clean` and `upstream_risk` is `safe`/empty.
- Run agents with least-privilege filesystem and network access when trying new skills.
- Watch for skills that ask your agent to fetch remote code or enter credentials.

## Reporting a vulnerability or unsafe skill

Open a GitHub issue titled `[security] <slug>` describing the skill, the catalog entry, and the concern — or reach the maintainer via the repository contact. Entries found to be dangerous will be removed from `skills/` and marked flagged in the catalog within the next update.
