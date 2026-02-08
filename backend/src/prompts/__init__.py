"""Prompt management module."""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt from the prompts directory.

    Args:
        name: Prompt file name without extension.

    Returns:
        The prompt text content.
    """
    prompt_path = _PROMPTS_DIR / f"{name}.md"
    return prompt_path.read_text(encoding="utf-8")


RAG_SYSTEM_PROMPT = load_prompt("rag_system")
VISION_CAPTION_PROMPT = load_prompt("vision_caption")
