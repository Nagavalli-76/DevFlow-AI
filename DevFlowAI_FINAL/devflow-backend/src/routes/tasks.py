from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from src.config.database import get_db
from src.utils.auth import get_current_user

router = APIRouter()

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: str
    assignee_id: Optional[str] = None
    priority: Optional[str] = "MEDIUM"
    due_date: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[str] = None

@router.get("/")
async def list_tasks(project_id: Optional[str] = None, db=Depends(get_db), current_user=Depends(get_current_user)):
    where = {"project": {"ownerId": current_user["id"]}}
    if project_id:
        where["projectId"] = project_id
    tasks = await db.task.find_many(where=where, order={"createdAt": "desc"})
    return {"tasks": [{"id": t.id, "title": t.title, "status": t.status, "priority": t.priority, "projectId": t.projectId} for t in tasks]}

@router.post("/", status_code=201)
async def create_task(body: TaskCreate, db=Depends(get_db), current_user=Depends(get_current_user)):
    project = await db.project.find_unique(where={"id": body.project_id})
    if not project or project.ownerId != current_user["id"]:
        raise HTTPException(404, "Project not found")

    task = await db.task.create(data={
        "title": body.title,
        "description": body.description,
        "projectId": body.project_id,
        "assigneeId": body.assignee_id,
        "priority": body.priority or "MEDIUM",
    })
    await db.activitylog.create(data={
        "userId": current_user["id"],
        "projectId": body.project_id,
        "action": "CREATE",
        "entity": "task",
        "entityId": task.id,
    })
    return {"task": {"id": task.id, "title": task.title, "status": task.status}}

@router.put("/{task_id}")
async def update_task(task_id: str, body: TaskUpdate, db=Depends(get_db), current_user=Depends(get_current_user)):
    task = await db.task.find_unique(where={"id": task_id}, include={"project": True})
    if not task or task.project.ownerId != current_user["id"]:
        raise HTTPException(404, "Task not found")

    update_data = {k: v for k, v in body.dict().items() if v is not None}
    updated = await db.task.update(where={"id": task_id}, data=update_data)
    return {"task": updated}

@router.delete("/{task_id}")
async def delete_task(task_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    task = await db.task.find_unique(where={"id": task_id}, include={"project": True})
    if not task or task.project.ownerId != current_user["id"]:
        raise HTTPException(404, "Task not found")
    await db.task.delete(where={"id": task_id})
    return {"message": "Task deleted"}
