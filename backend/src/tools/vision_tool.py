"""Vision tool for image captioning using Ollama Vision models."""

import base64
from io import BytesIO
from pathlib import Path

import structlog
from PIL import Image

from src.core import LLMError, Settings
from src.prompts import VISION_CAPTION_PROMPT

logger = structlog.get_logger()


class VisionTool:
    """Tool for generating captions from images using Ollama Vision models."""

    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

    def __init__(self, settings: Settings | None = None):
        """Initialize vision tool.

        Args:
            settings: Application settings.
        """
        self._settings = settings or Settings()

    def _encode_image(self, image_path: str | Path) -> str:
        """Encode image to base64.

        Args:
            image_path: Path to the image file.

        Returns:
            Base64 encoded image string.
        """
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _resize_if_needed(self, image_path: str | Path, max_size: int = 1024) -> str:
        """Resize image if too large while maintaining aspect ratio.

        Args:
            image_path: Path to the image file.
            max_size: Maximum dimension (width or height).

        Returns:
            Path to resized image (or original if no resize needed).
        """
        with Image.open(image_path) as img:
            width, height = img.size
            if width <= max_size and height <= max_size:
                return str(image_path)

            # Calculate new dimensions
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))

            # Resize and save to temp
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            temp_path = f"{image_path}.resized.jpg"
            resized.convert("RGB").save(temp_path, "JPEG", quality=85)

            return temp_path

    async def caption(self, image_path: str | Path) -> str:
        """Generate a text caption for an image.

        Args:
            image_path: Path to the image file.

        Returns:
            Generated caption text.

        Raises:
            LLMError: If captioning fails.
        """
        import ollama

        image_path = Path(image_path)

        if not image_path.exists():
            raise LLMError(f"Image not found: {image_path}")

        if image_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise LLMError(f"Unsupported image format: {image_path.suffix}")

        try:
            # Resize if needed
            resized_path = self._resize_if_needed(image_path)

            # Encode image
            image_data = self._encode_image(resized_path)

            # Clean up temp file if created
            if resized_path != str(image_path):
                Path(resized_path).unlink(missing_ok=True)

            # Call Ollama vision model
            client = ollama.AsyncClient(host=self._settings.ollama_base_url)

            response = await client.chat(
                model=self._settings.ollama_vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": VISION_CAPTION_PROMPT,
                        "images": [image_data],
                    },
                ],
            )

            caption = response.message.content.strip()
            logger.debug("image_captioned", path=str(image_path), caption_length=len(caption))

            return caption

        except Exception as e:
            logger.error("vision_caption_failed", error=str(e), path=str(image_path))
            raise LLMError(f"Failed to caption image: {e}") from e

    async def is_available(self) -> bool:
        """Check if vision model is available.

        Returns:
            True if the vision model can be used.
        """
        import ollama

        try:
            client = ollama.AsyncClient(host=self._settings.ollama_base_url)
            models = await client.list()
            model_names = [m.model for m in models.models] if models.models else []

            # Check if vision model is available
            return any(self._settings.ollama_vision_model in name for name in model_names)
        except Exception:
            return False
