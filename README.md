# AI Career Copilot

> An intelligent, AI-powered job application assistant that learns from every rejection and continuously improves your career strategy.

![License](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/Python-3.11+-green) ![React](https://img.shields.io/badge/React-18-blue)

---

## Overview

AI Career Copilot is a living career intelligence system. Unlike simple job trackers, it maintains an **evolving candidate profile** — updated after every rejection — so that every future application is smarter than the last.

**Core innovation:** A single `data.json` file serves as the complete source of truth, enabling a fully stateful AI system without a database.

---

## Four Tabs

| Tab | Purpose |
|-----|---------|
| **Apply** | Upload resume → match against JD → generate tailored PDF → submit |
| **Tracking** | Kanban board tracking: Submitted → Interview → Selected / Not Selected |
| **Not Selected** | Log rejection feedback → AI analyzes → updates skill confidence scores |
| **Global Analysis** | Radar chart + pattern detection across all rejections |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS + Framer Motion |
| State | Zustand (session-persisted) |
| Charts | Recharts (Radar chart) |
| Backend | FastAPI + Python 3.11+ |
| AI | OpenAI GPT-4o (structured JSON outputs) |
| Resume PDF | ReportLab |
| Doc Parsing | PyPDF2 + python-docx |
| Storage | Single `data.json` file |

---

## Quick Start

### 1. Clone & Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/ai-career-copilot.git
cd ai-career-copilot
```

### 2. Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key

uvicorn main:app --reload --port 8000
```

Backend runs at: http://localhost:8000  
API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

---

## Environment Variables

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

---

## Project Structure

```
ai-career-copilot/
├── frontend/                    # React + Vite app
│   └── src/
│       ├── components/
│       │   ├── tabs/            # 4 main tab components
│       │   ├── shared/          # Header, Sidebar
│       │   └── ui/              # Design system components
│       ├── hooks/useAppStore.ts # Zustand global state
│       ├── lib/api.ts           # Axios API layer
│       └── types/index.ts       # TypeScript interfaces
│
├── backend/                     # FastAPI app
│   ├── agents/                  # 4 AI agents
│   │   ├── profile_agent.py     # Agent 1: Resume parsing
│   │   ├── job_matching_agent.py # Agent 2: JD matching
│   │   ├── resume_agent.py      # Agent 3: PDF generation
│   │   └── learning_agent.py    # Agent 4: Rejection learning
│   ├── routers/                 # API routes
│   ├── services/                # Storage, OpenAI, PDF
│   ├── models/schemas.py        # Pydantic models
│   └── data/data.json           # Single source of truth
│
├── ARCHITECTURE.md              # Detailed system design
└── README.md
```

---

## AI Agents

1. **Profile Intelligence Agent** — Parses uploaded resumes (PDF/DOCX), extracts skills with confidence scores, domains, projects.

2. **Job Matching Agent** — Semantic skill matching against job descriptions. Returns match %, matched/missing skills, and recommendation.

3. **Resume Generation Agent** — Creates tailored summaries, reorders skills by JD relevance, generates professional PDF via ReportLab.

4. **Learning & Insights Agent** — Analyzes rejection feedback, updates skill confidence scores, generates action recommendations, and builds global career insights.

---

## Deployment

| Service | Platform |
|---------|---------|
| Frontend | Vercel |
| Backend | Render |
| Storage | `data.json` (included in backend) |

See `ARCHITECTURE.md` for detailed deployment instructions.
