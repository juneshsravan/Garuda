# GARUDA — Build Plan v2 (Supabase · 3-person team · 7 days)

Put this file in `docs/BUILD_PLAN.md` next to `docs/ARCHITECTURE.md`.
ARCHITECTURE.md stays the source of truth for design. This file adds the build order, scope and the rules learned from build v1.

---

## 0. Before you start

**Junesh (once):**
1. Rename the old folder to `Garuda_old` (keep as backup).
2. Create `C:\Projects\Garuda` OUTSIDE OneDrive, with `docs\ARCHITECTURE.md` and `docs\BUILD_PLAN.md`.
3. Supabase: create `garuda-dev` and `garuda-test` (Mumbai) and copy both **Session pooler** strings (ARCHITECTURE Section 3).
4. Open the folder in Antigravity and paste Chunk 1.
5. After Chunk 1: create a private GitHub repo `garuda`, push, add both friends as collaborators, send them the two connection strings privately.

**Friends (once):** install Python, Node.js, Git, Antigravity → clone the repo → create `backend/.env` from `.env.example` with the strings → open the folder in Antigravity → tell it: "Read docs/ARCHITECTURE.md and docs/BUILD_PLAN.md. Create a branch called feature/<my-part>."

No local PostgreSQL or Docker is needed by anyone.

---

## 1. Chunks and owners

| Chunk | What | Owner | Done when |
|---|---|---|---|
| 1 | Backend + Supabase + 18 tables + RLS | Junesh | Tables in Supabase Table Editor, /api/health ok |
| 2 | Golden tests, then message engine | Junesh | All SAFE cases pass, ≥ 90 % overall |
| 3 | Auth | Junesh | User visible in Supabase |
| 4 | Message analyze API + scans | Junesh | Scan rows in Supabase |
| 5A | Design system, eagle logo, landing | Friend A | Landing page looks finished |
| 5B | Login/register/verify pages + app shell, connected to auth | Friend A | Login in browser, avatar, logout |
| 6 | Message analyzer page, history, scan detail, dashboard | Friend A | Full flow with real data |
| 7A | Blocklist loader | Friend B | Row counts per category |
| 7B | URL analyzer + API | Friend B | 1xbet → High, sbi.co.in → Likely Safe |
| 8 | Reports + directory (backend Junesh, pages Friend A) | Both | GAR-2026-000001 created |
| 9 | QR + UPI analyzer (backend Friend B, page Friend A) | Both | Fake UPI QR → High |
| 10 | Email verification | Junesh | Code email arrives, verify works |
| — | README, slides, demo | Friend B (+ all) | Rehearsed twice |

Day-by-day schedule: ARCHITECTURE Section 14.

Every chunk prompt ends with: commit on your branch, push the branch, open a Pull Request, stop. Junesh merges.

---

## 2. Rules learned from build v1 (agent must follow)

1. **PostgreSQL only.** Never create or fall back to SQLite. If DATABASE_URL fails, crash with a clear error.
2. **Schema only through Alembic.** No separate .sql schema files.
3. **Tests never touch the dev database.** Tests use the Supabase `garuda-test` project via TEST_DATABASE_URL.
4. **No Supabase Auth, no Supabase JS client, no Supabase keys in the frontend.** Supabase is only the database.
5. **No mock or hardcoded results in the frontend.** Every result comes from the API.
6. **Explanations are built only from what was detected in THIS input.** No fixed summary sentences.
7. **Evidence snippets cut on word boundaries.**
8. **Score must be fully explainable on screen:** every indicator and every legitimacy signal that changed the score is shown.
9. **Honest wording:** "Threats Detected" not "Blocked"; "Likely Safe" not "Verified Safe"; never "Likely Legitimate Communication" for URLs; never claim government verification.
10. **Invalid input is never scored as safe** — return a validation error or "Unable to Verify".
11. **Stop after every chunk.** If tests pass: commit on your own branch, push the branch, open a Pull Request. Never push to main.
12. **Explain each chunk:** what, why, how, how it connects.

---

## 3. Chunk prompts (paste one at a time)

