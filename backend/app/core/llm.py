# =============================================================================
# core/llm.py — LLM Provider Wrapper (Pollinations API)
# =============================================================================
# WHAT IS THIS?
# A clean wrapper around the Pollinations API for text generation.
# Pollinations is FREE and requires NO API key — perfect for local development.
#
# DESIGN PATTERN: Provider-Agnostic Interface
# We define a simple `generate()` function that any part of the app can use.
# If you later switch to OpenAI or Anthropic, you only change THIS file —
# the rest of the codebase stays untouched.
#
# HOW POLLINATIONS WORKS:
# It's a simple HTTP API. You send a prompt, you get text back.
# URL: https://text.pollinations.ai/{encoded_prompt}
# =============================================================================

import httpx
import json
from typing import Optional
from urllib.parse import quote

from app.config import settings


class LLMProvider:
    """
    LLM provider that talks to the Pollinations API.
    
    Usage:
        llm = LLMProvider()
        response = await llm.generate("Write a cover letter for a Python dev role")
        print(response)  # The generated text
    """
    
    def __init__(self):
        self.base_url = settings.POLLINATIONS_BASE_URL
        # httpx is like `requests` but supports async/await
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "openai",
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text using Pollinations API.
        
        Args:
            prompt: The user's prompt / question
            system_prompt: Optional system message to set the AI's behavior
            model: Which model to use (default: "openai")
            temperature: Creativity level (0=precise, 1=creative)
        
        Returns:
            The generated text response
        """
        
        # Build the full prompt
        full_prompt = ""
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        else:
            full_prompt = prompt
        
        # URL-encode the prompt (spaces → %20, etc.)
        encoded_prompt = quote(full_prompt)
        
        # Call the Pollinations API
        url = f"{self.base_url}/{encoded_prompt}"
        params = {
            "model": model,
            "temperature": str(temperature),
            "json": "true",  # Request structured output when possible
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()  # Raise exception for 4xx/5xx status codes
            return response.text
            
        except httpx.HTTPStatusError as e:
            print(f"[ERR] LLM API error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"[ERR] LLM connection error: {e}")
            raise
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> dict:
        """
        Generate a JSON response from the LLM.
        
        Useful for structured outputs like:
        - Resume tailoring (get back modified sections as JSON)
        - Job scoring (get back {"score": 85, "reasoning": "..."})
        """
        
        json_system = (system_prompt or "") + (
            "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no explanations."
        )
        
        response_text = await self.generate(
            prompt=prompt,
            system_prompt=json_system,
            temperature=0.3,  # Lower temperature for structured output
        )
        
        # Try to parse JSON from the response
        # Sometimes the LLM wraps it in ```json ... ```, so we handle that
        text = response_text.strip()
        if text.startswith("```"):
            # Remove markdown code fences
            text = text.split("\n", 1)[1]  # Remove first line (```json)
            text = text.rsplit("```", 1)[0]  # Remove last ``` 
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print(f"[WARN] Failed to parse LLM JSON response: {text[:200]}...")
            return {"error": "Failed to parse JSON response", "raw": text}
    
    async def close(self):
        """Close the HTTP client. Call this on app shutdown."""
        await self.client.aclose()


# Singleton instance — import this everywhere
# Usage: from app.core.llm import llm_provider
llm_provider = LLMProvider()
