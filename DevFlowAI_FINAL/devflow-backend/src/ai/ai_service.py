# src/ai/ai_service.py
# ─────────────────────────────────────────────
# AI Service Layer
# Sits between API routes and watsonx client
# Handles: caching, logging, token tracking, fallback
# ─────────────────────────────────────────────

import hashlib
import json
import logging
from typing import List, Optional, AsyncGenerator
from src.ai.watsonx_client import watsonx
from src.config.redis import cache
from src.config.settings import settings

logger = logging.getLogger(__name__)


class AIService:
    """
    Main AI service for DevFlow AI
    
    All AI features go through here:
    - Chat with IBM BOB
    - Code analysis
    - Code generation
    - Bug fixing
    - Caching responses to save coins
    """

    # ─── HASH HELPER (for caching) ───
    def _hash_messages(self, messages: List[dict]) -> str:
        """Create unique hash of messages for cache key"""
        return hashlib.md5(json.dumps(messages, sort_keys=True).encode()).hexdigest()

    # ─── MOCK RESPONSE (when API key not set) ───
    async def _mock_response(self, message: str) -> dict:
        """
        Returns fake response during development
        So you don't waste BOB coins while testing!
        """
        import asyncio
        await asyncio.sleep(0.8)  # simulate API delay
        return {
            "content": f"[MOCK - IBM BOB] I've analyzed your query: '{message[:80]}...'\n\n"
                       f"**Note:** This is a mock response. Add your WATSONX_API_KEY in .env to get real IBM BOB responses.\n\n"
                       f"Real IBM BOB will provide:\n"
                       f"- Detailed code analysis\n"
                       f"- Security recommendations\n"
                       f"- Performance improvements\n"
                       f"- Production-ready code examples",
            "tokens_used": 0,
            "model": "mock-mode",
            "cached": False,
        }

    # ─── MAIN CHAT (with caching) ───
    async def chat(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None,
        use_cache: bool = True,
        max_tokens: int = 1024,
    ) -> dict:
        """
        Chat with IBM BOB
        
        1. Check Redis cache first (save coins!)
        2. If not cached → call IBM watsonx
        3. Save response to cache
        4. Return response
        """
        # Generate cache key upfront
        cache_key = self._hash_messages(messages) if use_cache else None
        
        # Check cache first
        if use_cache and cache_key:
            cached = await cache.get_cached_ai_response(cache_key)
            if cached:
                logger.info("Cache HIT — returning cached AI response (0 coins used)")
                return {
                    "content": cached,
                    "tokens_used": 0,
                    "model": settings.AI_MODEL,
                    "cached": True,
                }

        # Use mock if no API key (saves coins during development)
        if not settings.WATSONX_API_KEY:
            logger.warning("WATSONX_API_KEY not set — using mock response")
            last_msg = messages[-1]["content"] if messages else ""
            return await self._mock_response(last_msg)

        # Call real IBM BOB
        try:
            result = await watsonx.chat(messages, system_prompt=system_prompt, max_tokens=max_tokens)
            result["cached"] = False

            # Cache the response (save future coin usage)
            if use_cache and cache_key:
                await cache.cache_ai_response(cache_key, result["content"], ttl=1800)
                logger.info(f"Response cached — tokens used: {result['tokens_used']}")

            return result

        except Exception as e:
            logger.error(f"IBM watsonx error: {e}")
            raise Exception(f"AI service error: {str(e)}")

    # ─── STREAMING CHAT ───
    async def chat_stream(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream response from IBM BOB"""

        if not settings.WATSONX_API_KEY:
            # Mock streaming
            import asyncio
            mock = "This is a mock streaming response. Add WATSONX_API_KEY to get real IBM BOB streaming."
            for word in mock.split():
                yield word + " "
                await asyncio.sleep(0.05)
            return

        async for chunk in watsonx.chat_stream(messages, system_prompt=system_prompt):
            yield chunk

    # ─── CODE ANALYSIS ───
    async def analyze_code(self, code: str, language: str = "python") -> dict:
        """Analyze code for bugs, security, performance"""

        if not settings.WATSONX_API_KEY:
            return await self._mock_response(f"analyze {language} code")

        cache_key = f"code_analysis:{hashlib.md5(code.encode()).hexdigest()}"
        cached = await cache.get_cached_ai_response(cache_key)
        if cached:
            return {"content": cached, "cached": True, "tokens_used": 0, "model": settings.AI_MODEL}

        result = await watsonx.analyze_code(code, language)
        await cache.cache_ai_response(cache_key, result["content"], ttl=3600)
        return result

    # ─── CODE GENERATION ───
    async def generate_code(self, prompt: str, language: str = "python") -> dict:
        """Generate code from description"""

        if not settings.WATSONX_API_KEY:
            return await self._mock_response(f"generate {language}: {prompt}")

        return await watsonx.generate_code(prompt, language)

    # ─── BUG FIXING ───
    async def fix_bug(self, code: str, error: str) -> dict:
        """Fix a bug in code"""

        if not settings.WATSONX_API_KEY:
            return await self._mock_response(f"fix bug: {error}")

        return await watsonx.fix_bug(code, error)

    # ─── CODE EXPLANATION ───
    async def explain_code(self, code: str) -> dict:
        """Explain code in simple terms"""

        if not settings.WATSONX_API_KEY:
            return await self._mock_response(f"explain code")

        cache_key = f"explain:{hashlib.md5(code.encode()).hexdigest()}"
        cached = await cache.get_cached_ai_response(cache_key)
        if cached:
            return {"content": cached, "cached": True, "tokens_used": 0, "model": settings.AI_MODEL}

        result = await watsonx.explain_code(code)
        await cache.cache_ai_response(cache_key, result["content"], ttl=3600)
        return result


# ─── SINGLETON ───
ai_service = AIService()