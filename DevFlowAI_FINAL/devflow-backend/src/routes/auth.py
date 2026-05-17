from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr, field_validator
from src.config.database import get_db
from src.config.redis import cache
from src.config.settings import settings
from src.utils.auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from src.services.notification_service import NotificationService
from src.services.email_service import EmailService
import asyncio
import httpx

router = APIRouter()

# ─── TTL CONSTANTS (in seconds) ───
SESSION_TTL = 86400  # 1 day
EMAIL_VERIFICATION_TTL = 86400  # 1 day
RESET_TOKEN_TTL = 1800  # 30 minutes

# ─── SCHEMAS ───
class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    name: str
    password: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 30:
            raise ValueError('Username must not exceed 30 characters')
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Username can only contain alphanumeric characters, hyphens, and underscores')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

# ─── SIGNUP ───
@router.post("/signup", status_code=201)
async def signup(body: SignupRequest, db=Depends(get_db)):
    # Check existing
    existing = await db.user.find_first(where={"OR": [{"email": body.email}, {"username": body.username}]})
    if existing:
        raise HTTPException(400, "Email or username already taken")

    user = await db.user.create(data={
        "email": body.email,
        "username": body.username,
        "name": body.name,
        "passwordHash": hash_password(body.password),
        "isVerified": False,
    })

    # Generate verification token
    import secrets
    verification_token = secrets.token_urlsafe(32)
    # Store token in Redis for 24 hours
    await cache.redis.setex(f"verify:{verification_token}", EMAIL_VERIFICATION_TTL, str(user.id))

    # Send verification email (async, don't block response)
    if settings.EMAIL_USER:
        asyncio.create_task(
            asyncio.to_thread(EmailService.send_verification, user.email, user.name, verification_token)
        )

    # In-app welcome notification
    await NotificationService.create(db, user.id, "SYSTEM", "Welcome to DevFlow AI! 🚀", "Please verify your email to get full access.")

    # Return tokens but user needs to verify email for full access
    access  = create_access_token(user.id, user.email)
    refresh = create_refresh_token()
    await db.user.update(where={"id": user.id}, data={"refreshToken": refresh})

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "name": user.name, "username": user.username, "isVerified": False},
        "message": "Account created. Please check your email to verify your account."
    }

# ─── LOGIN ───
@router.post("/login")
async def login(body: LoginRequest, request: Request, db=Depends(get_db)):
    user = await db.user.find_unique(where={"email": body.email})
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    # Check if user has a password (not OAuth-only account)
    if not user.passwordHash:
        raise HTTPException(401, "This account uses OAuth login (GitHub/Google). Please use the appropriate login method.")
    
    # Verify password
    if not verify_password(body.password, user.passwordHash):
        raise HTTPException(401, "Invalid credentials")

    # Check if email is verified
    if not user.isVerified:
        raise HTTPException(403, "Please verify your email before logging in. Check your inbox for the verification link.")

    access  = create_access_token(user.id, user.email)
    refresh = create_refresh_token()
    await db.user.update(where={"id": user.id}, data={"refreshToken": refresh})
    await cache.set_session(user.id, {"email": user.email, "role": user.role}, ttl=SESSION_TTL)

    # Send login alert email (optional)
    if settings.SEND_LOGIN_ALERT and settings.EMAIL_USER:
        client_ip = request.client.host if request.client else "Unknown"
        asyncio.create_task(
            asyncio.to_thread(EmailService.send_login_alert, user.email, user.name, client_ip)
        )

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role}
    }

# ─── EMAIL VERIFICATION ───
@router.get("/verify-email")
async def verify_email(token: str, db=Depends(get_db)):
    # Get user ID from Redis token
    user_id = await cache.redis.get(f"verify:{token}")
    if not user_id:
        raise HTTPException(400, "Invalid or expired verification token")
    
    # Update user verification status
    user = await db.user.update(
        where={"id": user_id},
        data={"isVerified": True}
    )
    
    # Delete the token from Redis
    await cache.redis.delete(f"verify:{token}")
    
    # Send welcome email now that they're verified
    if settings.SEND_WELCOME_EMAIL and settings.EMAIL_USER:
        asyncio.create_task(
            asyncio.to_thread(EmailService.send_welcome, user.email, user.name)
        )
    
    return {"message": "Email verified successfully! You can now log in."}

