# Setup & GitHub Repository Guide

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `ai-career-copilot`
3. Set to **Public**
4. Do NOT initialize with README (we have one)
5. Click **Create repository**

---

## Step 2: Initialize Git & Push

Open PowerShell in the project root (`AI_Job_Application_Assistant/`):

```powershell
git init
git add .
git commit -m "feat: initial commit - AI Career Copilot hackathon project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-career-copilot.git
git push -u origin main
```

---

## Step 3: Backend Setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate

pip install -r requirements.txt

# Create .env file
Copy-Item .env.example .env
# Open .env and add your OPENAI_API_KEY

uvicorn main:app --reload --port 8000
```

✅ API docs available at: http://localhost:8000/docs

---

## Step 4: Frontend Setup

Open a new terminal:

```powershell
cd frontend
npm install
npm run dev
```

✅ App available at: http://localhost:5173

---

## Step 5: Verify Everything Works

1. Open http://localhost:5173
2. Go to the **Apply** tab
3. Upload a PDF resume
4. Paste a job description
5. Click "Extract Skills & Calculate Match"
6. Generate and download the tailored resume
7. Click "Mark as Submitted"
8. Switch to **Tracking** tab — your application appears
9. Move it to "Not Selected"
10. Go to **Not Selected** tab — analyze the rejection
11. Go to **Global Analysis** — click "Refresh Analysis"

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| CORS error | Make sure backend is running on port 8000 |
| OpenAI error | Check `.env` has valid `OPENAI_API_KEY` |
| PDF parse fails | Ensure PyPDF2 is installed; try a text-heavy PDF |
| Frontend 404 on /api | Vite proxy requires backend on port 8000 |
