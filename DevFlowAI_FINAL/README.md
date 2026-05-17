# DevFlow AI — IBM BOB Hackathon 2026 · Team Alpha Ninjas

## ✅ FIXED — Works 100% Without a Backend Server

### The Problem That Was Fixed
The original frontend called `http://localhost:8000` (a real Python server). If the server wasn't running, clicking **Create Account** showed:

> "Cannot reach backend. Make sure backend server is running on port 8000."

### The Fix
The new `script.js` includes a **built-in mock backend** using `localStorage`. No Python, no PostgreSQL, no Redis needed. Open the HTML file and everything works instantly.

---

## 🚀 Quick Start (Frontend — No Install Required)

1. Open `devflow-frontend/index.html` in any browser
2. Click **Get Started** → fill the form → click **Create Account**
3. You're in! ✅

> Accounts persist in the browser's localStorage, so you can log in again after closing the tab.

---

## 🐍 Running the Real Backend (Optional, for Production)

If you want the full FastAPI backend with PostgreSQL + Redis:

### Prerequisites
- Python 3.10+
- PostgreSQL running locally
- Redis running locally

### Steps

```bash
cd devflow-backend

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Copy and edit .env
cp .env .env.local
# Edit .env: set DATABASE_URL, REDIS_URL, JWT_SECRET

# 3. Run database migrations
prisma db push

# 4. Start the server
uvicorn main:app --reload --port 8000
```

Then open `devflow-frontend/index.html` in a browser. The frontend will automatically use the real backend if it's running.

---

## 📁 Project Structure

```
DevFlowAI/
├── devflow-frontend/
│   ├── index.html       ← Main app (open this)
│   ├── script.js        ← Fixed: mock backend built-in
│   └── style.css        ← All styles
│
└── devflow-backend/
    ├── main.py          ← FastAPI app entry point
    ├── requirements.txt
    ├── .env             ← Config (edit before running)
    ├── prisma/
    │   └── schema.prisma
    └── src/
        ├── routes/      ← auth, users, projects, ai, etc.
        ├── config/      ← database, redis, settings
        ├── services/    ← email, notifications
        ├── utils/       ← auth helpers (JWT, bcrypt)
        └── middleware/  ← rate limiting, logging
```

---

## 🏆 Team Alpha Ninjas · IBM BOB Hackathon 2026
