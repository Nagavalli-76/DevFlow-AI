from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastFile
from src.config.database import get_db
from src.utils.auth import get_current_user
from src.config.settings import settings
import os, uuid

# ─── ANALYTICS ───
router = APIRouter()

@router.get("/dashboard")
async def dashboard_analytics(db=Depends(get_db), current_user=Depends(get_current_user)):
    uid = current_user["id"]
    projects = await db.project.count(where={"ownerId": uid})
    tasks = await db.task.count(where={"project": {"ownerId": uid}})
    done_tasks = await db.task.count(where={"project": {"ownerId": uid}, "status": "DONE"})
    deploys = await db.deployment.count(where={"userId": uid})
    success_deploys = await db.deployment.count(where={"userId": uid, "status": "SUCCESS"})
    convs = await db.aiconversation.count(where={"userId": uid})
    return {
        "analytics": {
            "totalProjects": projects,
            "totalTasks": tasks,
            "completedTasks": done_tasks,
            "taskCompletionRate": round(done_tasks / tasks * 100, 1) if tasks else 0,
            "totalDeployments": deploys,
            "successfulDeployments": success_deploys,
            "deploymentSuccessRate": round(success_deploys / deploys * 100, 1) if deploys else 0,
            "aiConversations": convs,
        }
    }
