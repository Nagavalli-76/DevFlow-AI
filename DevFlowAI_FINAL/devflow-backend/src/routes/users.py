from fastapi import APIRouter, Depends, HTTPException
from src.config.database import get_db
from src.utils.auth import get_current_user

router = APIRouter()

@router.get("/me")
async def get_me(db=Depends(get_db), current_user=Depends(get_current_user)):
    user = await db.user.find_unique(where={"id": current_user["id"]})
    if not user:
        raise HTTPException(404, "User not found")
    return {"user": {"id": user.id, "email": user.email, "name": user.name, "username": user.username, "role": user.role, "avatar": user.avatar}}

@router.put("/me")
async def update_me(body: dict, db=Depends(get_db), current_user=Depends(get_current_user)):
    allowed = {k: v for k, v in body.items() if k in ["name", "avatar"]}
    user = await db.user.update(where={"id": current_user["id"]}, data=allowed)
    return {"user": user}

@router.get("/me/api-keys")
async def get_api_keys(db=Depends(get_db), current_user=Depends(get_current_user)):
    keys = await db.apikey.find_many(where={"userId": current_user["id"]}, order={"createdAt": "desc"})
    return {"keys": [{"id": k.id, "name": k.name, "createdAt": str(k.createdAt)} for k in keys]}

@router.post("/me/api-keys")
async def create_api_key(body: dict, db=Depends(get_db), current_user=Depends(get_current_user)):
    from src.utils.auth import generate_api_key
    key_val = generate_api_key()
    key = await db.apikey.create(data={"userId": current_user["id"], "name": body.get("name", "API Key"), "key": key_val})
    return {"key": {"id": key.id, "name": key.name, "key": key_val, "message": "Save this key — it won't be shown again"}}
