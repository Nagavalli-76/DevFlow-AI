from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from src.config.database import get_db
from src.config.redis import cache
from src.utils.auth import get_current_user

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    repo_url: Optional[str] = None
    team_id: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    repo_url: Optional[str] = None

@router.get("/")
async def list_projects(db=Depends(get_db), current_user=Depends(get_current_user)):
    cached = await cache.get(f"projects:{current_user['id']}")
    if cached:
        return cached

    projects = await db.project.find_many(
        where={"ownerId": current_user["id"]},
        order={"createdAt": "desc"},
        include={"tasks": True, "deployments": {"take": 1, "order": {"createdAt": "desc"}}}
    )
    result = {"projects": [
        {
            "id": p.id, "name": p.name, "description": p.description,
            "status": p.status, "repoUrl": p.repoUrl,
            "taskCount": len(p.tasks) if p.tasks else 0,
            "createdAt": str(p.createdAt)
        } for p in projects
    ]}
    await cache.set(f"projects:{current_user['id']}", result, ttl=60)
    return result

@router.post("/", status_code=201)
async def create_project(body: ProjectCreate, db=Depends(get_db), current_user=Depends(get_current_user)):
    project = await db.project.create(data={
        "name": body.name,
        "description": body.description,
        "repoUrl": body.repo_url,
        "teamId": body.team_id,
        "ownerId": current_user["id"],
    })
    await cache.delete(f"projects:{current_user['id']}")
    await db.activitylog.create(data={
        "userId": current_user["id"],
        "projectId": project.id,
        "action": "CREATE",
        "entity": "project",
        "entityId": project.id,
    })
    return {"project": {"id": project.id, "name": project.name, "status": project.status}}

@router.get("/{project_id}")
async def get_project(project_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    project = await db.project.find_unique(
        where={"id": project_id},
        include={"tasks": True, "deployments": {"take": 5, "order": {"createdAt": "desc"}}, "files": True}
    )
    if not project or project.ownerId != current_user["id"]:
        raise HTTPException(404, "Project not found")
    return {"project": project}

@router.put("/{project_id}")
async def update_project(project_id: str, body: ProjectUpdate, db=Depends(get_db), current_user=Depends(get_current_user)):
    project = await db.project.find_unique(where={"id": project_id})
    if not project or project.ownerId != current_user["id"]:
        raise HTTPException(404, "Project not found")

    update_data = {k: v for k, v in body.dict().items() if v is not None}
    updated = await db.project.update(where={"id": project_id}, data=update_data)
    await cache.delete(f"projects:{current_user['id']}")
    return {"project": updated}

@router.delete("/{project_id}")
async def delete_project(project_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    project = await db.project.find_unique(where={"id": project_id})
    if not project or project.ownerId != current_user["id"]:
        raise HTTPException(404, "Project not found")
    await db.project.delete(where={"id": project_id})
    await cache.delete(f"projects:{current_user['id']}")
    return {"message": "Project deleted"}

@router.get("/{project_id}/analytics")
async def project_analytics(project_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    tasks = await db.task.find_many(where={"projectId": project_id})
    deployments = await db.deployment.find_many(where={"projectId": project_id}, order={"createdAt": "desc"}, take=10)
    total = len(tasks)
    done = len([t for t in tasks if t.status == "DONE"])
    return {
        "analytics": {
            "totalTasks": total,
            "completedTasks": done,
            "completionRate": round(done / total * 100, 1) if total else 0,
            "recentDeployments": len(deployments),
            "deploymentSuccess": len([d for d in deployments if d.status == "SUCCESS"]),
        }
    }
