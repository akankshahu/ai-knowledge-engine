import os
from typing import AsyncGenerator
import json

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai, anthropic, or mock
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")


async def stream_completion(prompt: str, max_tokens: int = 512) -> AsyncGenerator[str, None]:
    """
    Stream LLM response token-by-token.
    
    For MVP, yield mock tokens. In production, integrate real provider:
    - OpenAI: use streaming=True with SSE
    - Anthropic: use streaming.ContentBlockDelta events
    """
    if LLM_PROVIDER == "mock":
        # Mock response for testing
        mock_response = "Based on the context provided, the system is designed for semantic search and retrieval."
        for word in mock_response.split():
            yield word + " "
    else:
        # Placeholder for real provider integration
        yield "LLM integration pending... "


def format_stream_event(chunk: str) -> str:
    """Format chunk for SSE (Server-Sent Events)."""
    data = {"content": chunk}
    return f"data: {json.dumps(data)}\n\n"
