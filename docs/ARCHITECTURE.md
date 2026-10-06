# GARUDA — Architecture Blueprint v2 (Source of Truth)

> **Detect. Verify. Protect.**
> AI-powered multimodal scam, phishing and suspicious-content detection platform for Indian users.
> Core principle: **DETECT → EXPLAIN → VERIFY → PROTECT → REPORT**

v2 changes from v1: **Supabase is the only database** (no local PostgreSQL, no Docker database, no SQLite), legitimacy signals in scoring, category blocklists (betting / adult / phishing / malware), QR + UPI analyzer, email verification, team workflow, 7-day plan.

---

## 0. Rules for every AI agent and teammate working in this repo

1. Follow this document. Do not redesign or replace the architecture.
2. **Supabase (PostgreSQL) only.** Never create or fall back to SQLite. If `DATABASE_URL` fails, crash with a clear error.
3. **Schema changes only through Alembic migrations**, and only the backend lead creates migrations. No separate `.sql` schema files.
4. **Tests never touch the dev database.** Tests use the separate Supabase test project via `TEST_DATABASE_URL`.
5. **Supabase is only the database.** No Supabase Auth, no Supabase JS client, no Supabase keys anywhere in the frontend.
6. **No mock or hardcoded results.** Every result shown comes from the API. Temporary mocks must be marked `// MOCK` and removed before merging.
7. **Explanations are built only from what was detected in THIS input.** No fixed summary sentences.
8. **Evidence snippets are cut on word boundaries.**
9. **Every score is explainable on screen:** all indicators and all legitimacy signals that changed it are shown.
10. **Honest wording:** "Threats Detected" (not "Blocked"), "Likely Safe" (not "Verified Safe"), never claim government verification or that a government authority received a report.
11. **Invalid input is never scored as safe** → validation error or "Unable to Verify".
12. **Work in small chunks.** After each chunk: run, test, fix, then stop and wait. Commit on your own branch when tests pass; never push directly to `main`.
13. **Explain each chunk:** WHAT was built, WHY it exists, HOW it works, HOW it connects to the rest of GARUDA.
14. An LLM (if ever added) never decides the risk score.

---

## 1. Overview — the five sectors

| # | Sector | What it does |
|---|---|---|
| 1 | Detection & Analysis | Message, URL, QR/UPI (and later image/OCR) analyzers with risk score, explanation and safe verification steps |
| 2 | AI & Threat Intelligence | Rule engine, legitimacy signals, URL heuristics, category blocklists, scoring, explanations (ML model later) |
| 3 | Dashboard & History | Personal stats, charts, scan history, full scan detail |
| 4 | Reporting | Report Center with evidence, `GAR-2026-XXXXXX` reference IDs, status tracking, official external channels |
| 5 | Threat Database & Admin | Shared threat records and blocklists now; admin dashboard and 22-lakh ingestion pipeline designed for Phase 2 |

Languages now: English, Hindi, Telugu, Romanized Telugu, Hinglish. Designed for all 22 scheduled languages (Section 8.9).

---

## 2. System Architecture

```
Browser
  │
  ▼
Next.js frontend (App Router, TypeScript, Tailwind)        localhost:3000
  │  HTTPS JSON  (only NEXT_PUBLIC_API_URL is public)
  ▼
FastAPI backend: routes (validation, auth, rate limit)     localhost:8000
  │
  ▼
Services: scan · report · dashboard · auth · audit · email
  │
  ▼
Detection Engine (pure Python package, NO FastAPI imports)
  │
  ▼
Supabase PostgreSQL (dev project)  ◄── SQLAlchemy + Alembic, SSL, Session pooler
Supabase PostgreSQL (test project) ◄── pytest only

Phase 2 (designed, not built): Redis queue + Celery workers → SAME engine → Supabase → OpenSearch
```

Key decisions:
- The engine is framework-free: `engine.analyze(input) -> AnalysisResult`. The API (and later Celery workers) call the same function.
- Single scans are synchronous (< 3 s target).
- Suspicious URLs are never opened or fetched. URL analysis is static; blocklist lookups are local database queries.
- Unavailable intelligence is reported as unavailable, never as "clean".
- The backend connects to Supabase as the database owner. Row Level Security is enabled on every table with **no policies**, so Supabase's public Data API cannot read anything.

---

## 3. Supabase Setup (do this before Chunk 1)

### 3.1 Projects
Use **two** free Supabase projects in the same organization:

