# AI Career Copilot — Architecture Document

> Last updated: reflects multi-agent resume tailoring (LaTeX/DOCX), step-by-step matching, guardrails, auth, job discovery, and CI.

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
Generate resume → Multi-agent Resume Pipeline tailors content to JD + ATS (structure preserved)
       ↓
Export → Reference LaTeX template → PyLaTeX PDF compile (ReportLab fallback)
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

### 3.3 Agent 3 — Resume Tailoring (`resume_pipeline.py` + `resume_structure_agents.py`)

**Multi-agent pipeline** — preserves original resume structure and full content while optimizing for ATS. All agents return **structured JSON** via `openai_service.chat_json()` and are wrapped by guardrails (`wrap_untrusted_content`, `sanitize_ai_text`, `apply_agent_policy`, per-agent `agent=` tags).

#### Architecture diagram

```
                    ┌─────────────────────────────────────────┐
                    │  Inputs                                  │
                    │  • CandidateProfile                      │
                    │  • ResumeSnapshot (raw text + sections)  │
                    │  • Job description + MatchContextInput   │
                    │  • ResumeStyle (optional reference tone)   │
                    └──────────────────┬──────────────────────┘
                                       │
         ┌─────────────────────────────┴─────────────────────────────┐
         │ STEP 0 — Parallel (asyncio.gather)                        │
         ├─────────────────────────────┬───────────────────────────────┤
         │ resume_step0_structure      │ resume_step0_ats            │
         │ analyze_resume_structure()  │ extract_ats_keywords()      │
         │ → section_order[]           │ → primary/secondary keywords│
         │ → sections_found[]          │ → all_keywords[]            │
         └─────────────────────────────┴───────────────────────────────┘
                                       │
                                       ▼
         ┌─────────────────────────────────────────────────────────────┐
         │ STEP 1 — resume_step1_plan                                  │
         │ Plan tailoring: priority roles/projects, keywords_to_weave, │
         │ experience_order, tailoring_steps[]                         │
         └─────────────────────────────┬───────────────────────────────┘
                                       │
         ┌─────────────────────────────┴───────────────────────────────┐
         │ STEP 2 — Parallel section agents (asyncio.gather)           │
         ├──────────────┬──────────────┬──────────────┬──────────────┤
         │ step2_summary│ step2_skills │ step2_projects│ step2_experience │
         │ tailored_    │ ordered_     │ highlighted_ │ ONE call per   │
         │ summary      │ skills[]     │ projects[],  │ profile role   │
         │              │              │ key_achieve- │ (parallel)     │
         │              │              │ ments[]      │ bullets[]      │
         └──────────────┴──────────────┴──────────────┴──────────────┘
                                       │
                                       ▼
         ┌─────────────────────────────────────────────────────────────┐
         │ STEP 3 — Deterministic merge (no LLM)                       │
         │ • _merge_tailored_with_profile — every original role kept   │
         │ • _ensure_bullet_count — pad from originals if AI drops     │
         │ • _order_experience_entries — reorder per plan, no omission │
         └─────────────────────────────┬───────────────────────────────┘
                                       │
                                       ▼
         ┌─────────────────────────────────────────────────────────────┐
         │ STEP 4 — Structured package + document build                │
         │ ResumePreviewResponse (Pydantic) + latex_source string        │
         │ → templates/resume/preamble.tex + build_latex_document()      │
         └─────────────────────────────┬───────────────────────────────┘
                                       │
                                       ▼
                    compile_latex_to_pdf() via PyLaTeX + pdflatex
                    (ReportLab fallback if compile unavailable)
```

Reference layout matches the professional ATS LaTeX template (letterpaper, `\color{Blue}` sections, `\scshape` name header, categorized skills, experience itemize with `\justifying`). See `Resume-Latex-ref/Pavankumar_Resume.pdf` for expected output.

#### Structured output contract

| Stage | Agent tag | JSON output (key fields) |
|-------|-----------|--------------------------|
| 0a | `resume_step0_structure` | `section_order`, `sections_found`, `structure_notes` |
| 0b | `resume_step0_ats` | `primary_keywords`, `secondary_keywords`, `role_titles` |
| 1 | `resume_step1_plan` | `priority_experience`, `keywords_to_weave`, `experience_order` |
| 2a | `resume_step2_summary` | `tailored_summary` |
| 2b | `resume_step2_skills` | `ordered_skills` (all skills, JD-prioritized) |
| 2c | `resume_step2_projects` | `highlighted_projects`, `key_achievements`, `emphasis` |
| 2d | `resume_step2_experience` | `company`, `role`, `duration`, `bullets[]` (same count as original) |

**Final API model:** `ResumePreviewResponse` — summary, skills, experience entries, `section_order`, `ats_keywords`, `latex_source`, `tailoring_steps[]`.

**Original content preservation:** On upload, `ResumeSnapshot` stores `raw_text` + heuristic `section_order`. Merge step guarantees no role or bullet is dropped (max 15 bullets/role via `MAX_EXPERIENCE_BULLETS`).

#### Document generation

| Format | Module | Mechanism |
|--------|--------|-----------|
| **LaTeX source** | `latex_service.py` + `templates/resume/preamble.tex` | Reference-template builder — escapes special chars, respects `section_order` |
| **PDF** | `latex_service.py` | **PyLaTeX** (`Document.generate_pdf`) compiles via system **`pdflatex`** |
| **PDF fallback** | `pdf_service.py` | **ReportLab** when PyLaTeX/pdflatex unavailable or compile fails |

**Endpoints:**
- `POST /api/apply/resume-preview` — JSON preview (+ `match_context`, `latex_source`)
- `POST /api/apply/generate-resume` — PDF (PyLaTeX + pdflatex preferred)

**Wrappers:** `resume_agent.py` orchestrates pipeline → `generate_resume_pdf_from_package()`.

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
                      └─ Multi-agent tailoring pipeline (structure + ATS + per-role)
                      └─ UI: section order, ATS keywords, tailoring steps, latex_source
6. Download PDF       POST /api/apply/generate-resume (+ match_context)
                      └─ Reference LaTeX → PyLaTeX + pdflatex (ReportLab fallback)
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

- `pytest` — 112+ backend tests (guardrails, matching/resume pipeline, LaTeX/DOCX, routers)
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
    │   ├── shared/profile_context.py      # Rich candidate context builder
    │   ├── matching_pipeline.py           # 3-step JD matching
    │   ├── resume_structure_agents.py     # Step 0: structure + ATS (parallel)
    │   ├── resume_pipeline.py             # Multi-agent resume tailoring
    │   ├── profile_agent.py
    │   ├── job_matching_agent.py          # thin wrapper → pipeline
    │   ├── resume_agent.py                # pipeline → LaTeX PDF / DOCX
    │   └── learning_agent.py
    ├── services/
    │   ├── guardrails/                    # Input/output/policy/rate limits
    │   ├── openai_service.py              # LLM gateway (JSON structured output)
    │   ├── latex_service.py               # Reference LaTeX + PyLaTeX PDF compile
    │   ├── templates/resume/preamble.tex  # Professional ATS LaTeX preamble
    │   ├── pdf_service.py                 # ReportLab PDF fallback
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
