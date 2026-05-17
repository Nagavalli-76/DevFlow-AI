# src/ai/ibm_token.py
# ─────────────────────────────────────────────
# IBM IAM Token Generator
# IBM BOB API Key → IAM Access Token (required for every API call)
# Token expires every 60 minutes — auto-refreshed here
# ─────────────────────────────────────────────

import httpx
import time
import logging
from src.config.settings import settings

logger = logging.getLogger(__name__)

# ─── TOKEN CACHE (in-memory) ───
_token_cache = {
    "access_token": None,
    "expires_at": 0  # unix timestamp
}

IBM_IAM_URL = "https://iam.cloud.ibm.com/identity/token"

async def get_ibm_access_token() -> str:
    """
    Exchange your IBM API Key → IAM Access Token
    Automatically refreshes when expired (every ~60 min)
    
    Flow:
    Your WATSONX_API_KEY (from .env)
         ↓
    POST to IBM IAM endpoint
         ↓
    Get access_token (Bearer token)
         ↓
    Use in all watsonx API calls
    """
    now = time.time()

    # Return cached token if still valid (with 5 min buffer)
    if _token_cache["access_token"] and now < _token_cache["expires_at"] - 300:
        logger.debug("Using cached IBM IAM token")
        return _token_cache["access_token"]

    logger.info("Fetching new IBM IAM access token...")

    if not settings.WATSONX_API_KEY:
        raise ValueError("WATSONX_API_KEY is not set in .env file!")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            IBM_IAM_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": settings.WATSONX_API_KEY,
            }
        )

        if response.status_code != 200:
            logger.error(f"IBM IAM token error: {response.text}")
            raise Exception(f"Failed to get IBM token: {response.status_code} — {response.text}")

        data = response.json()
        _token_cache["access_token"] = data["access_token"]
        _token_cache["expires_at"] = now + data.get("expires_in", 3600)

        logger.info("✅ IBM IAM token refreshed successfully")
        return _token_cache["access_token"]