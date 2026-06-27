# AI Career Copilot — Architecture Document

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER (User)                           │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Apply   │  │ Tracking │  │  Not     │  │   Global     │  │
│  │  Tab     │  │  Tab     │  │ Selected │  │  Analysis    │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│       │              │              │               │           │
│  ┌────▼──────────────▼──────────────▼───────────────▼────────┐ │
│  │           React + Zustand State (Session Storage)         │ │
│  │           Framer Motion · Recharts · Tailwind CSS         │ │
│  └───────────────────────────┬───────────────────────────────┘ │
└──────────────────────────────│──────────────────────────────────┘
                               │ HTTP (Axios · Vite Proxy)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                             │
│                                                                 │
│  POST /api/apply/upload-profile                                │
│  POST /api/apply/match                                          │
│  POST /api/apply/generate-resume                               │
│  POST /api/apply/submit                                         │
│  GET  /api/tracking/applications                               │
│  PUT  /api/tracking/applications/{id}/status                   │
│  POST /api/analysis/rejection/analyze                          │
│  GET  /api/analysis/global                                      │
│  POST /api/analysis/global/refresh                             │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                   AI Services Layer                    │    │
│  │                                                        │    │
│  │  Agent 1           Agent 2          Agent 3            │    │
│  │  Profile           Job Match        Resume Gen         │    │
│  │  Intelligence      Agent            Agent              │    │
│  │  ─────────         ──────────       ──────────         │    │
│  │  PyPDF2            Semantic         ReportLab PDF       │    │
│  │  python-docx       Matching         Tailored layout     │    │
│  │  Skill extract     Score 0-100      Ordered skills      │    │
│  │                                                        │    │
│  │  Agent 4: Learning & Insights Agent (⭐ Core)           │    │
│  │  ────────────────────────────────────────              │    │
│  │  Rejection analysis                                    │    │
│  │  Confidence delta calculation                          │    │
│  │  Global pattern detection                              │    │
│  │  Career recommendations                                │    │
│  └───────────────────────┬────────────────────────────────┘    │
│                           │ OpenAI GPT-4o (JSON mode)          │
│                           ▼                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                     data.json                          │    │
│  │                                                        │    │
│  │  metadata                                              │    │
│  │  current_profile_state  ← living, evolving profile     │    │
│  │  applications[]         ← all application records      │    │
│  │  rejections[]           ← rejection notes              │    │
│  │  profile_update_history[] ← skill evolution log        │    │
│  │  global_analysis        ← macro career insights        │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Concept: Living Profile

The most important architectural decision is the **Living Candidate Profile**.

```
Resume Upload
     │
     ▼
Profile Agent extracts:
  - skills + confidence scores (0-100)
  - experience, projects, domains
  - creates current_profile_state
     │
     ▼
User applies → Job Matching Agent
  - reads current_profile_state
  - calculates semantic match
     │
     ▼
User gets rejected → Learning Agent
  - reads rejection feedback
  - MUTATES skill confidence scores
  - adds new missing skills
  - stores delta in profile_update_history
     │
     ▼
Future applications use IMPROVED profile
  - higher quality matching
  - better tailored resumes
  - more relevant recommendations
```

---

## 3. Data Flow Per Tab

### Tab 1 — Apply

```
[Upload Resume] ──► profile_agent.parse_resume()
                         │ PyPDF2/python-docx text extraction
                         │ OpenAI JSON: skills[], experience[], projects[]
                         ▼
                    data.json[current_profile_state]

[Paste JD] ──────► job_matching_agent.match_job()
                         │ Semantic matching vs profile skills
                         │ OpenAI JSON: match%, matched[], missing[]
                         ▼
                    UI: animated score, skill badges

[Generate PDF] ──► resume_agent.generate_tailored_resume()
                         │ OpenAI JSON: tailored_summary, ordered_skills
                         │ ReportLab: professional PDF
                         ▼
                    Download .pdf

[Mark Submitted] ► POST /api/apply/submit
                         │ Creates Application record
                         ▼
                    data.json[applications[]]
```

### Tab 2 — Tracking

```
GET /api/tracking/applications
     │
     ▼
Kanban board (4 columns):
  Submitted → Interview → Selected
                        → Not Selected

PUT /api/tracking/applications/{id}/status
     │ Updates status + updated_at
     ▼
data.json[applications[]]
```

### Tab 3 — Not Selected