### CHUNK 1 — Backend + Supabase + schema
```
Read docs/ARCHITECTURE.md and docs/BUILD_PLAN.md fully. Follow both exactly, especially BUILD_PLAN Section 2 rules.
Setup: Windows, Python 3.14, Node 24, Git. Database = Supabase only: garuda-dev (DATABASE_URL) and garuda-test (TEST_DATABASE_URL). No local PostgreSQL, no Docker database, no SQLite.

Do chunk 1 only:
1. git init with .gitignore (backend/.env, .venv, __pycache__, node_modules, *.db, .next).
2. FastAPI skeleton per ARCHITECTURE Sections 2 and 4: app/main.py, core/config.py (pydantic-settings from backend/.env), standard error format (Section 6), db/session.py, GET /api/health that also checks the database connection.
3. backend/.env.example with every variable from Section 10. I will paste my Supabase Session pooler strings into backend/.env as DATABASE_URL and TEST_DATABASE_URL; convert it to postgresql+psycopg:// with sslmode=require.
4. All SQLAlchemy models from Section 5 (18 core tables + email_verification_codes) (UUID PKs, created_at/updated_at, FKs, indexes, report reference sequence).
5. Alembic migrations (include users.email_verified_at, email_verification_codes, analysis_results.legitimacy_signals, qr_codes UPI columns from ARCHITECTURE Section 5) including: citext extension, and Row Level Security enabled on every table with no policies.
6. Run alembic upgrade head on Supabase and list the tables. Run the migrations on the test project too.
7. Start the backend and confirm /api/health and /docs work.
Explain what you built. If everything works, commit and push to GitHub (I will create the repo; ask me for its URL). Stop and wait for me.
```

### CHUNK 2 — Golden tests first, then the engine
```
Chunk 1 is done. Friend B's real sample messages are in backend/tests/golden/samples/ if available; add the good ones as extra golden cases. Do chunk 2: the detection engine, TEST-FIRST, per ARCHITECTURE Section 8 (8.1–8.5, 8.9) and BUILD_PLAN rules.

Step A — before writing engine code, create backend/tests/golden/messages.yaml with these cases and expected levels:
SCAMS (High unless noted):
1. Dear SBI customer, your YONO account will be suspended today. Update PAN immediately: http://sbi-yono-kyc.in-verify.xyz
2. Dear consumer, your electricity power will be disconnected tonight at 9:30 PM because previous month bill was not updated. Call our officer 9000000001 immediately.
3. Part time job! Like YouTube videos and earn ₹3000 daily. Contact HR on Telegram @easyjobs_hr (Medium or High)
4. Complete 3 tasks and get ₹150 bonus. To unlock VIP tasks deposit ₹2000, guaranteed 30% returns.
5. Join our SEBI-registered VIP stock tips group. Guaranteed 300% returns in 1 month. Limited seats.
6. Instant loan ₹5 lakh approved without CIBIL check. Pay ₹1,499 processing fee to receive the amount today.
7. This is Mumbai Customs. A parcel in your name contains illegal drugs. Join a video call with a CBI officer now or face immediate arrest.
8. Income Tax Dept: You are eligible for a refund of ₹15,490. Submit your bank details at http://incometax-refund.co.in-claim.top
9. KBC Lucky Draw winner! You won ₹25 lakh. Pay ₹12,500 GST to release your prize.
10. I sent ₹5,000 to you by mistake. Please approve the request on your UPI app and enter your PIN to receive it.
11. Hi Mom, this is my new number, my phone broke. Please send ₹20,000 urgently to help.urgent@ybl
12. Your Netflix payment failed. Re-enter your card details within 24 hours: http://netf1ix-billing.com
13. Congratulations! You won ₹500. Scan this QR immediately to claim your reward.
14. बधाई हो! आपने ₹10,000 का इनाम जीता है। इनाम पाने के लिए अभी इस लिंक पर क्लिक करें।
15. आपका बैंक खाता आज बंद हो जाएगा। KYC अपडेट करने के लिए तुरंत अपना OTP साझा करें।
16. మీ బ్యాంక్ ఖాతా ఈరోజు బ్లాక్ అవుతుంది. KYC అప్‌డేట్ కోసం వెంటనే మీ OTP చెప్పండి.
17. Meeku ₹5000 cashback vachindi. Ee link click chesi mee UPI PIN enter cheyandi.
18. Aapka SIM card 2 ghante me band ho jayega. KYC update ke liye turant is number pe call karo.
19. Sh@re y0ur 0TP n0w to av0id acc0unt bl0ck (Medium or High)
SAFE (Likely Safe, at most Suspicious):
20. Your OTP for transaction of Rs 1,450.00 at AMAZON INDIA is 482910. Valid for 10 mins. Do NOT share OTP or password with anyone. Bank NEVER calls for OTP - HDFC Bank
21. Rs.450.00 debited from A/c XX1234 on 03-10-26 to VPA zomato@icici. If not you, call the number on the back of your card.
22. Your Flipkart order for boAt earbuds will be delivered today by 8 PM.
23. SBI never asks for your OTP, PIN or password. Do not share them with anyone.
24. you were absent for 4th hour
25. The last date to pay semester fees is 15 October. Pay through the official college portal.
26. You earned ₹25 cashback on your recharge. It has been added to your wallet.
27. Your electricity bill of ₹1,240 is due on 20-10-2026. Pay via the official app or website.
28. Bro, send me the notes from yesterday's lecture.
EDGE:
29. Check out the class photos: https://bit.ly/3abcXYZ (Suspicious, not High)
30. 😂😂👍 (Likely Safe or Unable to Verify)

Step B — build the engine (normalize, rules, scoring, explain) as pure Python with no FastAPI imports:
- Rules match PHRASES IN CONTEXT, not single words. "OTP" alone is not a threat; "share your OTP" is. "Valid for 10 mins" is expiry info, not urgency.
- Add LEGITIMACY signals (bank "do not share" advisories, standard transaction/OTP formats, official sign-offs) that reduce the score, and show them in the result.
- Noisy-OR scoring + risk bands exactly as ARCHITECTURE 8.5, including the legitimacy formula and anti-gaming rule. Critical only with intel evidence.
- Evidence on word boundaries. Summary built only from detected signals; neutral honest summary when nothing is found.
- Lexicons in YAML per category × language (English, Hindi, Telugu, Romanized Telugu, Hinglish).
- Fix GENERAL rules when a case fails. Do not special-case exact test sentences (no overfitting).

Run the golden tests and show the full table (case, expected, actual score, level, pass/fail, indicators, legitimacy signals). Target: all SAFE cases pass and at least 90% overall. Explain what you built. If targets are met: commit on my branch, push, open a Pull Request. Stop and wait for me.
```

