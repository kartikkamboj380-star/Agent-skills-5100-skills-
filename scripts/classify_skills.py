#!/usr/bin/env python3
"""
classify_skills.py - Assign category + subcategory to every scanned skill.

Heuristic, explainable keyword classifier. Rules are ordered by specificity:
the first matching rule wins. A per-source bias map gives a fallback category
for skills whose name/description carry no keywords (e.g. single-skill repos,
where the repo topic IS the category).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# (category, subcategory, compiled regex) - first match wins.
RULES: list[tuple[str, str, re.Pattern]] = []


def rule(category: str, subcategory: str, pattern: str):
    RULES.append((category, subcategory, re.compile(pattern, re.I)))


# --- Trading & Finance -------------------------------------------------------
rule("trading-finance", "Crypto Research", r"\bcrypto(currency|currencies)?\b|\bbitcoin\b|\bethereum\b|\bblockchain\b|\bweb3\b|\bdefi\b|\bnft\b")
rule("trading-finance", "Forex Research", r"\bforex|currency pair|fx trading")
rule("trading-finance", "Trading Strategy Research", r"trading (strategy|plan|system|bot|algo)")
rule("trading-finance", "Backtesting", r"backtest")
rule("trading-finance", "Paper Trading", r"paper[- ]trading")
rule("trading-finance", "Portfolio Analysis", r"portfolio (analysis|optimi[sz]|management|review)")
rule("trading-finance", "Risk Management", r"risk (management|assessment|analysis)")
rule("trading-finance", "Technical Analysis", r"technical analysis|candlestick|chart pattern|\brsi\b|\bmacd\b|moving average|price action")
rule("trading-finance", "Fundamental Analysis", r"fundamental analysis|earnings report|balance sheet|10-k filing|10-q filing|valuation model")
rule("trading-finance", "Stock Market Research", r"stock (market|analysis|research|portfolio|pick|price|screener|tip|trade|trading|position)|equity research|\bticker\b|market news|\bearnings\b")
rule("trading-finance", "Options & Derivatives", r"\boptions? trading\b|\bderivatives\b|futures market|\bgreeks\b")
rule("trading-finance", "Financial Modeling", r"financial model|dcf|three-statement|forecast(ing)? financial")
rule("trading-finance", "Financial Data Analysis", r"financial (data|statement|report) analysis|sec filing")
rule("trading-finance", "Investing Research", r"\binvest(ing|or|ment) research|\bvaluation\b|market analysis")

# --- Cybersecurity -----------------------------------------------------------
rule("cybersecurity", "Malware Analysis", r"malware|ransomware|virus analysis|reverse engineer(ing)? (a |an )?(malware|binary)")
rule("cybersecurity", "Incident Response", r"incident (response|handling)|dfir|forensic")
rule("cybersecurity", "Security Auditing", r"security (audit|review)|code audit.*security|penetration test|pentest|red team")
rule("cybersecurity", "Vulnerability Assessment", r"vulnerabilit(y|ies)|cve|exploit|nmap|nessie|burp|threat model")
rule("cybersecurity", "Secure Coding", r"secure (coding|development)|owasp|sast|dast|input validation|injection prevention")
rule("cybersecurity", "Network Security", r"network security|firewall|ids/ips|packet capture|tls configur")
rule("cybersecurity", "Defensive Security", r"blue team|defen(s|c)e.*security|siem|soc analyst|hardening")
rule("cybersecurity", "Privacy", r"\bprivacy\b|gdpr|data protection|pii")
rule("cybersecurity", "OSINT", r"\bosint\b|open source intelligence|recon(naissance)? \(?\b")
rule("cybersecurity", "Security Documentation", r"security (policy|documentation|checklist)")

# --- Documents & Office ------------------------------------------------------
rule("documents", "PDF", r"\bpdf\b(?!.*(research|paper))|pdf (form|extract|split|merge|generation)")
rule("documents", "Doc Coauthoring", r"co-authoring documentation|documentation co-author|write documentation, proposals|co-author")
rule("documents", "Internal Communications", r"internal communication|internal comms")
rule("documents", "DOCX", r"\bdocx\b|\bword document|\bdoc files")
rule("documents", "XLSX", r"\bxlsx\b|excel (file|workbook|spreadsheet)|spreadsheet (file|generation)")
rule("documents", "PPTX", r"\bpptx\b|powerpoint|slide deck|presentation (file|deck|generation)")
rule("documents", "Report Generation", r"report (generation|writing|builder)|generate.*report|meeting (notes|minutes)|documentation generator")
rule("documents", "Resume & Career Docs", r"resume|cover letter|cv (writing|review)")

# --- Data & Analytics --------------------------------------------------------
rule("data-analysis", "CSV Analysis", r"\bcsv\b|tsv analysis")
rule("data-analysis", "SQL", r"\bsql\b|\bmysql\b|\bpostgres|\bsqlite\b|query optimization|\bt-sql\b")
rule("data-analysis", "Database Design", r"database (design|schema|modeling)|data model(ing)?|\borm\b|database migration|schema migration|data migration")
rule("data-analysis", "Data Visualization", r"data visuali[sz]|chart|plot|dashboard design|matplotlib|d3\.js|vega")
rule("data-analysis", "Statistics", r"statistic|hypothesis test|regression analysis|probability|bayesian|ab test")
rule("data-analysis", "Business Intelligence", r"business intelligence|\bbi\b|kpi (dashboard|tracking)|analytics reporting")
rule("data-analysis", "Data Science", r"data science|data (analysis|analyst|pipeline|cleaning|wrangling|engineering)|pandas|numpy|jupyter|etl|notebook")
rule("data-analysis", "Excel", r"\bexcel\b")

# --- Android & Mobile --------------------------------------------------------
rule("android", "Termux", r"\btermux\b")
rule("android", "APK Analysis", r"\bapk\b|android reverse|smali")
rule("android", "Android Development", r"android|jetpack compose|android studio|adb|gradle.*android")
rule("android", "Kotlin", r"\bkotlin\b")
rule("android", "Flutter", r"\bflutter\b|dart (language|framework)")
rule("android", "React Native", r"react native|expo\b")
rule("android", "Mobile UI", r"mobile (ui|ux|design|app)")
rule("android", "Mobile Testing", r"mobile (testing|automation)|appium|espresso")

# --- Web Development ---------------------------------------------------------
rule("web-development", "React", r"\breact\b(?! native)|react hooks|jsx\b|react router|react state")
rule("web-development", "Next.js", r"next\.?js\b|\bnextjs\b")
rule("web-development", "Vue", r"\bvue\b|nuxt")
rule("web-development", "Angular", r"\bangular\b")
rule("web-development", "Svelte", r"\bsvelte\b|sveltekit")
rule("web-development", "Tailwind", r"tailwind")
rule("web-development", "CSS", r"\bcss\b|css (layout|grid|flexbox|animation)|sass|less\b")
rule("web-development", "HTML", r"\bhtml\b|semantic html")
rule("web-development", "JavaScript", r"\bjavascript\b|\bjs\b|es6|node\.?js frontend|dom manipulation")
rule("web-development", "Web Performance", r"web (performance|vitals|optimization)|page speed|lighthouse|bundle size")
rule("web-development", "Accessibility", r"accessib|a11y|wcag|screen reader|aria-")
rule("web-development", "SEO", r"\bseo\b|search engine optimization|meta tags|schema markup")
rule("web-development", "Browser Automation", r"browser automation|playwright|puppeteer|selenium|webdriver")
rule("web-development", "Frontend Design", r"frontend (design|development|architecture)|responsive design|web (app|component)|pwa\b")
rule("web-development", "Full-Stack", r"full[- ]stack|webapp testing|web application")

# --- AI / ML -----------------------------------------------------------------
rule("ai-ml", "MCP", r"\bmcp\b|model context protocol|mcp server")
rule("ai-ml", "Prompt Engineering", r"prompt engineer|prompt (design|writing|optimization|template)|system prompt")
rule("ai-ml", "RAG", r"\brag\b|retrieval augmented|vector (database|search|store)|embedding search")
rule("ai-ml", "LLM Development", r"\bllm\b|large language model|claude api|anthropic (api|sdk|docs)|openai api|chatbot (build|development)|gpt-")
rule("ai-ml", "AI Agent Development", r"agent (framework|development|builder|architecture|orchestration)|multi-agent|agentic|ai agent")
rule("ai-ml", "Machine Learning", r"machine learning|\bml model|scikit|sklearn|xgboost|lightgbm|feature engineering")
rule("ai-ml", "Deep Learning", r"deep learning|neural network|pytorch|tensorflow|keras|transformer model|cnn|rnn")
rule("ai-ml", "Model Fine-Tuning", r"fine[- ]tun|lora|qlora|rlhf|sft\b|training (a )?model")
rule("ai-ml", "Model Quantization", r"quantiz|gguf|ggml|model compress|pruning")
rule("ai-ml", "AI Evaluation", r"model (evaluation|benchmark)|eval harness|llm eval|red team.*model|hallucination")
rule("ai-ml", "AI Research", r"ai research|research.*(ai|llm|model)|diffusion model|generative ai|stable diffusion|image generation|text.to.image|generating (images|art)")
rule("ai-ml", "Voice & Speech", r"speech|text.to.speech|voice (assistant|clone)|whisper|tts\b")

# --- Design & Creative -------------------------------------------------------
rule("design", "UI/UX", r"\bui\b|\bux\b|user (interface|experience)|design (intelligence|review|system audit)|interface design")
rule("design", "Design Systems", r"design system|component library|style guide|design token")
rule("design", "Graphic Design", r"graphic design|logo design|poster|illustration|typography|color palette|visual identity")
rule("design", "Branding", r"brand(ing| guidelines| identity| strategy)|brand voice")
rule("design", "Image Generation Workflows", r"image (generation|editing) workflow|midjourney|dall-e|generative art|prompt.*image")
rule("design", "Video Editing Workflows", r"video (editing|production|shot|script)|film|cinemat")
rule("design", "Animation", r"animation|motion (design|graphics)|lottie|after effects")
rule("design", "3D Design", r"\b3d\b|blender|three\.?js|3d model")
rule("design", "Canvas & Generative Design", r"canvas design|generative design|art direction")

# --- Research & Productivity -------------------------------------------------
rule("research", "Deep Research", r"deep research|comprehensive research|research (workflow|plan|pipeline|agent)|in-depth research")
rule("research", "Fact Checking", r"fact.?check|misinformation|claim verification")
rule("research", "Source Verification", r"source verification|citation (check|verification|verifier)")
rule("research", "Academic Research", r"academic (research|paper|writing)|literature review|arxiv|peer review|systematic review|dissertation|thesis")
rule("research", "PDF Analysis", r"pdf (analysis|research)|research paper|scientific paper")
rule("research", "Web Research", r"web research|online research|internet research|competitive (research|intelligence)|market research")
rule("research", "Document Summarization", r"summariz|tl;dr|digest generation")
rule("research", "Knowledge Management", r"knowledge (management|base|graph)|second brain|zettelkasten|note taking|obsidian|pkm\b")

# --- Game Development --------------------------------------------------------
rule("game-development", "Game Development", r"\bgame\b|unity\b|unreal|godot|pygame|game (design|dev|mechanics|physics)|gamedev")

# --- Science -----------------------------------------------------------------
rule("science", "Bioinformatics", r"bioinformatic|genomic|genome|dna|rna|protein (structure|folding)|alphafold|sequence alignment|single.cell|scrna")
rule("science", "Chemistry", r"chemistr|molecular|rdkit|compound|reaction (prediction|design)")
rule("science", "Physics", r"physic|quantum (comput|mechan)")
rule("science", "Neuroscience", r"neurosci|brain (imaging|data)|fmri|eeg")
rule("science", "Astronomy", r"astronom|astrophysic|telescope data")
rule("science", "Scientific Analysis", r"scientific (analysis|computing|research|workflow)|lab (notebook|protocol|work)|bioinform|biolog|medical|clinical|epidemiolog|ecolog")

# --- Marketing ---------------------------------------------------------------
rule("marketing", "Content Marketing", r"content (marketing|strategy|calendar|creation)|blog (post|writing) strategy|\bmarketing\b|local service page")
rule("marketing", "Conversion Optimization", r"conversion (rate|optimi)|\bcro\b|signup flow|landing page optimi|funnel")
rule("marketing", "Social Media", r"social media|(twitter|linkedin|instagram|tiktok|youtube) (marketing|growth|content|algorithm|post)")
rule("marketing", "SEO Content", r"seo (content|strategy|audit|writing)|keyword research")
rule("marketing", "Email Marketing", r"email (marketing|campaign|newsletter|sequence)")
rule("marketing", "Ad Campaigns", r"ad (campaign|copy|creative)|google ads|meta ads|advertis")
rule("marketing", "Growth", r"growth (hacking|marketing|strategy)|viral loop|funnel optimization")
rule("marketing", "Market Analysis", r"competitor (analysis|research)|market (analysis|sizing|research)|positioning")
rule("marketing", "Copywriting", r"copywriting|landing page copy|ad text|persuasive writing")
rule("marketing", "Brand Marketing", r"brand (awareness|marketing|story)")

# --- Business ----------------------------------------------------------------
rule("business", "Business Analysis", r"business (analysis|analyst|case|plan|model)|swot|bmc\b|business requirements")
rule("business", "Pitch & Fundraising", r"pitch deck|investor (update|pitch)|fundrais|vc (pitch|funding)|term sheet")
rule("business", "Product Management", r"product (management|manager|requirements|spec|roadmap|discovery)|user stor(y|ies)|prd\b|prioritization framework")
rule("business", "Project Management", r"project (management|plan|scoping)|gantt|sprint (plan|retro)|agile (ceremony|workflow)|kanban|risk register")
rule("business", "Sales", r"sales (call|email|pitch|playbook|strategy)|cold (email|outreach)|lead (generation|qualification)|crm\b")
rule("business", "Customer Success", r"customer (success|support|feedback|journey)|churn|nps\b|support ticket")
rule("business", "Operations", r"business operations|process (optimization|documention|improvement)|sop\b|workflow design")
rule("business", "Legal & Compliance", r"legal (document|review|contract)|compliance (check|review)|terms of service|privacy policy draft|nda\b")
rule("business", "HR & Recruiting", r"recruit|hiring|interview (question|loop)|job description|onboarding plan|performance review")
rule("business", "Strategy", r"business strategy|strategic (plan|analysis)|competitive strategy|okr\b|go.to.market|gtm\b")

# --- Writing & Communication -------------------------------------------------
rule("writing", "Translation", r"translat|localiz|i18n|multilingual")
rule("writing", "Humanizing & Tone", r"humaniz|de-?ai.?ify|tone (adjust|of voice)|make.*sound human|rewrite.*tone")
rule("writing", "Technical Writing", r"technical writing|api (documentation|docs)|developer documentation|readme (writing|generator)|changelog")
rule("writing", "Editing & Proofreading", r"proofread|edit(ing)? (text|document|essay)|grammar (check|fix)|line edit")
rule("writing", "Creative Writing", r"creative writing|story (writing|telling)|fiction|novel|screenplay|poem|character (voice|creation)")
rule("writing", "Blogging & Newsletters", r"blog (post|article|writing)|newsletter (writing|draft)|article (writing|draft)")
rule("writing", "Communication", r"email (draft|writing|reply)|slack message|professional communication|difficult conversation|meeting (request|agenda)|announcement")
rule("writing", "General Writing", r"writing (assistant|coach|improvement)|write (a |an )?(post|essay|article|draft)|text improvement")

# --- Automation & DevOps -----------------------------------------------------
rule("automation", "CI/CD", r"ci/?cd|github actions|gitlab ci|jenkins|continuous (integration|deployment)|deployment pipeline")
rule("automation", "GitHub Automation", r"github (automation|workflow|action|api)|pull request (automation|review bot)|issue (triage|automation)|release automation|semantic version")
rule("automation", "Workflow Automation", r"workflow automation|n8n|zapier|make\.com|automation (workflow|pipeline|script)|schedule.*task|cron")
rule("automation", "API Integrations", r"api (integration|client|wrapper)|webhook|rest api (integration|design|testing)|graphql (api|integration)|connect.*api")
rule("automation", "Browser Automation", r"browser (automation|agent|extension)|web scraping|scraper|headless browser|playwright script")
rule("automation", "File Management", r"file (management|organization|organizer)|folder (structure|organization)|batch (rename|process)|file cleanup")
rule("automation", "Cloud Automation", r"cloud (automation|resource|provision)|infrastructure as code")
rule("automation", "Task Automation", r"automate (the |a |an )?|automation of|repeat(itive)? task")

# --- DevOps & Cloud ----------------------------------------------------------
rule("devops-cloud", "Containers", r"docker|container(image|ization)?|kubernetes|\bk8s\b|helm chart|podman")
rule("devops-cloud", "Infrastructure as Code", r"terraform|pulumi|ansible|cloudformation|bicep")
rule("devops-cloud", "AWS", r"\baws\b|amazon web services|lambda function|s3 bucket|dynamodb")
rule("devops-cloud", "GCP", r"\bgcp\b|google cloud|bigquery")
rule("devops-cloud", "Azure", r"\bazure\b")
rule("devops-cloud", "SRE & Monitoring", r"sre\b|site reliability|monitoring (setup|stack)|observability|prometheus|grafana|alerting|on-call")
rule("devops-cloud", "Cloud Architecture", r"cloud (architecture|migration|native|cost)|serverless|edge (computing|deploy)")
rule("devops-cloud", "Linux & Sysadmin", r"linux (admin|server|command)|system admin|bash script|shell script|ssh (config|setup)|nginx|systemd")

# --- Coding (generic software development, checked after more specific cats) --
rule("coding", "Debugging", r"debug(ging)?|troubleshoot(ing)?|root cause (analysis|investigation)|diagnos(e|ing) (bugs|issues)")
rule("coding", "Code Review", r"code review|pr review|reviewing (code|pull requests)|review checklist")
rule("coding", "Testing", r"\btest(ing)? (strategy|framework|automation|plan)|unit test|integration test|e2e test|tdd\b|pytest|jest|vitest|test-driven")
rule("coding", "Refactoring", r"refactor(ing)?|clean code|code (quality|smell|improvement)|technical debt|legacy (code|refactor)")
rule("coding", "Software Architecture", r"software (architecture|design patterns)|system design|microservices|domain.driven|ddd\b|architecture (decision|review)|monolith")
rule("coding", "API Development", r"api (development|design|endpoint|first)|fastapi|flask api|express\.js|openapi|swagger|grpc\b|endpoint design")
rule("coding", "Backend Development", r"backend (development|engineering|service)|server.side|django|rails|laravel|spring boot|node backend")
rule("coding", "Python", r"\bpython\b|pandas|django|flask|fastapi|pydantic|pythonic")
rule("coding", "JavaScript", r"\bjavascript\b|typescript|node\.?js|\bjs\b|esm\b")
rule("coding", "TypeScript", r"typescript|ts config|type.safe javascript")
rule("coding", "Rust", r"\brust\b|cargo (build|toml)|rustacean")
rule("coding", "Go", r"\bgo(lang)?\b|golang")
rule("coding", "Java", r"\bjava\b|maven|gradle (build|project)|jvm (language|tuning)|spring\b")
rule("coding", "C++", r"\bc\+\+\b|cpp\b|cmake")
rule("coding", "C#", r"\bc#\b|\.net\b|dotnet")
rule("coding", "PHP", r"\bphp\b|laravel|symfony")
rule("coding", "Ruby", r"\bruby\b|\brails\b|gemfile")
rule("coding", "Swift/iOS", r"\bswift\b|\bios\b development|xcode|swiftui")
rule("coding", "Version Control", r"\bgit\b(?!hub)|git (workflow|rebase|history|commit)|version control|conventional commits")
rule("coding", "Performance", r"performance (optimization|tuning|engineering)|latency (optimization|reduction)|profiling|memory optimization|algorithm optimization")
rule("coding", "Concurrency", r"concurrency|parallel(ism|ize)?|async(ion)? (programming|patterns)|thread safe|goroutine")
rule("coding", "Databases & ORM", r"redis\b|mongodb|elasticsearch|sqlite|database (performance|indexing|optimization)|orm query")
rule("coding", "Error Handling", r"error (handling|handling pattern)|exception (handling|strategy)|resilien|retry (logic|pattern)")
rule("coding", "Engineering Process", r"engineering (process|workflow|best practice)|development (workflow|process)|pair programming|mob programming|estimation")
rule("coding", "Documentation", r"code (comment|documentation)|docstring|inline documentation")
rule("coding", "CLI Tools", r"cli (tool|application|design)|command.?line (tool|interface|app)|argument parsing")
rule("coding", "General Programming", r"programming|coding (standard|practice|guideline)|software (engineering|craft|development)|developer (workflow|productivity)|codebase")

# --- Education ---------------------------------------------------------------
rule("education", "Learning & Teaching", r"education|teaching|tutor|lesson plan|curriculum|course (design|creation)|study (plan|guide|technique)|learning (path|plan)|explain.*simply|learning")

# --- Extra rules from first-pass "other" sample ------------------------------
rule("devops-cloud", "Deployment", r"\bdeploy|vercel|netlify|heroku|cloudflare (pages|workers)|deployment (guide|workflow)")
rule("devops-cloud", "Cost Optimization", r"cost optimi[sz]|finops|cloud cost")
rule("cybersecurity", "Secrets & Encryption", r"encrypt|sops\b|secrets management|vault|key rotation|credential storage")
rule("cybersecurity", "Bug Bounty Reporting", r"bug bounty|bugcrowd|hackerone|vulnerability (report|disclosure)")
rule("automation", "Logging & Context", r"diary|logger|context.preserv|session (log|record)|worklog")
rule("ai-ml", "Prompt Testing & Evals", r"prompt (regression|testing|evaluation|eval)|eval (set|harness|suite)|prompt quality")
rule("ai-ml", "Skill Engineering", r"skill[- ](improver|creator|reviewer|engineering|smith)|improve a .{0,20}skill|writing skills")
rule("writing", "AI Text Cleanup", r"unslop|ai.slop|strip ai (writing|patterns)|text humaniz")
rule("business", "Accounting & Bookkeeping", r"accounting|bookkeep|ledger|closing (statement|register)|reconciliation|\btds\b|\bgst\b|invoice (processing|organiz)")
rule("coding", "Error Diagnosis", r"error (resolution|resolver|diagnosis)|diagnos.*error|first.principle.*error")
rule("automation", "Screenshot & Capture", r"screenshot|screen capture|screen record")
rule("coding", "Patch & Diff", r"implement.patch|patch (application|workflow)|apply diff")

# --- Fallbacks for everything else -------------------------------------------
rule("research", "Productivity", r"productivity|time management|focus (technique|session)|pomodoro|daily (planner|routine)|habit track|morning routine")
rule("research", "Career Development", r"career (development|advice|growth)|job search|interview preparation|networking tips|personal brand(ing)?|salary negotiation|performance review prep")
rule("research", "Life & Personal", r"personal (finance|assistant|development)|fitness|health|cooking|recipe|travel|home (organization|improvement)|shopping|relationship|parenting|self.?care|mental health|life (coach|advice)")
rule("other", "", r"")

SOURCE_BIAS = {
    "K-Dense-AI/scientific-agent-skills": "science",
    "coreyhaines31/marketingskills": "marketing",
    "JimLiu/baoyu-skills": "writing",
    "blader/humanizer": "writing",
    "titanwings/distilly": "research",
    "alchaincyf/huashu-design": "design",
    "alchaincyf/nuwa-skill": "design",
    "op7418/guizang-ppt-skill": "documents",
    "Vincentwei1021/video-shotcraft": "design",
    "wheresryan22/anatomy": "coding",
    "Leonxlnx/taste-skill": "design",
    "nidhinjs/prompt-master": "ai-ml",
    "OthmanAdi/planning-with-files": "research",
    "elementalsouls/Claude-BugHunter": "coding",
    "mvanhorn/last30days-skill": "data-analysis",
    "latent-spaces/brag": "writing",
    "cloudflare/security-audit-skill": "cybersecurity",
    "nextlevelbuilder/ui-ux-pro-max-skill": "design",
    "obsidianmd/obsidian-skills": "research",
    "mattpocock/skills": "coding",
    "addyosmani/agent-skills": "coding",
    "github/awesome-copilot": "coding",
    "sickn33/agentic-awesome-skills": "coding",
}

CATEGORY_DIRS = {
    "coding": "coding", "web-development": "web-development", "android": "android",
    "ai-ml": "ai-ml", "trading-finance": "trading-finance", "cybersecurity": "cybersecurity",
    "data-analysis": "data-analysis", "research": "research", "automation": "automation",
    "design": "design", "documents": "documents", "devops-cloud": "devops-cloud",
    "game-development": "game-development", "science": "science", "marketing": "marketing",
    "business": "business", "writing": "writing", "education": "education", "other": "other",
}


# Upstream category mapping for repos that ship their own taxonomy
# (currently sickn33/agentic-awesome-skills via skills_index.json)
UPSTREAM_CATEGORY_MAP = {
    "development": "coding", "code": "coding", "code-quality": "coding",
    "backend": "coding", "engineering": "coding", "architecture": "coding",
    "testing": "coding", "super-code": "coding",
    "security": "cybersecurity", "devops": "devops-cloud", "cloud": "devops-cloud",
    "reliability": "devops-cloud",
    "marketing": "marketing", "seo": "marketing",
    "business": "business", "project-management": "business", "finance": "trading-finance",
    "ai-ml": "ai-ml", "ai-agents": "ai-ml", "agent-orchestration": "ai-ml", "mcp": "ai-ml",
    "content": "writing", "design": "design", "design-it": "design", "media": "design",
    "workflow": "automation", "automation": "automation", "api-integration": "automation",
    "granular-workflow-bundle": "automation",
    "data": "data-analysis", "database": "data-analysis",
    "web-development": "web-development", "frontend": "web-development",
    "productivity": "research", "research": "research",
    "mobile": "android", "game-development": "game-development",
    "meta": "other", "health": "other", "uncategorized": "other",
}


def load_sickn33_categories(clone_root: str = ".cache/upstream") -> dict:
    """path -> category from the repo's own skills_index.json, if present.

    Both the canonical path ("skills/<name>") and the bare skill name are
    indexed, because deduplication may keep a mirrored copy under plugins/.
    """
    idx = Path(clone_root) / "sickn33_agentic-awesome-skills" / "skills_index.json"
    mapping = {}
    if idx.exists():
        try:
            for entry in json.loads(idx.read_text(encoding="utf-8")):
                if not isinstance(entry, dict) or not entry.get("category"):
                    continue
                cat = entry["category"]
                if entry.get("path"):
                    mapping[entry["path"]] = cat
                if entry.get("name"):
                    mapping[f"name:{entry['name']}"] = cat
        except Exception:
            pass
    return mapping


def classify_text(name: str, description: str, source_repo: str, upstream_category: str = "") -> tuple[str, str, str]:
    text = f"{name} :: {description}"
    for category, subcategory, pat in RULES:
        if pat.search(text):
            return category, subcategory, "keywords"
    if upstream_category:
        mapped = UPSTREAM_CATEGORY_MAP.get(upstream_category)
        if mapped:
            return mapped, "", f"upstream-category:{upstream_category}"
    bias = SOURCE_BIAS.get(source_repo)
    if bias:
        return bias, "", "source-bias"
    return "other", "", "fallback"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=".cache/build/raw_skills.json")
    ap.add_argument("--output", default=".cache/build/classified.json")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as fh:
        data = json.load(fh)

    counts: dict[str, int] = {}
    sickn33_cats = load_sickn33_categories()
    for rec in data["skills"]:
        up_cat = rec.get("upstream_category", "")
        if not up_cat:
            sp = rec.get("source_path", "")
            up_cat = sickn33_cats.get(sp, "") or sickn33_cats.get(f"name:{Path(sp).name}", "")
        risk = rec.get("upstream_risk", "")
        if risk:
            rec["upstream_risk"] = risk
        cat, sub, how = classify_text(rec["name"], rec.get("description", ""), rec["source_repo"], up_cat)
        rec["category"] = cat
        rec["subcategory"] = sub
        rec["classification"] = how
        rec["category_dir"] = CATEGORY_DIRS.get(cat, "other")
        counts[cat] = counts.get(cat, 0) + 1

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
    print("classified:", len(data["skills"]), "records")
    for cat, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {cat}: {n}")


if __name__ == "__main__":
    main()
