# AI Career Copilot — Architecture Document

> Last updated: reflects step-by-step matching & resume tailoring pipelines, guardrails, auth, job discovery, and CI.

---

## 1. System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           BROWSER (React + Vite)                         │
│  Discover │ Apply │ Tracking │ Not Selected │ Global Analysis │ Auth     │
│       Zustand (useAppStore + useAuthStore) · sessionStorage              │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │ HTTPS · JWT Bearer · Vite proxy /api
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend (main.py)                        │
│  SecurityHeaders · MaxBodySize · CORS · Auth · Guardrails (ai_guard)     │
│                                                                          │
│  Routers: auth · apply · jobs · tracking · analysis · data               │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 4 AI Agents   │     │ Job Feed Layer  │     │ Per-user JSON   │
│ (OpenAI GPT)  │     │ LinkedIn/GH/HC  │     │ storage_service │
└───────────────┘     └─────────────────┘     └─────────────────┘
```

---

## 2. Core Concept: Living Profile

The **Living Candidate Profile** (`current_profile_state`) evolves with every application and rejection:

```
Upload resume → Profile Agent parses skills, experience, projects
       ↓
Apply to jobs → Matching Pipeline scores fit vs JD (step-by-step)
       ↓
Generate resume → Resume Pipeline tailors bullets to JD + match analysis
       ↓
Rejection → Learning Agent adjusts skill confidence + recommendations
       ↓
Future matches & resumes use the improved profile
```

---

## 3. AI Agent Architecture

### 3.1 Agent 1 — Profile Intelligence (`profile_agent.py`)

| Input | Output |
|-------|--------|
| PDF / DOCX / TXT resume | `CandidateProfile` |

- Extracts text (PyPDF2 / python-docx)
- OpenAI JSON: name, skills + confidence, experience bullets, projects, education
- Optional reference resume → `ResumeStyle` (tone, section order — **style only, never content**)

### 3.2 Agent 2 — Job Matching (`matching_pipeline.py`)

**Step-by-step pipeline** (3 LLM calls, evidence-based):

```
Step 1 — Extract JD requirements
  → company, role, seniority, must-have / nice-to-have skills, responsibilities

Step 2 — Map candidate evidence
  → experience_matches[], project_matches[], skill_evidence[], gaps[]
  (uses full profile context including experience bullets)

Step 3 — Score & recommend
  → match_percentage, score_breakdown {skills, experience, projects, domain}
  → matched_skills, missing_skills, experience_highlights, matching_steps[]
```

**Endpoint:** `POST /api/apply/match`

**Response (`MatchResponse`):** score, skills, recommendation, `matching_steps`, `score_breakdown`, `experience_highlights`

### 3.3 Agent 3 — Resume Tailoring (`resume_pipeline.py`)

**Step-by-step pipeline** (2 LLM calls, uses match context):

```
Step 1 — Plan tailoring
  → priority experience/projects, keywords to weave, tailoring plan

Step 2 — Produce package
  → tailored_summary, ordered_skills, highlighted_projects
  → tailored_experience[] with REWRITTEN bullets per role (JD-aligned)
  → key_achievements, emphasis, tailoring_steps[]
```

**Endpoints:**
- `POST /api/apply/resume-preview` — JSON preview (passes `match_context` from Step 2)
- `POST /api/apply/generate-resume` — ReportLab PDF with tailored experience bullets

**PDF (`pdf_service.py`):** renders rewritten experience bullets, JD-prioritized skills, highlighted projects.

### 3.4 Agent 4 — Learning & Insights (`learning_agent.py`)

| Trigger | Action |
|---------|--------|
| Rejection form | Analyze feedback → skill confidence deltas |
| Global refresh | Aggregate patterns → radar chart + career recommendations |

---

## 4. Apply Tab — End-to-End Flow

```
1. Upload profile     POST /api/apply/upload-profile
2. (Optional) reference resume style
3. Paste JD + company/role
4. Match              POST /api/apply/match
                      └─ 3-step matching pipeline
                      └─ UI: score breakdown, step list, experience highlights
5. Resume preview     POST /api/apply/resume-preview  (+ match_context)
                      └─ 2-step tailoring pipeline