### CHUNK 3 — Authentication
```
Chunk 2 is done. Do chunk 3: authentication per ARCHITECTURE Sections 6, 9, 10.
- Argon2 (pwdlib) hashing, JWT access token 15 min, refresh token in httpOnly SameSite=Lax cookie, rotated on refresh, stored hashed in sessions.
- POST /api/auth/register (email, password min 8, full_name min 2), /login, /refresh, /logout, GET /api/auth/me.
- Validation errors return field-level details in error.details.
- EMAIL_VERIFICATION_REQUIRED setting, default false (verification is a later stretch feature).
- get_current_user and require_admin dependencies. In-memory rate limit on login/register (5/min/IP). Audit log for register, login, failed login, logout. CORS for http://localhost:3000 with credentials.
- Login fails with the same message for unknown email and wrong password.
- Tests on TEST_DATABASE_URL only: register, duplicate email, wrong password, unknown email, /me with and without token, tampered token, refresh rotation, logout revocation.
Run tests, demo in /docs, confirm the user appears in Supabase. Explain. If tests pass: commit on my branch, push, open a Pull Request. Stop and wait for me.
```

### CHUNK 4 — Message analyze API + scans
```
Chunk 3 is done. Do chunk 4 per ARCHITECTURE Sections 6 and 8.
- services/scan_service.py calls engine.analyze() (no duplicated logic) and saves scans, messages, analysis_results, threat_indicators, and urls found (source=message) in one transaction.
- POST /api/analyze/message {text, save}: login required, text 1–5000 chars, 30/min/user, exact response format from ARCHITECTURE Section 6 including legitimacy signals. save=false stores nothing.
- GET /api/scans (own scans, newest first, cursor pagination, filters scan_type and risk_level), GET /api/scans/{id} (404 for other users), DELETE /api/scans/{id}.
- Tests on TEST_DATABASE_URL: ₹500 QR message High and saved in all tables; HDFC OTP Likely Safe; save=false stores nothing; user A can't read/delete user B's scan; unauthenticated rejected; empty/too-long rejected.
Run tests, demo in /docs, show rows in Supabase. Explain. If tests pass: commit on my branch, push, open a Pull Request. Stop and wait for me.
```

