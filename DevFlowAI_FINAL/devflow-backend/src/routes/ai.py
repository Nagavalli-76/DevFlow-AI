from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, AsyncGenerator
from src.config.database import get_db
from src.config.redis import cache
from src.utils.auth import get_current_user
from src.config.settings import settings
import httpx
import json
import hashlib
import asyncio

router = APIRouter()

# ─── SCHEMAS ───
class ChatMessage(BaseModel):
    role: str   # "user" | "assistant" | "system"
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    project_id: Optional[str] = None
    context: Optional[str] = None
    stream: bool = False

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"
    project_id: Optional[str] = None

# ─── IBM WATSONX AI CALL ───
async def call_watsonx(messages: List[dict], stream: bool = False) -> AsyncGenerator[str, None]:
    """Call IBM watsonx.ai via REST API"""
    url = f"{settings.WATSONX_URL}/ml/v1/text/chat?version=2024-05-31"
    headers = {
        "Authorization": f"Bearer {settings.WATSONX_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model_id": settings.AI_MODEL,
        "project_id": settings.WATSONX_PROJECT_ID,
        "messages": messages,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
        }
    }
    if stream:
        body["stream"] = True

    async with httpx.AsyncClient(timeout=60) as client:
        if stream:
            async with client.stream("POST", url, headers=headers, json=body) as resp:
                full = ""
                async for line in resp.aiter_lines():
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data == "[DONE]": break
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0]["delta"].get("content", "")
                            full += delta
                            yield delta
                        except: pass
        else:
            resp = await client.post(url, headers=headers, json=body)
            data = resp.json()
            yield data["choices"][0]["message"]["content"]

# ─── FALLBACK MOCK (when watsonx not configured) ───
async def mock_ai_response(message: str) -> str:
    await asyncio.sleep(0.5)
    return f"IBM BOB AI: I've analyzed your query about '{message[:60]}...' Here's my comprehensive analysis based on the repository context and best practices."

# ─── CHAT ENDPOINT ───
@router.post("/chat")
async def chat(body: ChatRequest, db=Depends(get_db), current_user=Depends(get_current_user)):
    # Get or create conversation
    if body.conversation_id:
        conv = await db.aiconversation.find_unique(where={"id": body.conversation_id})
        if not conv or conv.userId != current_user["id"]:
            raise HTTPException(404, "Conversation not found")
    else:
        conv = await db.aiconversation.create(data={
            "userId": current_user["id"],
            "projectId": body.project_id,
            "title": body.message[:50],
        })

    # Save user message
    await db.message.create(data={
        "conversationId": conv.id,
        "userId": current_user["id"],
        "role": "USER",
        "content": body.message,
    })

    # Build message history
    history = await db.message.find_many(
        where={"conversationId": conv.id},
        order={"createdAt": "asc"},
        take=20,
    )
    messages = [{"role": m.role.lower(), "content": m.content} for m in history]

    if body.context:
        messages.insert(0, {"role": "system", "content": f"Project context: {body.context}\nYou are IBM BOB, an expert AI coding assistant for DevFlow AI."})

    # Check cache
    prompt_hash = hashlib.md5(json.dumps(messages).encode()).hexdigest()
    cached = await cache.get_cached_ai_response(prompt_hash)

    if cached:
        ai_text = cached
    else:
        if settings.WATSONX_API_KEY:
            ai_text = ""
            async for chunk in call_watsonx(messages):
                ai_text += chunk
        else:
            ai_text = await mock_ai_response(body.message)

        await cache.cache_ai_response(prompt_hash, ai_text, ttl=1800)

    # Save AI response
    await db.message.create(data={
        "conversationId": conv.id,
        "userId": None,  # AI messages don't have a userId
        "role": "ASSISTANT",
        "content": ai_text,
    })

    # Log activity
    await db.activitylog.create(data={
        "userId": current_user["id"],
        "projectId": body.project_id,
        "action": "AI_CHAT",
        "entity": "conversation",
        "entityId": conv.id,
    })

    return {
        "conversation_id": conv.id,
        "message": ai_text,
        "model": settings.AI_MODEL,
    }

# ─── STREAM CHAT ───
@router.post("/chat/stream")
async def chat_stream(body: ChatRequest, db=Depends(get_db), current_user=Depends(get_current_user)):
    messages = [
        {"role": "system", "content": "You are IBM BOB, an expert AI coding assistant for DevFlow AI."},
        {"role": "user", "content": body.message}
    ]

    async def generate():
        try:
            if settings.WATSONX_API_KEY:
                async for chunk in call_watsonx(messages, stream=True):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            else:
                response = await mock_ai_response(body.message)
                for word in response.split():
                    yield f"data: {json.dumps({'chunk': word + ' '})}\n\n"
                    await asyncio.sleep(0.05)
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

# ─── CONVERSATIONS ───
@router.get("/conversations")
async def list_conversations(db=Depends(get_db), current_user=Depends(get_current_user)):
    convs = await db.aiconversation.find_many(
        where={"userId": current_user["id"]},
        order={"updatedAt": "desc"},
        take=50,
    )
    return {"conversations": [{"id": c.id, "title": c.title, "createdAt": str(c.createdAt)} for c in convs]}

@router.get("/conversations/{conv_id}/messages")
async def get_messages(conv_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    conv = await db.aiconversation.find_unique(where={"id": conv_id})
    if not conv or conv.userId != current_user["id"]:
        raise HTTPException(404, "Conversation not found")

    messages = await db.message.find_many(where={"conversationId": conv_id}, order={"createdAt": "asc"})
    return {"messages": [{"id": m.id, "role": m.role, "content": m.content, "createdAt": str(m.createdAt)} for m in messages]}

@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    conv = await db.aiconversation.find_unique(where={"id": conv_id})
    if not conv or conv.userId != current_user["id"]:
        raise HTTPException(404, "Conversation not found")
    await db.aiconversation.delete(where={"id": conv_id})
    return {"message": "Deleted"}