# ─── RESEND VERIFICATION EMAIL ───
@router.post("/resend-verification")
async def resend_verification(body: ForgotPasswordRequest, db=Depends(get_db)):
    user = await db.user.find_unique(where={"email": body.email})
    if not user:
        # Don't reveal if email exists
        return {"message": "If that email is registered and unverified, a verification link has been sent."}
    
    if user.isVerified:
        raise HTTPException(400, "Email is already verified")
    
    # Generate new verification token
    import secrets
    verification_token = secrets.token_urlsafe(32)
    # Store token in Redis for 24 hours
    await cache.redis.setex(f"verify:{verification_token}", EMAIL_VERIFICATION_TTL, str(user.id))
    
    # Send verification email
    if settings.EMAIL_USER:
        asyncio.create_task(
            asyncio.to_thread(EmailService.send_verification, user.email, user.name, verification_token)
        )
    
    return {"message": "If that email is registered and unverified, a verification link has been sent."}

# ─── FORGOT PASSWORD ───
@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db=Depends(get_db)):
    user = await db.user.find_unique(where={"email": body.email})
    # Always return success to avoid email enumeration
    if user and settings.EMAIL_USER:
        import secrets
        reset_token = secrets.token_urlsafe(32)
        # Store token in Redis for 30 minutes
        await cache.redis.setex(f"reset:{reset_token}", RESET_TOKEN_TTL, str(user.id))
        asyncio.create_task(
            asyncio.to_thread(EmailService.send_password_reset, user.email, user.name, reset_token)
        )
    return {"message": "If that email is registered, a reset link has been sent."}

# ─── REFRESH TOKEN ───
@router.post("/refresh")
async def refresh(body: RefreshRequest, db=Depends(get_db)):
    user = await db.user.find_first(where={"refreshToken": body.refresh_token})
    if not user:
        raise HTTPException(401, "Invalid refresh token")

    access      = create_access_token(user.id, user.email)
    new_refresh = create_refresh_token()
    await db.user.update(where={"id": user.id}, data={"refreshToken": new_refresh})

    return {"access_token": access, "refresh_token": new_refresh, "token_type": "bearer"}

# ─── LOGOUT ───
@router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}

# ─── GITHUB OAUTH ───
@router.get("/github")
async def github_auth():
    url = f"https://github.com/login/oauth/authorize?client_id={settings.GITHUB_CLIENT_ID}&scope=user:email"
    return {"redirect_url": url}

@router.get("/github/callback")
async def github_callback(code: str, db=Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={"client_id": settings.GITHUB_CLIENT_ID, "client_secret": settings.GITHUB_CLIENT_SECRET, "code": code},
            headers={"Accept": "application/json"}
        )
        token_data = token_resp.json()
        gh_token   = token_data.get("access_token")

        user_resp = await client.get("https://api.github.com/user", headers={"Authorization": f"Bearer {gh_token}"})
        gh_user   = user_resp.json()

    user = await db.user.find_first(where={"githubId": str(gh_user["id"])})
    if not user:
        async with httpx.AsyncClient() as client:
            email_resp = await client.get("https://api.github.com/user/emails", headers={"Authorization": f"Bearer {gh_token}"})
        emails        = email_resp.json()
        primary_email = next((e["email"] for e in emails if e["primary"]), None)

        user = await db.user.create(data={
            "email":    primary_email or f"{gh_user['login']}@github.local",
            "username": gh_user["login"],
            "name":     gh_user.get("name") or gh_user["login"],
            "githubId": str(gh_user["id"]),
            "avatar":   gh_user.get("avatar_url"),
            "isVerified": True,
        })
        if settings.SEND_WELCOME_EMAIL and settings.EMAIL_USER and primary_email:
            asyncio.create_task(asyncio.to_thread(EmailService.send_welcome, primary_email, user.name))

    access  = create_access_token(user.id, user.email)
    refresh = create_refresh_token()
    await db.user.update(where={"id": user.id}, data={"refreshToken": refresh})

    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