### CHUNK 5 — Frontend foundation
```
Do chunk 5 (I am Friend A, frontend). Work on branch feature/frontend. The backend auth API may not be merged yet: build against the API contract in ARCHITECTURE Section 6 and connect when it is merged; any temporary mock must be marked // MOCK and removed before the PR. Next.js frontend foundation per ARCHITECTURE Section 7 and BUILD_PLAN rules.
- Next.js App Router + TypeScript + Tailwind + shadcn/ui + lucide-react + React Query + zod + react-hook-form. Design tokens from ARCHITECTURE Section 7 (dark navy, electric blue, subtle cyan, risk colors). No neon, no Matrix effects.
- An original minimal GARUDA eagle logo as an SVG component, used everywhere.
- Landing page (/) with hero "DETECT. VERIFY. PROTECT.", buttons "Analyze a Threat" and "Explore GARUDA", a realistic console preview, and sections: How GARUDA Works, Multimodal Detection, Explainable Risk, History, Reporting, Privacy & Security, Final CTA, Footer. Top marketing nav ONLY on the landing page.
- /login and /register: field-level errors from the API and zod, eye icon to show/hide password.
- App shell for logged-in pages: sidebar (Dashboard, Message Analyzer, URL Analyzer, History, Reports, Profile) + slim top bar with page title and profile avatar (initial, dropdown with name, email, Profile, Logout).
- Route guards: app pages redirect to /login when logged out; /login and /register redirect to /dashboard when logged in. Access token in memory, refresh via cookie on page load.
Test register → login → avatar → logout in the browser. Explain. If tests pass: commit on my branch, push, open a Pull Request. Stop and wait for me.
```

### CHUNK 6 — Analyzer page, history, dashboard
```
Chunk 5 is merged and chunk 4 (message API) is merged. Do chunk 6 on branch feature/frontend-analyzer.
- /message-analyzer: large input, character counter, "Save to history" toggle, Analyze button, loading/error states. Result: risk gauge, level, confidence, category, summary, threat indicators with evidence and weight, legitimacy signals, recommended actions, verify steps. All data from the API, no mock.
- /history: table from GET /api/scans with filters (type, risk level), pagination, delete with confirmation dialog, empty state.
- /scan/[id]: full saved analysis.
- GET /api/dashboard/stats (backend, own data): total scans, threats detected (High+Critical), suspicious (Suspicious+Medium), likely safe, risk distribution, scans over last 14 days, top categories, 5 recent scans.
- /dashboard: 4 stat cards (Total Scans, Threats Detected, Suspicious, Likely Safe), Recharts charts (activity line, risk distribution, categories), recent scans list.
- Responsive at 375, 768, 1280 px.
Test the full flow with 5 golden messages. Explain. If tests pass: commit on my branch, push, open a Pull Request. Stop and wait for me.
```

### CHUNK 7 — URL Analyzer + blocklists
```
Do chunk 7 (I am Friend B). Work on branch feature/url-analyzer. Only edit url_analyzer.py, intel/, scripts/load_blocklists.py, the url route and tests; ask Junesh if a table change is needed. Follow ARCHITECTURE Sections 5, 6, 8.6 and 8.7. Never fetch or visit analyzed URLs.
- Validation: reject invalid input (spaces, no domain) with a clear message; normalize missing scheme.
- Static checks: IP host, punycode, @ in URL, subdomain depth, risky TLDs, shorteners, brand lookalikes (edit distance vs Indian banks, wallets, couriers, gov), suspicious params (pin, otp, password).
- backend/scripts/load_blocklists.py: download open lists (StevenBlack gambling + porn extensions, URLhaus malware/phishing), batch-load into threat_intelligence (source, indicator_type=domain, indicator_hash, verdict=category). Re-runnable, no duplicates. Plus garuda_curated betting list: 1xbet, parimatch, betway, stake, lotus365, mahadev. Match on registered domain.
- Scoring: phishing/malware High; gambling High, category "Illegal Betting / Gambling Platform" with India legal explanation; adult Medium, category "Restricted Content (Adult)". verification_status names the matched list. Not found → "Not found in GARUDA's reputation lists", never "safe verified".
- POST /api/analyze/url saves to scans + urls + analysis_results + threat_indicators; /url-analyzer page like the message analyzer.
- Show loaded row counts per category. Test: sbi.co.in, sbi-kyc-update.xyz/login, bit.ly/3abcXYZ, indian.1xbet.com, invalid "xxx videos.com", google.com.
Explain. If tests pass: commit on my branch, push, open a Pull Request. Stop and wait for me.
```

