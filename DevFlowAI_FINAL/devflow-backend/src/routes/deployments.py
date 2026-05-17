from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from src.config.database import get_db
from src.utils.auth import get_current_user
import asyncio

router = APIRouter()

class DeployRequest(BaseModel):
    project_id: str
    environment: Optional[str] = "production"
    branch: Optional[str] = "main"
    commit_hash: Optional[str] = None

async def simulate_deployment(deployment_id: str, db):
    """Simulate a build/deploy process"""
    await asyncio.sleep(2)
    await db.deployment.update(where={"id": deployment_id}, data={"status": "BUILDING", "logs": "Installing dependencies...\n"})
    await asyncio.sleep(3)
    await db.deployment.update(where={"id": deployment_id}, data={
        "status": "SUCCESS",
        "logs": "Installing dependencies...\nBuild complete!\nDeployed successfully.",
        "duration": 5,
        "url": f"https://devflow-app.vercel.app"
    })

@router.get("/")
async def list_deployments(project_id: Optional[str] = None, db=Depends(get_db), current_user=Depends(get_current_user)):
    where = {"userId": current_user["id"]}
    if project_id:
        where["projectId"] = project_id
    deploys = await db.deployment.find_many(where=where, order={"createdAt": "desc"}, take=20)
    return {"deployments": [{"id": d.id, "status": d.status, "environment": d.environment, "branch": d.branch, "createdAt": str(d.createdAt)} for d in deploys]}

@router.post("/", status_code=201)
async def deploy(body: DeployRequest, background_tasks: BackgroundTasks, db=Depends(get_db), current_user=Depends(get_current_user)):
    project = await db.project.find_unique(where={"id": body.project_id})
    if not project or project.ownerId != current_user["id"]:
        raise HTTPException(404, "Project not found")

    deployment = await db.deployment.create(data={
        "projectId": body.project_id,
        "userId": current_user["id"],
        "environment": body.environment,
        "branch": body.branch,
        "commitHash": body.commit_hash,
        "status": "PENDING",
    })

    background_tasks.add_task(simulate_deployment, deployment.id, db.get_client())

    await db.notification.create(data={
        "userId": current_user["id"],
        "type": "SYSTEM",
        "title": "Deployment Started",
        "body": f"Deploying {project.name} to {body.environment}",
    })

    return {"deployment": {"id": deployment.id, "status": "PENDING", "message": "Deployment started"}}

@router.get("/{deployment_id}")
async def get_deployment(deployment_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    d = await db.deployment.find_unique(where={"id": deployment_id})
    if not d or d.userId != current_user["id"]:
        raise HTTPException(404, "Deployment not found")
    return {"deployment": {"id": d.id, "status": d.status, "logs": d.logs, "url": d.url, "duration": d.duration}}

@router.delete("/{deployment_id}/cancel")
async def cancel_deployment(deployment_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    d = await db.deployment.find_unique(where={"id": deployment_id})
    if not d or d.userId != current_user["id"]:
        raise HTTPException(404, "Deployment not found")
    if d.status not in ["PENDING", "BUILDING"]:
        raise HTTPException(400, "Cannot cancel this deployment")
    await db.deployment.update(where={"id": deployment_id}, data={"status": "CANCELLED"})
    return {"message": "Deployment cancelled"}
