from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from src.config.database import get_db
from src.utils.auth import get_current_user

router = APIRouter()

class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None

class InviteMember(BaseModel):
    email: str
    role: Optional[str] = "MEMBER"

@router.get("/")
async def list_teams(db=Depends(get_db), current_user=Depends(get_current_user)):
    memberships = await db.teammember.find_many(
        where={"userId": current_user["id"]},
        include={"team": True}
    )
    return {"teams": [{"id": m.team.id, "name": m.team.name, "role": m.role, "plan": m.team.plan} for m in memberships]}

@router.post("/", status_code=201)
async def create_team(body: TeamCreate, db=Depends(get_db), current_user=Depends(get_current_user)):
    slug = body.name.lower().replace(" ", "-")
    team = await db.team.create(data={"name": body.name, "slug": slug, "description": body.description})
    await db.teammember.create(data={"userId": current_user["id"], "teamId": team.id, "role": "OWNER"})
    return {"team": {"id": team.id, "name": team.name, "slug": team.slug}}

@router.post("/{team_id}/invite")
async def invite_member(team_id: str, body: InviteMember, db=Depends(get_db), current_user=Depends(get_current_user)):
    membership = await db.teammember.find_first(where={"teamId": team_id, "userId": current_user["id"]})
    if not membership or membership.role not in ["OWNER", "ADMIN"]:
        raise HTTPException(403, "Insufficient permissions")

    user = await db.user.find_unique(where={"email": body.email})
    if not user:
        raise HTTPException(404, "User not found")

    existing = await db.teammember.find_first(where={"teamId": team_id, "userId": user.id})
    if existing:
        raise HTTPException(400, "User already in team")

    await db.teammember.create(data={"userId": user.id, "teamId": team_id, "role": body.role})
    await db.notification.create(data={
        "userId": user.id,
        "type": "TEAM_INVITE",
        "title": "Team Invitation",
        "body": f"You've been added to a team",
    })
    return {"message": "Member invited"}

@router.get("/{team_id}/members")
async def list_members(team_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    members = await db.teammember.find_many(where={"teamId": team_id}, include={"user": True})
    return {"members": [{"id": m.user.id, "name": m.user.name, "email": m.user.email, "role": m.role} for m in members]}