### CHUNK 8 — Reports + README + demo prep
```
Do chunk 8 on branch feature/reports.
- POST/GET /api/reports, GET /api/reports/{id} per ARCHITECTURE Section 6. Categories: Scam, Phishing, Financial Fraud, QR Scam, Malicious Website, Fake Account, Impersonation, Other. Evidence: attach a previous scan or text. Reference GAR-{year}-{seq:06d} from the Postgres sequence. Status history starting at "submitted".
- /reports (list), /reports/new (3 steps: details → evidence → review & submit), /reports/[id] with a right-side status panel: "Submitted to GARUDA", reference ID, status "Under Review" timeline. NEVER claim a government authority received it.
- GET /api/directory/reporting-channels: cybercrime.gov.in and helpline 1930 as external links labeled "GARUDA does not submit to this channel on your behalf".
- "Report this" button on scan results pre-fills a report.
- Update README.md accurately: Implemented vs Planned lists, Supabase setup, Windows + macOS/Linux commands, only real endpoints, MIT license.
- Run ALL backend tests and the golden set; show the final table.
Explain. If tests pass: commit on my branch, push, open a Pull Request. Stop and wait for me.
```

---

### CHUNK 9 — QR + UPI analyzer (backend Friend B, page Friend A)
```
Do chunk 9 on branch feature/qr-upi, following ARCHITECTURE Sections 6 and 8.8. Never open decoded destinations.
- POST /api/analyze/qr: multipart image (≤ 5 MB, png/jpg/webp, magic-byte check, processed in memory, never stored) or {payload}; save flag.
- Decode with OpenCV QRCodeDetector, pyzbar fallback. Classify payload: url / upi / text / wifi / other.
- UPI (upi://pay?pa=&pn=&am=&tn=): extract payee VPA, name, amount, note. Flags: pre-filled amount with reward/refund text, payee name claiming a brand/government with a personal-looking handle, "scan to receive money" (receiving never needs a scan or PIN), note text with urgency.
- URL payloads go through the existing URL analyzer + blocklists.
- Save scans + qr_codes (+ urls) + analysis_results + threat_indicators.
- /qr-analyzer page: drag-and-drop / upload / paste image, decoded payload preview card (never a clickable link for risky results), UPI details card, then the standard result panel.
- Generate test QR images in tests: a genuine merchant UPI, a fake "claim ₹500 reward" UPI with amount, a QR with sbi-kyc-update.xyz, plain text. Run tests and show results.
Explain. If tests pass: commit on my branch, push, open a Pull Request. Stop and wait for me.
```

### CHUNK 10 — Email verification (Junesh)
```
Do chunk 10 on branch feature/email-verification, following ARCHITECTURE Sections 5, 6, 9, 10.
- SMTP settings from backend/.env (Gmail app password). Never in code.
- On register when EMAIL_VERIFICATION_REQUIRED=true: user inactive, random 6-digit code, store only its hash, 10-minute expiry, GARUDA-branded email.
- POST /api/auth/verify-email (5 attempts per code), POST /api/auth/resend-code (1/min/email). Login returns EMAIL_NOT_VERIFIED for unverified accounts.
- Development only: if SMTP is empty and APP_ENV=development, log the code to the backend console.
- /verify-email page with code input, resend button with 60 s countdown; login page shows a "Verify your email" link on EMAIL_NOT_VERIFIED.
- Audit log: code sent, verified, failed. Tests mock email sending.
Test the full flow with my real email. Explain. If tests pass: commit on my branch, push, open a Pull Request. Stop and wait for me.
```

---

## 4. Your check after each chunk (2 minutes)

- Chunk 1: Supabase → Table Editor shows 18 tables.
- Chunk 2: golden table — all SAFE cases pass.
- Chunk 3: register in /docs → user in Supabase `users`, password starts with `$argon2id$`.
- Chunk 4: analyze in /docs → rows in `scans`, `analysis_results`, `threat_indicators`.
- Chunk 5: register/login in browser, avatar appears, logout works.
- Chunk 6: analyze 5 messages → dashboard numbers and history update.
- Chunk 7: `indian.1xbet.com` → High, Illegal Betting.
- Chunk 8: file a report → GAR-2026-000001 appears.
- Chunk 9: upload a fake reward UPI QR → High, UPI details shown.
- Chunk 10: register with your real email → code arrives → verify → login.
