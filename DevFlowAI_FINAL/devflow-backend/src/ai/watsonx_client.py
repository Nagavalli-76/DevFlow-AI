# src/ai/watsonx_client.py
# ─────────────────────────────────────────────
# IBM watsonx.ai Client — Core AI Engine
# Handles all communication with IBM BOB (watsonx)
# Supports: normal chat, streaming, code analysis
# ─────────────────────────────────────────────

import httpx
import json
import logging
from typing import List, AsyncGenerator, Optional
from src.config.settings import settings
from src.ai.ibm_token import get_ibm_access_token

logger = logging.getLogger(__name__)

# ─── WATSONX API ENDPOINT ───
WATSONX_CHAT_URL = "{base}/ml/v1/text/chat?version=2024-05-31"
WATSONX_GENERATE_URL = "{base}/ml/v1/text/generation?version=2024-05-31"

# ─── IBM BOB SYSTEM PROMPT ───
IBM_BOB_SYSTEM_PROMPT = """You are IBM BOB, an expert AI coding assistant built into DevFlow AI — 
an IBM BOB Hackathon project. You are powered by IBM watsonx.ai.

Your expertise:
- Code review and analysis
- Debugging and error fixing  
- Architecture design
- Security best practices
- Performance optimization
- Writing clean, production-ready code

Guidelines:
- Always give clear, structured answers
- Provide code examples when helpful
- Explain your reasoning step by step
- Be concise but thorough
- Format code blocks properly

You are helping developers build better software faster."""


class WatsonxClient:
    """
    IBM watsonx.ai API Client for DevFlow AI
    
    Usage:
        client = WatsonxClient()
        response = await client.chat([{"role": "user", "content": "Hello"}])
    """

    def __init__(self):
        self.base_url = settings.WATSONX_URL
        self.model_id = settings.AI_MODEL
        self.project_id = settings.WATSONX_PROJECT_ID

    def _build_messages(self, messages: List[dict], system_prompt: Optional[str] = None) -> List[dict]:
        """Build message list with system prompt"""
        full_messages = []

        # Add system prompt at the beginning
        prompt = system_prompt or IBM_BOB_SYSTEM_PROMPT
        full_messages.append({"role": "system", "content": prompt})

        # Add conversation history
        for msg in messages:
            full_messages.append({
                "role": msg["role"],   # user / assistant
                "content": msg["content"]
            })

        return full_messages

    # ─── NORMAL CHAT (returns full response at once) ───
    async def chat(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> dict:
        """
        Send messages to IBM BOB and get full response
        
        Returns:
            {
                "content": "AI response text",
                "tokens_used": 150,
                "model": "meta-llama/..."
            }
        """
        token = await get_ibm_access_token()
        url = WATSONX_CHAT_URL.format(base=self.base_url)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        body = {
            "model_id": self.model_id,
            "project_id": self.project_id,
            "messages": self._build_messages(messages, system_prompt),
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9,
                "repetition_penalty": 1.1,
            }
        }

        logger.info(f"Calling IBM watsonx — model: {self.model_id}")

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=body)

            if response.status_code != 200:
                logger.error(f"watsonx error {response.status_code}: {response.text}")
                raise Exception(f"IBM watsonx error: {response.status_code}")

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("total_tokens", 0)

            logger.info(f"✅ IBM BOB responded — tokens used: {tokens}")

            return {
                "content": content,
                "tokens_used": tokens,
                "model": self.model_id,
            }

    # ─── STREAMING CHAT (yields chunks as they arrive) ───
    async def chat_stream(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from IBM BOB word by word
        Used for real-time typing effect in frontend
        
        Yields: text chunks as they stream in
        """
        token = await get_ibm_access_token()
        url = WATSONX_CHAT_URL.format(base=self.base_url)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        body = {
            "model_id": self.model_id,
            "project_id": self.project_id,
            "messages": self._build_messages(messages, system_prompt),
            "stream": True,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", url, headers=headers, json=body) as resp:
                if resp.status_code != 200:
                    raise Exception(f"IBM stream error: {resp.status_code}")

                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data_str)
                            delta = chunk_data["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except json.JSONDecodeError:
                            continue

    # ─── CODE ANALYSIS (specialized for code review) ───
    async def analyze_code(self, code: str, language: str = "python") -> dict:
        """
        Specialized code analysis using IBM BOB
        Checks for bugs, security issues, improvements
        """
        system = """You are IBM BOB, an expert code reviewer. 
Analyze the provided code and give structured feedback covering:
1. Bugs or errors found
2. Security vulnerabilities  
3. Performance improvements
4. Code quality suggestions
5. Overall score (1-10)

Format your response clearly with sections."""

        messages = [{
            "role": "user",
            "content": f"Please analyze this {language} code:\n\n```{language}\n{code}\n```"
        }]

        return await self.chat(messages, system_prompt=system, max_tokens=2048)

    # ─── GENERATE CODE (write new code) ───
    async def generate_code(self, prompt: str, language: str = "python") -> dict:
        """Generate new code based on description"""
        system = f"""You are IBM BOB, an expert {language} developer.
Generate clean, production-ready {language} code.
Always include:
- Proper error handling
- Comments explaining the logic
- Type hints (if applicable)
- Example usage"""

        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, system_prompt=system, max_tokens=2048)

    # ─── EXPLAIN CODE ───
    async def explain_code(self, code: str) -> dict:
        """Explain what a piece of code does"""
        messages = [{
            "role": "user",
            "content": f"Explain this code in simple terms:\n\n```\n{code}\n```"
        }]
        return await self.chat(messages, max_tokens=1024)

    # ─── FIX BUG ───
    async def fix_bug(self, code: str, error_message: str) -> dict:
        """Fix a bug given code and error message"""
        messages = [{
            "role": "user",
            "content": f"Fix this bug:\n\nError: {error_message}\n\nCode:\n```\n{code}\n```\n\nProvide the fixed code with explanation."
        }]
        return await self.chat(messages, max_tokens=2048)


# ─── SINGLETON INSTANCE ───
watsonx = WatsonxClient()