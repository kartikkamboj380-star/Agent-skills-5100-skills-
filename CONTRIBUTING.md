# Contributing to AgentSkills

Thanks for helping grow the library! Every contribution must keep the collection **source-verified, legally clean and safe**.

## Adding a skill

1. **Source it** — skills must come from a real, public GitHub repository. Open an issue with the repo URL, or add the repo to the scan list in `scripts/scan_sources.py` and clone it into `.cache/upstream/<owner>_<repo>`.
2. **License first** — the repo (or the skill directory itself) must carry a recognizable license that permits redistribution with attribution (MIT, Apache-2.0, BSD, ISC, CC-BY, CC-BY-SA, MPL-2.0, Unlicense, CC0...). No license → the skill can only be added as a *source-linked catalog-only* entry.
3. **Run the pipeline**:
   ```bash
   python scripts/scan_sources.py
   python scripts/classify_skills.py
   python scripts/deduplicate.py
   python scripts/import_skills.py
   python scripts/add_external_listings.py
   python scripts/generate_catalog.py
   python scripts/validate_skills.py
   ```
4. **Validate** — `scripts/validate_skills.py` must finish with **0 errors**. Include the validation summary in your PR.
5. **Commit** the updated `skills/` tree, `catalog/`, `licenses/` and `report/` outputs together.

## Rules

- **No duplicates**: the dedupe report must show the new skill was not already covered. Alternative sources go into `alternate_sources`, not as new entries.
- **No fabricated entries**: every catalog row must point at a real path in a real repository. PRs with invented links will be rejected.
- **Security**: unlawful, purely offensive, or unsafe skills (remote shells, credential exfiltration, destructive operations) are not bundled. Defensive and authorized-testing skills are welcome and keep their upstream risk labels.
- **Preserve originals**: never rewrite an upstream SKILL.md body. Fix integration issues via the wrapper/importer, not by editing content.
- **Size discipline**: imports are capped (≤10 files, ≤300 KB per skill) to keep the collection cloneable. Larger skills stay catalog-only.

## Reporting problems

Found a misclassified, mislicensed or dangerous skill? Open an issue with the catalog slug (e.g. `coding/python`) — see also [SECURITY.md](SECURITY.md).