| Project | Purpose | Who connects |
|---|---|---|
| `garuda-dev` | Real app data (users, scans, reports, blocklists) | Every teammate's backend |
| `garuda-test` | Automated tests only; data is wiped by tests | pytest only |

The free plan allows 2 active projects. If an old project (for example the earlier "Garuda" in Tokyo) is in the way, delete it: Project Settings → General → Delete project.

Create each project:
1. supabase.com → your organization → **New project**
2. Name `garuda-dev` (then `garuda-test`)
3. Database password: **letters and numbers only** (symbols like @ # / break the URL). Save it in a password manager.
4. Region: **South Asia (Mumbai)**
5. Plan: Free → Create

### 3.2 Connection string
1. Open the project → green **Connect** button → **Session pooler** (not "Direct connection"; direct needs IPv6 and often fails on Indian home networks).
2. Copy: `postgresql://postgres.<ref>:[YOUR-PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:5432/postgres`
3. Replace `[YOUR-PASSWORD]` (no brackets). The backend converts the scheme to `postgresql+psycopg://` and adds `sslmode=require`.
4. Put it in `backend/.env` as `DATABASE_URL` (dev) and `TEST_DATABASE_URL` (test).

### 3.3 Rules
- `backend/.env` is never committed, never pasted into chats or screenshots, never put in the frontend.
- Teammates receive connection strings privately (direct message), not through GitHub.
- View data in Supabase → **Table Editor**. Run SQL in **SQL Editor** (read-only checks; schema changes go through Alembic).
- Free projects pause after about a week of no activity. Open the dashboard and click **Restore** if that happens. Check the day before the demo.
- Demo needs internet: keep a phone hotspot ready.

---

## 4. Folder Structure

```
Garuda/                          (outside OneDrive, e.g. C:\Projects\Garuda)
├── docs/
│   ├── ARCHITECTURE.md          ← this file
│   └── BUILD_PLAN.md            ← chunk prompts + team plan
├── README.md
├── docker-compose.yml           # optional, Phase 2 (Redis/MinIO); NOT used for the database
├── .gitignore                   # backend/.env, .venv, __pycache__, node_modules, .next, *.db
├── backend/
│   ├── .env / .env.example
│   ├── requirements.txt
│   ├── alembic/ , alembic.ini
│   ├── app/
│   │   ├── main.py
│   │   ├── core/        # config, security, rate_limit, errors, logging
│   │   ├── db/          # session (engine with SSL, pool_pre_ping)
│   │   ├── models/      # SQLAlchemy
│   │   ├── schemas/     # Pydantic
│   │   ├── api/routes/  # auth, analyze, scans, reports, dashboard, directory
│   │   ├── services/    # scan, report, dashboard, audit, email
│   │   └── engine/
│   │       ├── orchestrator.py
│   │       ├── normalize/    # NFKC, zero-width strip, homoglyphs, leetspeak, language detect
│   │       ├── extractors/   # urls.py, qr.py, upi.py (ocr.py in Phase 2)
│   │       ├── analyzers/    # text_rules.py, legitimacy.py, url_analyzer.py, qr_analyzer.py
│   │       ├── lexicons/     # YAML rule packs per category × language
│   │       ├── intel/        # blocklist lookup (threat_intelligence table)
│   │       ├── scoring/      # signals.py, scorer.py, bands.py
│   │       └── explain/      # explainer.py, templates/
│   ├── scripts/         # load_blocklists.py, create_admin.py
│   └── tests/           # unit/, integration/, golden/, security/
└── frontend/
    ├── .env.local       # only NEXT_PUBLIC_API_URL
    └── src/
        ├── app/(public)/   # /, /login, /register, /verify-email, /privacy
        ├── app/(app)/      # dashboard, analyzers, history, scan/[id], reports, profile
        ├── components/{ui,layout,analysis,charts,landing,brand}/
        ├── lib/            # api-client.ts, auth.ts, format.ts
        └── types/
```

---

## 5. Database (Supabase PostgreSQL, UUID PKs, every table has created_at / updated_at)

**Accounts**
- **users**: id, email (citext, unique), password_hash, full_name, role (user|admin), is_active, email_verified_at, last_login_at
- **sessions**: id, user_id→users, refresh_token_hash (unique), ip, user_agent, expires_at, revoked_at
- **admin_users**: id, user_id→users (unique), admin_role (analyst|superadmin), permissions jsonb
- **email_verification_codes**: id, user_id→users, code_hash, expires_at, attempts, used_at

**Detection**
- **scans**: id, user_id→users, scan_type (message|url|qr|image), status (done|failed), input_sha256, persisted_content
- **messages**: id, scan_id→scans (unique), content, detected_language
- **images**: id, scan_id→scans, mime_type, size_bytes, sha256, ocr_text, ocr_confidence (images themselves are never stored)
- **qr_codes**: id, scan_id→scans, image_id→images (nullable), payload, payload_type (url|upi|text|wifi|other), upi_payee, upi_name, upi_amount
- **urls**: id, scan_id→scans, raw_url, normalized_url, registered_domain, source (direct|message|qr|ocr)
- **analysis_results**: id, scan_id→scans (unique), risk_score, risk_level, confidence, verification_status, category, summary, legitimacy_signals jsonb, recommendations jsonb, verify_steps jsonb, intel_status jsonb, engine_version
- **threat_indicators**: id, analysis_id→analysis_results, code, label, severity, weight, evidence

**Threat intelligence**
- **threats**: id, threat_type (domain|url|qr_payload|phone|upi), value_hash (unique), value, risk_level, occurrence_count, first_seen, last_seen
- **scan_threats**: (scan_id, threat_id) composite PK
- **threat_intelligence**: id, threat_id→threats (nullable), source, indicator_type, indicator_value, indicator_hash, verdict (phishing|malware|gambling|adult|…), fetched_at, expires_at

**Reporting**
- **reports**: id, reference_code (unique, `GAR-{year}-{seq:06d}` from a Postgres sequence), user_id, scan_id (nullable), category, title, description, status (submitted|under_review|needs_info|closed), incident_date
- **report_evidence**: id, report_id, evidence_type (message|url|qr|analysis|text), text_value, scan_id
- **report_status_history**: id, report_id, from_status, to_status, note, changed_by→users

**Platform**
- **notifications**: id, user_id, type, title, body, read_at
- **audit_logs**: id, actor_user_id, action, entity_type, entity_id, ip, metadata jsonb

**Indexes:** scans(user_id, created_at DESC); analysis_results(risk_level), (category); urls(registered_domain); threats unique(value_hash); threat_intelligence unique(source, indicator_hash) and (indicator_type, indicator_hash); reports(user_id, created_at DESC), (status); notifications partial (user_id) WHERE read_at IS NULL; audit_logs BRIN(created_at).

**Security migration:** `ALTER TABLE … ENABLE ROW LEVEL SECURITY` on every table, no policies.

---

## 6. API (FastAPI)

Error shape: `{ "error": { "code": "...", "message": "...", "details": {...} } }` — validation errors list each field.
Auth: access JWT 15 min (kept in memory by the frontend) + refresh token in httpOnly, SameSite=Lax cookie (Secure in production), rotated on refresh, stored hashed in `sessions`. Every resource read checks ownership (no IDOR).

| Method | Path | Notes |
|---|---|---|
| GET | /api/health | Includes a database check |
| POST | /api/auth/register | email, password ≥ 8, full_name ≥ 2 |
| POST | /api/auth/verify-email | email, code; 5 attempts per code |
| POST | /api/auth/resend-code | 1 per minute per email |
| POST | /api/auth/login | Same error for unknown email and wrong password; EMAIL_NOT_VERIFIED when required |
| POST | /api/auth/refresh · /api/auth/logout | |
| GET | /api/auth/me | |
| POST | /api/analyze/message | {text 1–5000, save} |
| POST | /api/analyze/url | {url, save} |
| POST | /api/analyze/qr | multipart image (≤ 5 MB, png/jpg/webp, magic-byte check) or {payload}; save flag |
| GET | /api/scans | own scans, cursor pagination, filters type / risk_level |
| GET / DELETE | /api/scans/{id} | 404 for other users' scans |
| GET | /api/dashboard/stats | own data only |
| POST / GET | /api/reports · /api/reports/{id} | |
| GET | /api/directory/reporting-channels | external links only |

Analysis response (all analyzers):
```json
{
  "scan_id": "uuid", "scan_type": "message",
  "risk": { "score": 91, "level": "high", "label": "High Risk" },
  "confidence": 0.89,
  "verification_status": "unverified",
  "category": { "code": "qr_reward_scam", "label": "Potential QR / Reward Scam" },
  "summary": "Built only from the signals below.",
  "indicators": [{ "code": "FIN_UNEXPECTED_REWARD", "label": "Unexpected monetary reward", "severity": "high", "weight": 0.35, "evidence": "You won ₹500" }],
  "legitimacy_signals": [{ "code": "LEGIT_BANK_ADVISORY", "label": "Contains standard bank safety advice", "weight": 0.5, "evidence": "Do NOT share OTP" }],
  "recommendations": ["Do not scan the QR code", "Do not pay", "Do not share OTP or passwords"],
  "verify_steps": ["Type the organization's official website yourself", "…"],
  "extracted": { "urls": [], "qr": null, "upi": null, "language": "en" },
  "intel": [{ "source": "garuda_blocklists", "status": "not_found" }],
  "engine_version": "2.0.0"
}
```

Reporting directory: National Cyber Crime Reporting Portal (cybercrime.gov.in) and helpline 1930, shown as external links labeled "GARUDA does not submit to this channel on your behalf." Report status always says "Submitted to GARUDA".

---

## 7. Frontend

Public: `/`, `/login`, `/register`, `/verify-email`, `/privacy`
App (login required): `/dashboard`, `/message-analyzer`, `/url-analyzer`, `/qr-analyzer`, `/history`, `/scan/[id]`, `/reports`, `/reports/new`, `/reports/[id]`, `/profile`
Phase 2: `/image-analyzer`, `/admin/*`

- Top marketing nav only on the landing page. App pages: sidebar + slim top bar with page title and profile avatar (initial, dropdown: name, email, Profile, Logout).
- Route guards: app pages → /login when logged out; /login and /register → /dashboard when logged in.
- Forms: zod + react-hook-form, field-level errors, show/hide password eye icon.
- Brand: an original minimal GARUDA eagle mark (SVG component) used in sidebar, auth pages and landing.
- Tokens: bg `#070B14`, surface `#0D1424`, elevated `#121B2F`, border `rgba(148,163,184,0.12)`, primary `#3B82F6`, accent cyan `#22D3EE` (sparingly). Risk: Likely Safe `#34D399`, Suspicious `#FBBF24`, Medium `#F59E0B`, High `#F97316`, Critical `#EF4444`, Unable to Verify `#94A3B8`. Fonts Inter + JetBrains Mono. Motion 150–250 ms, respects reduced motion. No neon, no Matrix effects, no constant glow.
- Every page has loading, empty and error states; responsive at 375 / 768 / 1280 px.

---

## 8. Detection Engine

### 8.1 Pipeline
```
Input → Validate → Normalize → Extract (URLs · QR · UPI) → Rule engine + Legitimacy signals + URL analyzer + Blocklist lookup → Scorer → Category → Explainer → AnalysisResult
```

### 8.2 Normalize
NFKC, remove zero-width characters, homoglyph and leetspeak folding (`0TP` → `OTP`, `sh@re` → `share`), lowercase copy for matching, language/script detection.

### 8.3 Rule engine (risk indicators)
- YAML packs per category × language: reward/lottery, KYC/bank block, credential/OTP/PIN request, payment/fee demand, fake job/task, investment, loan, delivery, utility disconnection, government/police impersonation ("digital arrest"), family impersonation, UPI collect/PIN-to-receive, urgency.
- **Match phrases in context, not single words.** "OTP" alone is not a threat; "share your OTP" is. "Valid for 10 mins" is expiry information, not urgency. Urgency means pressure: "will be blocked today", "act now", "or face arrest".
- Each rule → indicator code, label, severity, weight, evidence.

### 8.4 Legitimacy signals
Patterns that genuine messages carry: bank "never share / bank never calls" advisories, standard OTP/transaction formats with masked accounts (XX1234), official sign-offs, "via the official app/website" guidance. Each has a weight and is shown in the result.

### 8.5 Scoring
```
R = 1 − Π(1 − wᵢ)          over risk indicators (noisy-OR)
L = 1 − Π(1 − lⱼ)          over legitimacy signals, capped at 0.8
score = round(100 × R × (1 − L))
```
**Anti-gaming rule:** if any high-severity indicator is present (credential/PIN request, payment demand, lookalike or blocklisted URL), L is ignored (scammers copy "do not share" text).
Example: ₹500 QR reward message → reward 0.35, urgency 0.25, QR CTA 0.30, financial action 0.30, unverifiable destination 0.20 → R ≈ 0.81 → **81 High**, no legitimacy discount.

**Bands:** 0–24 Likely Safe · 25–44 Suspicious · 45–64 Medium · 65–100 High · **Critical** only if ≥ 85 AND a blocklist (phishing/malware) hit or credential/payment request + impersonation · **Unable to Verify** when input is unusable.

**Confidence** (separate from risk): agreement between signals, input length/quality, language support level (lower for unsupported languages).
**Verification status** (separate): `matched_<list>` when a blocklist matched (names the list), otherwise `unverified`, or `unable_to_verify`. Never "verified safe".

### 8.6 URL analyzer (static, never fetches)
Validation and normalization (add https://; reject spaces / no domain) → IP-literal host, punycode/IDN, `@` in URL, subdomain depth, risky TLDs, shorteners, brand lookalikes (edit distance vs Indian banks, wallets, couriers, government domains), suspicious parameters (pin, otp, password) → blocklist lookup on the registered domain (`indian.1xbet.com` → `1xbet.com`).

### 8.7 Category blocklists
`scripts/load_blocklists.py` downloads open lists (StevenBlack hosts extensions: gambling, porn; URLhaus: malware/phishing) and batch-loads them into `threat_intelligence`; re-runnable without duplicates. Plus `garuda_curated` Indian betting list (1xbet, parimatch, betway, stake, lotus365, mahadev).

| Verdict | Risk | Category label | User message |
|---|---|---|---|
| phishing / malware | High | Phishing / Malicious Website | Listed as a phishing/malware domain in <source> |
| gambling | High | Illegal Betting / Gambling Platform | Online real-money betting is illegal in India; no legal protection for money deposited |
| adult | Medium | Restricted Content (Adult) | Adult website; often carries malicious ads, fake virus pop-ups and subscription traps |
| not found | — | — | "Not found in GARUDA's reputation lists" (not "safe") |

### 8.8 QR + UPI analyzer
Decode with OpenCV QRCodeDetector (pyzbar fallback) → classify payload: url / upi / text / wifi / other → for `upi://pay?pa=…&pn=…&am=…`: extract payee VPA, name, amount; flag amount pre-filled with reward text, payee name mismatch with claimed brand, unknown/personal handles claiming to be a business, and "scan to receive money" (receiving money never needs scanning or a PIN) → URL payloads go through the URL analyzer. Never open the decoded destination; show a safe preview only.

### 8.9 Languages
Now: rule packs for English, Hindi (Devanagari), Telugu (script), Romanized Telugu, Hinglish. Language-independent signals (URLs, UPI IDs, phone numbers, ₹ amounts, OTP/KYC/PIN) work in every language.
Phase 2 (all 22 scheduled languages, native and romanized): inside Normalize — IndicLID (language ID incl. romanized) → IndicXlit (romanized → native script) → IndicTrans2 (→ English) → English rules. Translation is preprocessing only; rules still decide the score. Unsupported language today → lower confidence, stated honestly.

### 8.10 ML (Phase 2)
TF-IDF (char 3–5 + word n-grams) + calibrated Logistic Regression as one extra weighted signal. Requires a labeled Indian dataset with hard negatives (real OTPs, debit alerts, delivery updates).

---

## 9. Security & Privacy
Argon2 password hashing · JWT + rotated refresh cookies · ownership checks on every resource · rate limits (auth 5/min/IP, analyze 30/min/user) · field validation and size limits · magic-byte check for QR uploads, images processed in memory and never stored · no fetching of analyzed URLs · audit log for auth events and report actions · secrets only in `backend/.env` · RLS on all Supabase tables · CORS only for the frontend origin · "Don't save this scan" option · users can delete their scans · reports visible only to the owner (and admins in Phase 2).

---

## 10. Environment Variables

```
# backend/.env
APP_ENV=development
API_CORS_ORIGINS=http://localhost:3000
DATABASE_URL=postgresql+psycopg://postgres.<ref>:<password>@aws-0-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require
TEST_DATABASE_URL=<same format, garuda-test project>
JWT_SECRET=<64+ random characters>
JWT_ACCESS_TTL_MIN=15
REFRESH_TTL_DAYS=7
COOKIE_SECURE=false
RATE_LIMIT_ANALYZE=30/minute
MAX_QR_UPLOAD_MB=5
EMAIL_VERIFICATION_REQUIRED=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=          # Gmail app password
EMAIL_FROM=
# Phase 2: REDIS_URL, S3_*, OPENSEARCH_URL, ML_MODEL_PATH, TESSERACT_LANGS

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 11. Dependencies
Backend: fastapi, uvicorn[standard], pydantic ≥ 2, pydantic-settings, sqlalchemy ≥ 2, alembic, psycopg[binary], pwdlib[argon2], pyjwt, python-multipart, email-validator, httpx, pillow, opencv-python-headless, pyzbar, tldextract, idna, rapidfuzz, pyyaml, slowapi · dev: pytest, ruff
Frontend: next, react, typescript, tailwindcss, shadcn/ui (Radix), lucide-react, @tanstack/react-query, zod, react-hook-form, @hookform/resolvers, recharts, framer-motion (subtle), react-dropzone
System: Python 3.12+ (3.14 works), Node 20+, Git. No local database needed.

---

## 12. Testing
- **Golden set** (`tests/golden/messages.yaml`, 30+ cases incl. safe hard negatives) written BEFORE the engine; all safe cases must pass; ≥ 90 % overall. Fix general rules, never special-case test sentences.
- Unit tests: each rule pack, legitimacy signals, scorer math, URL features, UPI parser.
- API integration tests against `garuda-test` (TEST_DATABASE_URL).
- Security tests: IDOR (user A vs user B), tampered JWT, rate limits, oversized / wrong-type uploads, invalid URLs.
- Manual browser check after every chunk; responsive check at 375 / 768 / 1280 px.

---

## 13. Team Workflow (3 members)

**Roles**
| Member | Role | Owns |
|---|---|---|
| Junesh | Backend lead + integrator | `backend/app` core, `alembic/`, engine message rules, merges to `main` |
| Friend A | Frontend lead | `frontend/` |
| Friend B | Intelligence + QR | `engine/analyzers/url_analyzer.py`, `qr_analyzer.py`, `extractors/qr.py`, `extractors/upi.py`, `intel/`, `scripts/load_blocklists.py`, golden data, slides |

**Git workflow**
1. Junesh creates a **private** GitHub repo `garuda` after Chunk 1 and adds friends as collaborators.
2. Each friend clones it and creates `backend/.env` from `.env.example` with the connection strings Junesh sends privately.
3. Everyone works on their own branch (`feature/frontend-shell`, `feature/url-analyzer`, …), never directly on `main`.
4. At the end of each chunk: commit → push the branch → open a Pull Request. Junesh reviews and merges.
5. Everyone pulls `main` at the start of each day.
6. Ownership rule: don't edit files another member owns without telling them. Only Junesh creates Alembic migrations; others ask him for table changes.
7. Antigravity can run every git command: "create a branch called X", "commit and push this branch", "pull the latest main". GitHub Desktop is a click-based alternative.

---

## 14. Seven-Day Plan

| Day | Junesh (backend) | Friend A (frontend) | Friend B (intelligence + QR) |
|---|---|---|---|
| 1 | Chunk 1: backend + Supabase + schema; create GitHub repo | Install tools; Chunk 5A: design system, eagle logo, landing page | Install tools; collect 40+ real Indian scam and genuine messages (5 languages) |
| 2 | Chunk 2: golden tests + engine (using Friend B's samples) | Chunk 5B: login/register/verify pages, app shell UI | Chunk 7A: blocklist loader script + curated betting list |
| 3 | Chunks 3 + 4: auth + message analyze API | Connect auth + route guards once Chunk 3 is merged | Chunk 7B: URL analyzer + /api/analyze/url |
| 4 | Engine tuning from golden results; reviews/merges | Chunk 6: message analyzer page, history, scan detail, dashboard | Chunk 9: QR + UPI analyzer backend |
| 5 | Chunk 8 backend: reports + directory | URL analyzer, QR analyzer and report pages | Golden tests for URL/QR; help with pages |
| 6 | Chunk 10: email verification | Polish: responsive, empty/error states, accessibility | README (accurate), slides, demo script |
| 7 | **Feature freeze.** All: bug bash, full test run, demo rehearsal twice | | |

---

## 15. Phase 2 (designed, not built — present in slides)
Admin dashboard (/admin/*), Celery + Redis background processing, 22-lakh record ingestion (stream in 1,000-record chunks → SHA-256 dedupe → COPY into Supabase → workers run the same engine → OpenSearch index), image/OCR analyzer, ML classifier, 22-language translation layer, MinIO/S3 evidence storage with signed URLs.
