# app/common/ai_client.py
"""
Simplified, robust AI client wrapper for OpenRouter.
- Returns plain text from chat() always.
- Handles missing API key or missing OpenRouter SDK gracefully.
- Minimal surface area for the rest of the app.
"""

import os
import logging
from typing import List, Dict, Any, Union

# load env if you use dotenv in your project; safe to call even if .env missing
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
_logger = logging.getLogger(__name__)

# Try to import OpenRouter lazily — keep module import-safe even if SDK missing
try:
    from openrouter import OpenRouter   # type: ignore
    _HAS_OPENROUTER = True
except Exception:
    _HAS_OPENROUTER = False
    _logger.debug("openrouter SDK not available; AI calls will error unless provided a substitute.")


class AIClient:
    def __init__(self, api_key: str = API_KEY):
        if not api_key:
            raise ValueError("OpenRouter API key missing. Set OPENROUTER_API_KEY in environment or .env")
        if not _HAS_OPENROUTER:
            raise RuntimeError("openrouter SDK is not installed. Install it or provide a mock.")
        self.api_key = api_key

    def chat(self,
             messages: Union[str, List[Dict[str, str]]],
             model: str = "gpt-4o-mini",
             max_tokens: int = 1024,
             temperature: float = 0.2,
             **kwargs) -> str:
        """
        Send chat-like messages to the model and return assistant text.
        - messages: either a plain string prompt, or list of {"role":..., "content":...}
        - always returns a plain string (never complex objects)
        """
        # Normalize messages: if a string provided, wrap as system/user pair
        if isinstance(messages, str):
            payload = [{"role": "user", "content": messages}]
        else:
            payload = messages

        try:
            with OpenRouter(api_key=self.api_key) as client:
                resp = client.beta.responses.send(
                    model=model,
                    input=payload,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )

                # Collect textual pieces defensively
                out_text = ""

                for item in getattr(resp, "output", []) or []:
                    # Typical block: item.type == "message"
                    item_type = getattr(item, "type", None)
                    content = getattr(item, "content", None)
                    if content is None:
                        continue

                    # content can be a list of blocks or a string
                    if isinstance(content, list):
                        for block in content:
                            # block may be an object with attributes, or dict
                            if hasattr(block, "type") and getattr(block, "type", None) in ("output_text", "message_text", "text"):
                                out_text += getattr(block, "text", "") or ""
                            elif isinstance(block, dict):
                                out_text += block.get("text", "") or block.get("content", "") or ""
                            else:
                                # fallback: str()
                                out_text += str(block)
                    elif isinstance(content, str):
                        out_text += content
                    elif isinstance(content, dict):
                        # sometimes content is a dict with nested text
                        out_text += content.get("text", "") or content.get("content", "") or ""
                    else:
                        out_text += str(content)

                return out_text.strip()

        except Exception as e:
            # keep error short and deterministic for UI
            _logger.exception("AI chat call failed")
            return f"[AI error: {str(e)}]"


# singleton convenience
_ai_client = None


def get_ai_client() -> AIClient:
    """
    Return a module-level singleton AIClient instance.
    Raises a helpful error if OpenRouter or API key missing.
    """
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client
