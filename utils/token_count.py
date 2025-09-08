import math
from typing import Optional


def _heuristic_token_count(text: str) -> int:
    """Simple heuristic: ~4 characters per token on average."""
    if not text:
        return 0
    # Use UTF-8 length as a closer proxy than python char count for multilingual text
    approx_tokens = math.ceil(len(text) / 4)
    return max(approx_tokens, 0)


def count_tokens(text: str, model: Optional[str] = None) -> int:
    """
    Return token estimate for given text.

    Keep it simple: use a heuristic by default to avoid extra dependencies.
    If a provider-specific tokenizer is available in the environment, you may
    extend this to use it, but it's optional and not required.
    """
    # Placeholder for future model-specific integrations.
    # For now, always use heuristic to keep implementation lightweight.
    return _heuristic_token_count(text or "")


