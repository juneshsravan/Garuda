# GARUDA 2.0 — Team Collaboration & Onboarding Guide

Welcome to **GARUDA** (India-Focused Multi-Modal Citizen Cyber-Defense Platform).
This document provides clear onboarding steps, branch policies, architecture contracts, and local development instructions for all team members.

---

## 1. Team Responsibilities & Ownership

| Contributor | Focus Area | Active Branch | Primary Deliverables |
| :--- | :--- | :--- | :--- |
| **Junesh (Lead)** | Backend Core & Detection Engine | `main` | Core platform, models, Alembic migrations, pure Python engine, auth, reports API |
| **Friend A** | Frontend (Next.js 14 App Router) | `feature/frontend` | Design system, eagle theme, landing page, auth UI, scan dashboards, citizen reporting |
| **Friend B** | Intel, URLs, QR & Presentations | `feature/url-analyzer` | Threat intel blocklists loader, URL analyzer, QR/UPI verification, demo slides & README |

---

## 2. Prerequisites & Environment Setup

- **Python**: 3.12+ (tested on Python 3.14)
- **Node.js**: 20+ (recommended Node 24 LTS)
- **Git**
- **Database**: PostgreSQL 15+ (Local development: `garuda` and `garuda_test`; or Supabase connection string)

### Initial Setup Steps:
1. **Clone the repository:**
   ```bash
   git clone https://github.com/juneshsravan/Garuda.git
   cd Garuda
   ```

2. **Configure Backend Environment:**
   ```bash
   cd backend
   cp .env.example .env
   ```
   *Never commit `backend/.env`! It is ignored by `.gitignore`.*

3. **Install Backend Dependencies:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```

4. **Run Database Migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start Dev Server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Check health endpoint: `http://localhost:8000/api/health`

---

## 3. Architecture & Coding Rules

All team members must follow the core guidelines in `docs/ARCHITECTURE.md` and `docs/BUILD_PLAN.md`:

1. **Zero Framework Imports in Engine Core (`app/engine`)**:
   - The detection engine must remain pure Python standard library + PyYAML.
   - Never import FastAPI, SQLAlchemy, or Pydantic inside `app/engine`.
2. **Never Fetch Untrusted URLs**:
   - URL and link analysis must remain purely static (lexical inspection, homoglyph unfolding, domain whitelisting).
   - Never visit, scrape, or issue HTTP GET/POST requests to suspicious links.
3. **Database RLS & Migrations**:
   - Only Junesh creates database migration scripts.
   - All tables must have Row Level Security (RLS) enabled.
4. **Honest Verification**:
   - The engine never labels messages "Verified Safe" — use `likely_safe`, `suspicious`, `medium`, `high`, `critical`, or `unable_to_verify`.
   - Neutral personal messages must not receive artificial legitimacy signals.

---

## 4. Test Suites & Verification

Before opening PRs or merging, run the test suites from `backend/`:

```bash
# 1. Lexicon Parity Test (ensures 10 concepts across all 5 languages)
python -u tests/golden/test_parity.py

# 2. Golden Dataset (30 core benchmark cases)
python -u tests/golden/test_golden.py

# 3. Holdout Validation Set (12 unseen generalization cases)
python -u tests/golden/test_holdout.py

# 4. Regression Exam 1 Set (14 complex edge cases)
python -u tests/golden/test_regression_exam1.py
```

Target: **100% of SAFE/Genuine cases must pass** and overall scams pass rate must exceed **90%**.

---

## 5. Git Workflow & Branch Policy

- `main`: Main production branch maintained by Junesh.
- `feature/<name>`: Feature branches for frontend and intel analyzers.
- Before opening a PR to `main`:
  1. Pull latest `main`: `git pull origin main`
  2. Resolve any merge conflicts.
  3. Run all 4 test suites to ensure zero regressions.
  4. Submit PR for review.