```
[Fill rejection form] ──► POST /api/analysis/rejection/analyze
                               │
                               ├─► learning_agent.analyze_rejection()
                               │       OpenAI: skill_changes[], recommendations[]
                               │
                               ├─► MUTATE current_profile_state
                               │       confidence scores updated
                               │
                               ├─► APPEND profile_update_history
                               │
                               └─► UPDATE application status → not_selected

UI shows:
  - SkillChange: Docker 80% → 50%
  - Recommendations: ["Learn Kubernetes"]
  - Profile evolution timeline
```

### Tab 4 — Global Analysis

```
POST /api/analysis/global/refresh
     │
     ▼
learning_agent.build_global_analysis(data)
     │ All rejections aggregated
     │ OpenAI: patterns, radar data, career_recommendations
     ▼
data.json[global_analysis]

UI shows:
  - Radar chart (6 skill categories)
  - Recurring missing skills (across companies)
  - Common interview topics
  - Career recommendations
```

---

## 4. OpenAI Integration

All AI calls use `response_format: {"type": "json_object"}` for **guaranteed structured output**.

```python
# Pattern used in all 4 agents:
response = await client.chat.completions.create(
    model="gpt-4o",
    response_format={"type": "json_object"},
    temperature=0.3,  # Low temperature for consistency
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_context},
    ],
)
data = json.loads(response.choices[0].message.content)
```

---

## 5. File Structure

```
ai-career-copilot/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── tabs/
│   │   │   │   ├── ApplyTab.tsx        # Upload → Match → Generate → Submit
│   │   │   │   ├── TrackingTab.tsx     # Kanban pipeline
│   │   │   │   ├── NotSelectedTab.tsx  # Rejection form + AI analysis
│   │   │   │   └── GlobalAnalysisTab.tsx # Radar + insights
│   │   │   ├── shared/
│   │   │   │   ├── Header.tsx          # Sticky top bar
│   │   │   │   └── Sidebar.tsx         # Left nav + mobile bottom bar
│   │   │   └── ui/
│   │   │       ├── Button.tsx          # Multi-variant button
│   │   │       ├── Card.tsx            # Glassmorphism card
│   │   │       ├── Badge.tsx           # Status/skill badges
│   │   │       ├── Progress.tsx        # Animated progress + counter
│   │   │       ├── Spinner.tsx         # Loading + AI thinking animation
│   │   │       ├── Toast.tsx           # Toast notification system
│   │   │       └── Tooltip.tsx         # Hover tooltips
│   │   ├── hooks/
│   │   │   └── useAppStore.ts          # Zustand global store
│   │   ├── lib/
│   │   │   ├── api.ts                  # All axios API calls
│   │   │   └── utils.ts                # cn(), formatDate, STATUS_CONFIG
│   │   └── types/index.ts              # TypeScript interfaces
│   └── (config files)
│
└── backend/
    ├── agents/
    │   ├── profile_agent.py            # PDF/DOCX parsing + OpenAI
    │   ├── job_matching_agent.py       # Semantic job matching
    │   ├── resume_agent.py             # Tailored resume generation
    │   └── learning_agent.py           # Rejection analysis + global
    ├── routers/
    │   ├── apply.py                    # /api/apply/*
    │   ├── tracking.py                 # /api/tracking/*
    │   └── analysis.py                 # /api/analysis/*
    ├── services/
    │   ├── storage_service.py          # Async data.json R/W
    │   ├── openai_service.py           # OpenAI client wrapper
    │   └── pdf_service.py              # ReportLab PDF generation
    ├── models/schemas.py               # All Pydantic models
    ├── config.py                       # Settings (pydantic-settings)
    ├── main.py                         # FastAPI app + CORS + routers
    └── data/data.json                  # Single source of truth
```

---

## 6. UI/UX Design Principles

- **Dark theme** — slate-950 background with indigo/purple gradient accents
- **Glassmorphism cards** — `bg-slate-900/60 backdrop-blur-xl`
- **Framer Motion** — page transitions, card entry animations, counter animations
- **Responsive** — sidebar on desktop, bottom tab bar on mobile
- **Error resilience** — every API call has try/catch with toast notifications
- **Loading states** — per-action loading flags in Zustand, never global blocking

---

## 7. Deployment Guide

### Frontend → Vercel

```bash
cd frontend
npm run build        # Outputs to dist/
# Push to GitHub → connect to Vercel
# Add env: VITE_API_URL=https://your-backend.onrender.com
```

### Backend → Render

```yaml
# render.yaml
services:
  - type: web
    name: ai-career-copilot-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: OPENAI_API_KEY
        sync: false
```

### Environment Variables

| Variable | Where | Value |
|---------|-------|-------|
| `OPENAI_API_KEY` | Backend (Render) | `sk-...` |
| `VITE_API_URL` | Frontend (Vercel) | `https://api.onrender.com` |
