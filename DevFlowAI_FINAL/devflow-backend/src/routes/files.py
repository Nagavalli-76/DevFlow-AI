from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastFile
from src.config.database import get_db
from src.utils.auth import get_current_user
from src.config.settings import settings
import os, uuid

router = APIRouter()

ALLOWED_TYPES = ["image/png", "image/jpeg", "image/gif", "application/pdf", "text/plain", "application/zip"]

@router.post("/upload")
async def upload_file(
    file: UploadFile = FastFile(...),
    project_id: str = None,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "File type not allowed")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(400, f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB}MB")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4()}_{file.filename}"
    path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(content)

    record = await db.file.create(data={
        "name": file.filename,
        "url": f"/uploads/{filename}",
        "size": len(content),
        "mimeType": file.content_type,
        "projectId": project_id,
        "uploadedBy": current_user["id"],
    })
    return {"file": {"id": record.id, "name": record.name, "url": record.url, "size": record.size}}

@router.get("/")
async def list_files(project_id: str = None, db=Depends(get_db), current_user=Depends(get_current_user)):
    where = {"uploadedBy": current_user["id"]}
    if project_id:
        where["projectId"] = project_id
    files = await db.file.find_many(where=where, order={"createdAt": "desc"})
    return {"files": [{"id": f.id, "name": f.name, "url": f.url, "size": f.size, "mimeType": f.mimeType} for f in files]}

@router.delete("/{file_id}")
async def delete_file(file_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    file = await db.file.find_unique(where={"id": file_id})
    if not file or file.uploadedBy != current_user["id"]:
        raise HTTPException(404, "File not found")
    # Remove from disk
    disk_path = os.path.join(settings.UPLOAD_DIR, file.url.split("/")[-1])
    if os.path.exists(disk_path):
        os.remove(disk_path)
    await db.file.delete(where={"id": file_id})
    return {"message": "File deleted"}
