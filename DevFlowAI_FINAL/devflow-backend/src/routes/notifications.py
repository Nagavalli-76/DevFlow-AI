from fastapi import APIRouter, Depends
from src.config.database import get_db
from src.utils.auth import get_current_user

router = APIRouter()

@router.get("/")
async def list_notifications(db=Depends(get_db), current_user=Depends(get_current_user)):
    notifs = await db.notification.find_many(
        where={"userId": current_user["id"]},
        order={"createdAt": "desc"},
        take=50
    )
    return {
        "notifications": [{"id": n.id, "type": n.type, "title": n.title, "body": n.body, "isRead": n.isRead, "createdAt": str(n.createdAt)} for n in notifs],
        "unreadCount": len([n for n in notifs if not n.isRead])
    }

@router.put("/{notif_id}/read")
async def mark_read(notif_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    await db.notification.update_many(
        where={"id": notif_id, "userId": current_user["id"]},
        data={"isRead": True}
    )
    return {"message": "Marked as read"}

@router.put("/read-all")
async def mark_all_read(db=Depends(get_db), current_user=Depends(get_current_user)):
    await db.notification.update_many(
        where={"userId": current_user["id"], "isRead": False},
        data={"isRead": True}
    )
    return {"message": "All marked as read"}
