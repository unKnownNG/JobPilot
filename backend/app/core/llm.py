# =============================================================================
# core/llm.py — LLM Provider (Pollinations API)
# =============================================================================
# Two modes:
#   - With API key (Seed tier): Uses gen.pollinations.ai (OpenAI-compatible, fast)
#   - Without API key (free):   Uses text.pollinations.ai (rate-limited)
# =============================================================================

import httpx
import json
from typing import Optional

from app.config import settings


class LLMProvider:
    """
    LLM provider using Pollinations API.
    Automatically picks the right endpoint based on whether you have an API key.
    """
    
    def __init__(self):
        self.api_key = getattr(settings, "POLLINATIONS_API_KEY", "") or ""
        self.has_key = bool(self.api_key.strip())
        self.client = httpx.AsyncClient(timeout=120.0)
        
        if self.has_key:
            self.base_url = "https://gen.pollinations.ai/v1"
            print("[LLM] Using Seed tier (gen.pollinations.ai)")
        else:
            self.base_url = "https://text.pollinations.ai/openai"
            print("[LLM] Using free tier (text.pollinations.ai)")
    
    async def _chat_completion(
        self,
        messages: list[dict],
        model: str = "openai",
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str:
        """Make a chat completion request to the Pollinations API."""
        headers = {"Content-Type": "application/json"}
        if self.has_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        body: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        
        url = f"{self.base_url}/chat/completions"
        
        try:
            response = await self.client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            print(f"[ERR] LLM API {e.response.status_code}: {e.response.text[:200]}")
            raise
        except httpx.RequestError as e:
            print(f"[ERR] LLM connection error: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "openai",
        temperature: float = 0.7,
    ) -> str:
        """Generate text using Pollinations API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        return await self._chat_completion(messages, model, temperature)
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "openai",
    ) -> dict | list:
        """
        Generate a JSON response. Uses response_format: json_object when available.
        """
        json_system = (system_prompt or "") + "\nRespond ONLY with valid JSON. No markdown, no explanations."
        messages = [
            {"role": "system", "content": json_system},
            {"role": "user", "content": prompt},
        ]
        
        try:
            text = await self._chat_completion(
                messages, model, temperature=0.3, json_mode=True,
            )
            text = text.strip()
            
            # Clean markdown fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                text = text.rsplit("```", 1)[0]
            
            return json.loads(text)
            
        except json.JSONDecodeError:
            print(f"[WARN] Failed to parse LLM JSON: {text[:300]}...")
            return {"error": "Failed to parse JSON", "raw": text}
        except Exception as e:
            print(f"[ERR] generate_json failed: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Singleton instance
llm_provider = LLMProvider()