6. Download PDF       POST /api/apply/generate-resume (+ match_context)
7. Submit application POST /api/apply/submit → tracking pipeline
```

---

## 5. Discover Tab — Live Job Feed

```
GET /api/jobs/live?refresh=true
  → LinkedIn guest search · Greenhouse boards · Hiring Cafe API
  → Location filter · remote-only · posted_within (24h / 3d / 7d / anytime)
  → Profile-based match scoring · cached per user
```

Preferences stored in `JobPreferences` via `PUT /api/auth/preferences`.

---

## 6. Guardrails Layer (`services/guardrails/`)

All AI endpoints use `ai_guard` dependency:

| Layer | Purpose |
|-------|---------|
| **Input** | HTML strip, length limits, URL validation, `<user_*>` delimiters |
| **Injection** | Heuristic scan + audit log |
| **Policy** | Appended to every system prompt (scope, no fabrication) |
| **Output** | Score clamping, forbidden phrase scrubbing |
| **Rate limit** | 30 AI calls / hour / user |
| **Files** | PDF page limit, extension whitelist |

See PR #10 for full guardrail matrix.

---

## 7. Auth & Data Isolation

- Email/password (always) · Google OAuth (optional via `GOOGLE_CLIENT_ID`)
- JWT sessions · per-user `backend/data/users/{id}/data.json`
- No shared `data.json` in multi-user mode

---

## 8. OpenAI Integration

```python
# All agents use openai_service.chat_json():
# - apply_agent_policy() on system prompt
# - sanitize user content · max_tokens · timeout
# - response_format: json_object
# - agent tag for audit logging (no PII in logs)
```

---

## 9. CI / Testing

GitHub Actions (`.github/workflows/ci.yml`):

- `pytest` — 75+ backend tests (guardrails, matching pipeline helpers, routers)
- `vitest` + `npm run build` — frontend
- Gate: **CI / All Tests Passed** (enable branch protection on `dev`)

Tests run **without real API keys** — conftest forces empty secrets.

---

## 10. File Structure

```
ai-career-copilot/
├── ARCHITECTURE.md          ← this document
├── .github/workflows/ci.yml
├── frontend/
│   └── src/
│       ├── components/tabs/
│       │   ├── DiscoverTab.tsx    # Live jobs + recency filter
│       │   ├── ApplyTab.tsx       # Match → tailor → submit
│       │   ├── TrackingTab.tsx    # Jobright-style pipeline
│       │   ├── NotSelectedTab.tsx # Rejection analysis
│       │   └── GlobalAnalysisTab.tsx
│       ├── hooks/                 # useAppStore · useAuthStore
│       └── lib/api.ts
└── backend/
    ├── agents/
    │   ├── shared/profile_context.py   # Rich candidate context builder
    │   ├── matching_pipeline.py        # 3-step JD matching
    │   ├── resume_pipeline.py          # 2-step resume tailoring
    │   ├── profile_agent.py
    │   ├── job_matching_agent.py       # thin wrapper → pipeline
    │   ├── resume_agent.py             # thin wrapper → pipeline
    │   └── learning_agent.py
    ├── services/
    │   ├── guardrails/                 # Input/output/policy/rate limits
    │   ├── openai_service.py           # LLM gateway
    │   ├── pdf_service.py              # Tailored PDF generation
    │   ├── job_feed_service.py         # Multi-source job aggregation
    │   └── job_recency.py              # Posted-within filtering
    ├── routers/                        # apply · jobs · auth · tracking · analysis
    ├── models/schemas.py               # Pydantic models + validators
    └── tests/
```

---

## 11. Environment Variables

| Variable | Where | Purpose |
|----------|-------|---------|
| `OPENAI_API_KEY` | backend/.env | Required for AI features |
| `JWT_SECRET` | backend/.env | Auth tokens |
| `GOOGLE_CLIENT_ID` | backend + frontend/.env | Optional Google sign-in |
| `VITE_GOOGLE_CLIENT_ID` | frontend/.env | Optional Google button |
| `VITE_API_URL` | frontend (prod) | Backend URL |

---

## 12. Deployment

**Frontend:** Vercel / static host — `npm run build` → `dist/`

**Backend:** Render / Railway — `uvicorn main:app --host 0.0.0.0 --port $PORT`

Both servers must run locally for development (backend `:8000`, frontend `:5173`).
