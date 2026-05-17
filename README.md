# ⚡ DevFlow AI
### *IBM BOB-Powered Developer Productivity Platform*

> An AI-augmented full-stack development workspace that supercharges developer teams with IBM watsonx.ai — built for the **IBM BOB Hackathon 2026** by Team **Alpha Ninjas**.

---

## 👥 Team Alpha Ninjas — IBM BOB Hackathon 2026

| Member | Role |
|---|---|
| **Nagavalli Kodidasu** | Frontend Developer & UI/UX Designer |
| **Anurag Dudi** | Backend Developer & AI Integration Engineer |

---

## 🧩 Problem Statement

Modern software development teams face a fragmentation crisis. Developers constantly context-switch between:

- **Multiple disconnected tools** — project boards, code editors, deployment dashboards, and chat tools all live in separate tabs.
- **Manual, repetitive workflows** — code reviews, bug triage, and task assignments drain hours that should go toward building.
- **No intelligent assistance at the right moment** — generic AI chatbots lack the context of your actual project, codebase, and team.
- **Poor observability** — teams have limited real-time visibility into deployment health, task progress, and team performance.

The result: developers spend more time managing tools than writing code, leading to slower delivery, burnout, and lower software quality.

---

## 💡 Our Solution — DevFlow AI

**DevFlow AI** is a unified, AI-first developer workspace that brings project management, AI code assistance, team collaboration, deployment tracking, and analytics into a single, cohesive platform — all powered by **IBM watsonx.ai (IBM BOB)**.

### ✅ Key Capabilities

| Feature | Description |
|---|---|
| 🤖 **IBM BOB AI Assistant** | Conversational AI powered by `meta-llama/llama-3-3-70b-instruct` via IBM watsonx.ai — answers code questions, reviews bugs, generates code, and gives architecture advice in real time |
| 📋 **Project & Task Management** | Full Kanban-style task board with priorities, assignees, status tracking, and deadlines |
| 👥 **Team Workspace** | Invite team members, assign roles (Admin / Member), and collaborate across projects |
| 🚀 **Deployment Tracker** | Track deployment pipelines across environments (dev, staging, production) in real time |
| 📊 **Analytics Dashboard** | Visualize team velocity, task completion rates, AI usage stats, and project health |
| 🔔 **Notifications** | Real-time in-app notifications for task updates, deployments, and mentions |
| 🔐 **Auth System** | JWT-based authentication with GitHub & Google OAuth support (backend), mock auth for demo |
| 💾 **Works Offline (Demo)** | Frontend includes a built-in mock backend using `localStorage` — zero setup required to demo |

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| **HTML5** | App structure & semantic markup |
| **CSS3** (custom, ~2500 lines) | Full design system — dark theme, animations, responsive layout |
| **Vanilla JavaScript (ES6+)** | App logic, routing, mock backend, API integration |
| **Google Fonts** — Outfit, JetBrains Mono, Fraunces | Typography system |
| **Netlify** | Static hosting & live deployment |

### Backend
| Technology | Purpose |
|---|---|
| **Python 3.10+** | Primary backend language |
| **FastAPI** `0.111.0` | REST API framework with async support |
| **Uvicorn** `0.29.0` | ASGI server for high-performance async I/O |
| **Prisma ORM** `0.13.1` | Type-safe database ORM with schema-first design |
| **PostgreSQL** | Primary relational database |
| **Redis** `5.0.4` | Session caching, rate limiting, AI response caching |
| **Pydantic v2** `2.7.1` | Request/response validation & settings management |
| **Passlib + bcrypt** | Secure password hashing |
| **Python-JOSE + PyJWT** | JWT token generation & verification |
| **HTTPX** `0.27.0` | Async HTTP client for IBM watsonx.ai API calls |
| **Aiofiles** | Async file uploads |

### AI & IBM Integration
| Technology | Purpose |
|---|---|
| **IBM watsonx.ai** | Core AI engine — `ml/v1/text/chat` API |
| **meta-llama/llama-3-3-70b-instruct** | LLM model served via IBM BOB |
| **IBM IAM Token Service** | Secure API key → access token exchange |
| **Redis AI Cache** | MD5-hashed prompt caching to minimize watsonx API calls |

---

