"""Dispatcher for selecting content extractor tools based on file metadata."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from auto_file.core.detector import FileMetadata

logger = logging.getLogger(__name__)

CANDIDATE_TOOLS: list[str] = [
    "pdf_extractor",
    "image_extractor",
    "text_extractor",
    "audio_extractor",
    "fallback_extractor",
]

IMAGE_EXTENSIONS: set[str] = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".svg",
    ".heic",
    ".heif",
    ".ico",
    ".raw",
    ".cr2",
    ".nef",
    ".arw",
}

AUDIO_EXTENSIONS: set[str] = {
    ".mp3",
    ".wav",
    ".flac",
    ".ogg",
    ".m4a",
    ".aac",
    ".wma",
    ".aiff",
    ".alac",
    ".opus",
    ".mid",
    ".midi",
}

TEXT_EXTENSIONS: set[str] = {
    ".txt",
    ".csv",
    ".tsv",
    ".md",
    ".markdown",
    ".json",
    ".xml",
    ".html",
    ".htm",
    ".yaml",
    ".yml",
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".css",
    ".scss",
    ".sh",
    ".bash",
    ".zsh",
    ".log",
    ".rst",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".sql",
    ".tex",
    ".rtf",
    ".env",
}

TEXT_MIME_TYPES: set[str] = {
    "application/json",
    "application/xml",
    "application/javascript",
    "application/x-yaml",
    "application/yaml",
    "application/toml",
    "application/x-sh",
    "application/csv",
    "application/rtf",
    "application/sql",
    "application/x-python",
    "application/x-python-code",
}


def _create_onnx_session(model_path: Path | str) -> Any:
    """Create an ONNX runtime inference session.

    Separated into a standalone helper for test mockability and error handling.
    """
    import onnxruntime as ort  # type: ignore[import-untyped]

    return ort.InferenceSession(str(model_path))


class LayaDispatcher:
    """Dispatches content extractor tools based on file metadata.

    Supports zero-drift ONNX decision ranking when model weights are provided,
    and falls back to deterministic MIME/extension evaluation rules for
    robust offline execution.
    """

    def __init__(self, model_path: Path | str | None = None) -> None:
        self.default_model_path = Path(model_path) if model_path is not None else None

    def dispatch_tool(
        self,
        metadata: FileMetadata,
        model_path: Path | str | None = None,
    ) -> str:
        """Choose the extractor tool identifier for the given file metadata.

        Args:
            metadata: FileMetadata instance for the incoming file.
            model_path: Optional path to Laya ONNX decision model weights.
                If omitted, uses the dispatcher default model path.

        Returns:
            One of: 'pdf_extractor', 'image_extractor', 'text_extractor',
            'audio_extractor', or 'fallback_extractor'.
        """
        active_model = model_path if model_path is not None else self.default_model_path

        # Attempt ONNX model prediction when weights path is present
        if active_model is not None:
            predicted_tool = self._predict_onnx(metadata, active_model)
            if predicted_tool is not None:
                return predicted_tool

        # Deterministic fallback rules
        return self._dispatch_deterministic(metadata)

    def dispatch(
        self,
        metadata: FileMetadata,
        model_path: Path | str | None = None,
    ) -> str:
        """Alias for dispatch_tool."""
        return self.dispatch_tool(metadata, model_path=model_path)

    def _predict_onnx(
        self,
        metadata: FileMetadata,
        model_path: Path | str,
    ) -> str | None:
        """Run Laya ONNX session prediction if available."""
        try:
            session = _create_onnx_session(model_path)
            inputs = session.get_inputs()
            input_names = [inp.name for inp in inputs] if inputs else ["input"]

            prompt_text = (
                f"mime_type: {metadata.mime_type}, "
                f"extension: {metadata.extension}, "
                f"size_bytes: {metadata.size_bytes}"
            )

            feed: dict[str, Any] = {}
            for name in input_names:
                feed[name] = [prompt_text]

            outputs = session.run(None, feed)
            if not outputs:
                return None

            raw_out = outputs[0]
            if hasattr(raw_out, "tolist"):
                raw_out = raw_out.tolist()

            # Handle sequence of logits or scores
            if isinstance(raw_out, (list, tuple)) and len(raw_out) > 0:
                first_item = raw_out[0]
                if isinstance(first_item, (list, tuple)):
                    scores = list(first_item)
                else:
                    scores = list(raw_out)

                if scores and len(scores) == len(CANDIDATE_TOOLS):
                    max_idx = max(range(len(scores)), key=lambda i: scores[i])
                    return CANDIDATE_TOOLS[max_idx]

            # Handle direct string output
            if isinstance(raw_out, str) and raw_out in CANDIDATE_TOOLS:
                return raw_out

            return None
        except Exception as exc:
            logger.debug("ONNX dispatch inference failed, falling back: %s", exc)
            return None

    def _dispatch_deterministic(self, metadata: FileMetadata) -> str:
        """Deterministic MIME and extension inspection rules."""
        mime = (metadata.mime_type or "").strip().lower()
        ext = (metadata.extension or "").strip().lower()

        # 1. PDF files
        if mime in {"application/pdf", "application/x-pdf", "application/acrobat"} or ext == ".pdf":
            return "pdf_extractor"

        # 2. Image files
        if mime.startswith("image/") or ext in IMAGE_EXTENSIONS:
            return "image_extractor"

        # 3. Audio files
        if mime.startswith("audio/") or ext in AUDIO_EXTENSIONS:
            return "audio_extractor"

        # 4. Text and structured documents
        if mime.startswith("text/") or mime in TEXT_MIME_TYPES or ext in TEXT_EXTENSIONS:
            return "text_extractor"

        # 5. Fallback for unclassified binaries and unknown types
        return "fallback_extractor"


def dispatch_tool(
    metadata: FileMetadata,
    model_path: Path | str | None = None,
) -> str:
    """Convenience top-level function to dispatch extractor tool."""
    return LayaDispatcher(model_path=model_path).dispatch_tool(metadata, model_path=model_path)
