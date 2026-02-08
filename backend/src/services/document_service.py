"""Document processing service for text extraction."""

import uuid
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import chardet
import fitz  # PyMuPDF
import structlog
from docx import Document as DocxDocument

from src.core import DocumentProcessingError, Settings
from src.tools import VisionTool

logger = structlog.get_logger()


class DocumentService:
    """Service for processing and extracting text from documents."""

    SUPPORTED_TEXT_TYPES = {".txt", ".md", ".csv", ".json", ".py", ".js", ".ts", ".html", ".css"}
    SUPPORTED_DOC_TYPES = {".docx"}
    SUPPORTED_PDF_TYPES = {".pdf"}
    SUPPORTED_IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

    def __init__(self, settings: Settings | None = None):
        """Initialize document service.

        Args:
            settings: Application settings.
        """
        self._settings = settings or Settings()
        self._vision_tool = VisionTool(self._settings)

    def _detect_encoding(self, content: bytes) -> str:
        """Detect text encoding.

        Args:
            content: Raw bytes content.

        Returns:
            Detected encoding name.
        """
        result = chardet.detect(content)
        return result.get("encoding") or "utf-8"

    def _extract_text_file(self, content: bytes, filename: str) -> str:
        """Extract text from a plain text file.

        Args:
            content: Raw file bytes.
            filename: Original filename.

        Returns:
            Extracted text.
        """
        encoding = self._detect_encoding(content)
        try:
            return content.decode(encoding, errors="replace")
        except Exception as e:
            logger.error("text_extraction_failed", filename=filename, error=str(e))
            raise DocumentProcessingError(f"Failed to extract text from {filename}: {e}") from e

    def _extract_docx(self, content: bytes, filename: str) -> str:
        """Extract text from a DOCX file.

        Args:
            content: Raw file bytes.
            filename: Original filename.

        Returns:
            Extracted text.
        """
        try:
            doc = DocxDocument(BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            logger.error("docx_extraction_failed", filename=filename, error=str(e))
            raise DocumentProcessingError(f"Failed to extract text from DOCX {filename}: {e}") from e

    def _extract_pdf(self, content: bytes, filename: str) -> str:
        """Extract text from a PDF file.

        Args:
            content: Raw file bytes.
            filename: Original filename.

        Returns:
            Extracted text.
        """
        try:
            text_parts = []
            with fitz.open(stream=content, filetype="pdf") as pdf:
                for page_num, page in enumerate(pdf, 1):
                    text = page.get_text()
                    if text.strip():
                        text_parts.append(f"[Page {page_num}]\n{text}")

            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error("pdf_extraction_failed", filename=filename, error=str(e))
            raise DocumentProcessingError(f"Failed to extract text from PDF {filename}: {e}") from e

    async def _extract_image(self, content: bytes, filename: str) -> str:
        """Extract text description from an image using vision model.

        Args:
            content: Raw file bytes.
            filename: Original filename.

        Returns:
            Generated caption/description.
        """
        # Save to temp file for vision tool
        temp_path = Path(f"/tmp/{uuid.uuid4()}_{filename}")
        try:
            temp_path.write_bytes(content)
            caption = await self._vision_tool.caption(temp_path)
            return f"[Image: {filename}]\n{caption}"
        except Exception as e:
            logger.error("image_caption_failed", filename=filename, error=str(e))
            raise DocumentProcessingError(f"Failed to process image {filename}: {e}") from e
        finally:
            temp_path.unlink(missing_ok=True)

    def get_document_type(self, filename: str) -> str:
        """Determine document type from filename.

        Args:
            filename: Original filename.

        Returns:
            Document type category: "text", "document", "pdf", or "image".
        """
        ext = Path(filename).suffix.lower()

        if ext in self.SUPPORTED_TEXT_TYPES:
            return "text"
        elif ext in self.SUPPORTED_DOC_TYPES:
            return "document"
        elif ext in self.SUPPORTED_PDF_TYPES:
            return "pdf"
        elif ext in self.SUPPORTED_IMAGE_TYPES:
            return "image"
        else:
            return "unknown"

    def is_supported(self, filename: str) -> bool:
        """Check if file type is supported.

        Args:
            filename: Original filename.

        Returns:
            True if supported, False otherwise.
        """
        ext = Path(filename).suffix.lower()
        return ext in (
            self.SUPPORTED_TEXT_TYPES
            | self.SUPPORTED_DOC_TYPES
            | self.SUPPORTED_PDF_TYPES
            | self.SUPPORTED_IMAGE_TYPES
        )

    async def extract(self, content: bytes, filename: str) -> tuple[str, str]:
        """Extract text from a document.

        Args:
            content: Raw file bytes.
            filename: Original filename.

        Returns:
            Tuple of (extracted_text, document_type).

        Raises:
            DocumentProcessingError: If extraction fails.
        """
        doc_type = self.get_document_type(filename)

        if not self.is_supported(filename):
            raise DocumentProcessingError(f"Unsupported file type: {filename}")

        logger.info("extracting_document", filename=filename, type=doc_type)

        if doc_type == "text":
            text = self._extract_text_file(content, filename)
        elif doc_type == "document":
            text = self._extract_docx(content, filename)
        elif doc_type == "pdf":
            text = self._extract_pdf(content, filename)
        elif doc_type == "image":
            text = await self._extract_image(content, filename)
        else:
            raise DocumentProcessingError(f"Unknown document type: {filename}")

        if not text or not text.strip():
            raise DocumentProcessingError(f"No text extracted from {filename}")

        logger.info(
            "document_extracted",
            filename=filename,
            type=doc_type,
            text_length=len(text),
        )

        return text, doc_type

    async def extract_from_upload(self, file: BinaryIO, filename: str) -> tuple[str, str]:
        """Extract text from an uploaded file.

        Args:
            file: File-like object.
            filename: Original filename.

        Returns:
            Tuple of (extracted_text, document_type).
        """
        content = file.read()
        return await self.extract(content, filename)