## 📁 Folder Structure

```
DevFlowAI_FINAL/
│
├── devflow-frontend/               # Static frontend (Netlify deployment)
│   ├── index.html                  # Single-page application entry point
│   ├── script.js                   # App logic + built-in mock backend (localStorage)
│   └── style.css                   # Complete design system & all page styles
│
└── devflow-backend/                # Python FastAPI backend (production)
    ├── main.py                     # FastAPI app — middleware, routers, lifespan
    ├── requirements.txt            # Python dependencies
    ├── seed.py                     # Database seed script for initial data
    ├── .env                        # Environment configuration (template)
    │
    ├── prisma/
    │   └── schema.prisma           # Database schema — User, Team, Project, Task,
    │                               #   AIConversation, Message, Notification, ActivityLog
    │
    └── src/
        ├── __init__.py
        │
        ├── ai/                     # IBM watsonx.ai integration layer
        │   ├── watsonx_client.py   # WatsonxClient — chat, streaming, code analysis
        │   ├── ai_service.py       # AIService — caching, logging, token tracking
        │   ├── aii.py              # Extended AI utilities
        │   └── ibm_token.py        # IBM IAM access token exchange
        │
        ├── config/                 # App configuration
        │   ├── settings.py         # Pydantic settings (env vars)
        │   ├── database.py         # Prisma DB connection
        │   └── redis.py            # Redis client & cache helpers
        │
        ├── routes/                 # API route handlers
        │   ├── auth.py             # /api/v1/auth — register, login, OAuth, refresh
        │   ├── users.py            # /api/v1/users — profile, update
        │   ├── teams.py            # /api/v1/teams — create, invite, manage
        │   ├── projects.py         # /api/v1/projects — CRUD, status
        │   ├── tasks.py            # /api/v1/tasks — Kanban CRUD, assignees
        │   ├── ai.py               # /api/v1/ai — IBM BOB chat, code review
        │   ├── deployments.py      # /api/v1/deployments — pipeline tracking
        │   ├── analytics.py        # /api/v1/analytics — velocity, metrics
        │   ├── files.py            # /api/v1/files — file upload/download
        │   ├── notifications.py    # /api/v1/notifications — alerts, read status
        │   └── websocket.py        # /ws — real-time WebSocket events
        │
        ├── services/               # Business logic services
        │   ├── email_service.py    # Gmail SMTP — welcome & alert emails
        │   └── notification_service.py  # In-app notification dispatch
        │
        ├── utils/                  # Shared helpers
        │   └── auth.py             # JWT encode/decode, password hashing
        │
        └── middleware/             # HTTP middleware
            ├── rate_limit.py       # Redis-backed rate limiting
            └── logger.py           # Structured request logging
```

---

## 🚀 Getting Started

### Option 1 — Frontend Only (No Setup Required)

The frontend ships with a **built-in mock backend** using `localStorage`. Perfect for demo and evaluation:

1. Clone or download the project
2. Open `devflow-frontend/index.html` in any browser
3. Click **Get Started** → fill the form → click **Create Account**
4. You're in! All data persists in your browser across sessions.

