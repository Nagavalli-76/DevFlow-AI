from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging

from src.config.settings import settings
from src.config.database import db
from src.config.redis import redis_client
from src.routes import auth, users, teams, projects, tasks, ai, deployments, analytics, files, notifications, websocket
from src.middleware.rate_limit import RateLimitMiddleware
from src.middleware.logger import LoggerMiddleware

# ─── LOGGING ───
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("devflow")

# ─── LIFESPAN ───
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting DevFlow AI backend...")
    await db.connect()
    await redis_client.ping()
    logger.info("✅ Database & Redis connected")
    yield
    # Shutdown
    await db.disconnect()
    await redis_client.close()
    logger.info("DevFlow AI backend stopped")

# ─── APP ───
app = FastAPI(
    title="DevFlow AI API",
    description="IBM BOB Hackathon — AI-powered developer productivity platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ─── MIDDLEWARE ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggerMiddleware)

# ─── ROUTERS ───
API = "/api/v1"
app.include_router(auth.router,          prefix=f"{API}/auth",          tags=["Auth"])
app.include_router(users.router,         prefix=f"{API}/users",         tags=["Users"])
app.include_router(teams.router,         prefix=f"{API}/teams",         tags=["Teams"])
app.include_router(projects.router,      prefix=f"{API}/projects",      tags=["Projects"])
app.include_router(tasks.router,         prefix=f"{API}/tasks",         tags=["Tasks"])
app.include_router(ai.router,            prefix=f"{API}/ai",            tags=["AI"])
app.include_router(deployments.router,   prefix=f"{API}/deployments",   tags=["Deployments"])
app.include_router(analytics.router,     prefix=f"{API}/analytics",     tags=["Analytics"])
app.include_router(files.router,         prefix=f"{API}/files",         tags=["Files"])
app.include_router(notifications.router, prefix=f"{API}/notifications",  tags=["Notifications"])
app.include_router(websocket.router,     prefix="/ws",                  tags=["WebSocket"])

# ─── HEALTH CHECK ───
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "devflow-ai-backend",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {"message": "DevFlow AI API — IBM BOB Hackathon", "docs": "/api/docs"}

# ─── GLOBAL ERROR HANDLER ───
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
