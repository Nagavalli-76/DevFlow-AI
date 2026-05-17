from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.config.settings import settings
import secrets

# ─── PASSWORD HASHING (FIXED FOR YOUR BUG) ───

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

security = HTTPBearer()


def hash_password(password: str) -> str:
    """
    bcrypt has a hard limit of 72 bytes.
    We enforce it BEFORE hashing to prevent runtime crash.
    """
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password too long (max 72 bytes for bcrypt)")

    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ─── JWT TOKENS ───

def create_access_token(user_id: str, email: str) -> str:
    """
    Create a JWT access token for authenticated users.
    
    Args:
        user_id (str): The unique identifier of the user.
        email (str): The email address of the user.
    
    Returns:
        str: A signed JWT access token containing user information and expiration time.
    
    Note:
        The token expires after the duration specified in settings.ACCESS_TOKEN_EXPIRE_MINUTES.
        The token includes the following claims:
        - sub: user_id
        - email: user email
        - exp: expiration timestamp
        - type: "access"
    """
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "type": "access"
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.
    
    Args:
        token (str): The JWT token string to decode.
    
    Returns:
        dict: The decoded token payload containing user information (sub, email, exp, type).
    
    Raises:
        HTTPException: 401 status code with "Token expired" detail if the token has expired.
        HTTPException: 401 status code with "Invalid token" detail if the token is malformed or invalid.
    
    Note:
        The token is validated against the JWT_SECRET and JWT_ALGORITHM from settings.
    """
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ─── AUTH DEPENDENCY ───

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    FastAPI dependency to extract and validate the current authenticated user from the request.
    
    Args:
        credentials (HTTPAuthorizationCredentials): The HTTP Bearer token credentials from the request header.
            Automatically injected by FastAPI's Security dependency.
    
    Returns:
        dict: A dictionary containing the authenticated user's information:
            - id (str): The user's unique identifier.
            - email (str): The user's email address.
    
    Raises:
        HTTPException: 401 status code if the token is expired, invalid, or missing.
    
    Usage:
        Use as a FastAPI dependency in route handlers:
        @app.get("/protected")
        async def protected_route(user = Depends(get_current_user)):
            return {"user_id": user["id"]}
    """
    token = credentials.credentials
    payload = decode_token(token)

    return {
        "id": payload["sub"],
        "email": payload["email"]
    }


# ─── API KEY GENERATION ───

def generate_api_key() -> str:
    return f"df_{secrets.token_urlsafe(32)}"