> Or simply visit the **[Live Netlify Demo ↗](https://devflow-ai-ibm-bob.netlify.app/)**

---

### Option 2 — Full Stack (Backend + Frontend)

#### Prerequisites
- Python 3.10+
- PostgreSQL (running locally or remote)
- Redis (running locally or remote)
- IBM watsonx.ai API key ([get one here](https://www.ibm.com/products/watsonx-ai))

#### Backend Setup

```bash
# 1. Navigate to backend
cd devflow-backend

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env .env.local
# Edit .env with your actual values (see Environment Variables section)

# 5. Push database schema
prisma db push

# 6. (Optional) Seed with sample data
python seed.py

# 7. Start the server
uvicorn main:app --reload --port 8000
```

#### Frontend Setup

Simply open `devflow-frontend/index.html` in your browser, or serve with any static server:

```bash
# Using Python
python -m http.server 5500 --directory devflow-frontend

# Using Node.js
npx serve devflow-frontend
```

The frontend auto-detects if the backend is reachable and switches between real API and mock mode.

---

## ⚙️ Environment Variables

Create a `.env` file in `devflow-backend/` with the following:

```env
# App
DEBUG=true
SECRET_KEY=your-32-char-secret-key-here

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/devflow_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET=your-jwt-secret-32-chars-minimum
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# IBM watsonx.ai (required for AI features)
WATSONX_API_KEY=your-watsonx-api-key
WATSONX_PROJECT_ID=your-watsonx-project-id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
AI_MODEL=meta-llama/llama-3-3-70b-instruct

# GitHub OAuth (optional)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Email (Gmail SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USER=your.email@gmail.com
EMAIL_PASSWORD=your-16-char-app-password
```

---

## 🔌 API Overview

Base URL: `http://localhost:8000/api/v1`  
Interactive docs: `http://localhost:8000/api/docs`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create new user account |
| `POST` | `/auth/login` | Login, receive JWT tokens |
| `POST` | `/auth/refresh` | Refresh access token |
| `GET` | `/users/me` | Get current user profile |
| `GET/POST` | `/teams` | List / create teams |
| `GET/POST` | `/projects` | List / create projects |
| `GET/POST` | `/tasks` | List / create tasks |
| `POST` | `/ai/chat` | Chat with IBM BOB (watsonx.ai) |
| `POST` | `/ai/code-review` | Submit code for AI review |
| `GET` | `/deployments` | List deployment pipelines |
| `GET` | `/analytics` | Fetch team metrics |
| `GET/PATCH` | `/notifications` | List / mark notifications read |
| `WS` | `/ws/{user_id}` | Real-time WebSocket events |
| `GET` | `/health` | Server health check |

---

## 🌐 Live Demo

> **[https://devflow-ai-alphaninjas.netlify.app](https://devflow-ai-alphaninjas.netlify.app)**

The Netlify deployment serves the frontend in mock mode. All features (dashboard, task board, AI chat, analytics, deployments, settings) are fully functional without a backend server.

**Demo credentials:** Register any account on the sign-up page — no email verification required in demo mode.

---

## 🔮 Future Improvements

| Priority | Feature |
|---|---|
| 🔴 High | **GitHub Integration** — connect repos, trigger deployments from PR merges, sync issues as tasks |
| 🔴 High | **Real-time Collaboration** — live cursor sharing, simultaneous task editing via WebSocket |
| 🟡 Medium | **AI Code Review on PRs** — automatic IBM BOB review triggered on every pull request |
| 🟡 Medium | **VS Code Extension** — bring the DevFlow AI assistant directly into the editor |
| 🟡 Medium | **Mobile App** — React Native companion app for on-the-go notifications and task updates |
| 🟢 Low | **Slack / Discord Integration** — send deployment alerts and task updates to team channels |
| 🟢 Low | **Multi-model AI Support** — allow teams to switch between IBM watsonx models |
| 🟢 Low | **Billing & Plans** — Stripe-powered Free / Pro / Enterprise tier management |
| 🟢 Low | **Advanced Analytics** — sprint burndown charts, individual contributor heatmaps |
| 🟢 Low | **AI-generated Release Notes** — auto-summarize commits into a changelog with IBM BOB |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   DevFlow AI                        │
│                                                     │
│  ┌──────────────┐      ┌───────────────────────┐   │
│  │   Frontend   │◄────►│   FastAPI Backend      │   │
│  │  (Netlify)   │      │   (Python / Uvicorn)   │   │
│  │              │      │                        │   │
│  │  HTML/CSS/JS │      │  REST API + WebSocket  │   │
│  │  Mock Backend│      │  JWT Auth              │   │
│  └──────────────┘      └────────┬───────────────┘   │
│                                 │                   │
│                    ┌────────────┼────────────┐      │
│                    │            │            │      │
│             ┌──────┴──┐  ┌─────┴───┐  ┌────┴───┐  │
│             │PostgreSQL│  │  Redis  │  │IBM     │  │
│             │(Prisma)  │  │ (Cache) │  │watsonx │  │
│             └──────────┘  └─────────┘  └────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 📄 License

This project was built for the **IBM BOB Hackathon 2026** and is intended for educational and demonstration purposes.

---

<div align="center">

**Built with ❤️ by Team Alpha Ninjas**

Nagavalli Kodidasu · Anurag Dudi

*IBM BOB Hackathon 2026*

</div>
