"""Multimodal document understander using Gemma 4 E2B with JSON parsing and fallback."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
import json
import logging
from pathlib import Path
import re
from typing import Any

from auto_file.core.extractors.base import ExtractedContent
from auto_file.core.naming import sanitize_slug

logger = logging.getLogger(__name__)

CANONICAL_PEOPLE: list[str] = ["Alpha", "Bravo", "Charlie", "Delta", "Echo"]

COMMON_ORGANIZATIONS: list[str] = [
    "Chase",
    "Chase Bank",
    "Wells Fargo",
    "Bank of America",
    "Citibank",
    "Capital One",
    "US Bank",
    "Fidelity",
    "Vanguard",
    "Schwab",
    "IRS",
    "US Treasury",
    "Social Security",
    "Pacific Power",
    "Home Depot",
    "Costco",
    "Amazon",
    "Walmart",
    "Target",
]

MONTH_NAMES: dict[str, int] = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}


@dataclass
class UnderstandingResult:
    """Structured understanding of a file produced by the understander stage.

    Attributes:
        content_date: Extracted document date normalized to YYYY-MM-DD or None.
        file_description: Descriptive snake_case slug (max 64 chars).
        detected_entities: List of named people, organizations, or accounts.
        category_hint: High-level classification hint for taxonomy routing.
        summary: Concise single-sentence summary of the content.
    """

    content_date: str | None = None
    file_description: str = ""
    detected_entities: list[str] = field(default_factory=list)
    category_hint: str = ""
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert result to a standard dictionary."""
        return asdict(self)


def normalize_date_string(date_input: Any) -> str | None:
    """Normalize a raw date string or object into ISO format (YYYY-MM-DD).

    Returns None if date is missing, unparseable, or invalid on the calendar.
    """
    if date_input is None:
        return None

    if isinstance(date_input, (datetime, date)):
        return date_input.strftime("%Y-%m-%d")

    if not isinstance(date_input, str):
        return None

    raw = date_input.strip()
    if not raw or raw.lower() in {"none", "null", "unknown", "n/a", "undefined"}:
        return None

    # Strip ISO timestamp time component if present (e.g. 2026-02-14T15:30:00Z)
    t_match = re.match(r"^(\d{4}[-/]\d{1,2}[-/]\d{1,2})[T\s]", raw)
    if t_match:
        raw = t_match.group(1)

    # 1. Try standard ISO format YYYY-MM-DD or YYYY/MM/DD or YYYY.MM.DD
    iso_match = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", raw)
    if iso_match:
        try:
            y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
            validated = date(y, m, d)
            return validated.strftime("%Y-%m-%d")
        except (ValueError, OverflowError):
            return None

    # 2. Try US format MM/DD/YYYY or MM-DD-YYYY
    us_match = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", raw)
    if us_match:
        try:
            m, d, y = int(us_match.group(1)), int(us_match.group(2)), int(us_match.group(3))
            validated = date(y, m, d)
            return validated.strftime("%Y-%m-%d")
        except (ValueError, OverflowError):
            return None

    # 3. Clean ordinal indicators: 1st -> 1, 2nd -> 2, 3rd -> 3, 4th -> 4
    cleaned = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", raw, flags=re.IGNORECASE)

    # Try textual dates: "Month DD, YYYY" or "Month DD YYYY"
    textual_match = re.match(
        r"^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$",
        cleaned.strip(),
    )
    if textual_match:
        month_name = textual_match.group(1).lower()
        if month_name in MONTH_NAMES:
            try:
                m = MONTH_NAMES[month_name]
                d = int(textual_match.group(2))
                y = int(textual_match.group(3))
                validated = date(y, m, d)
                return validated.strftime("%Y-%m-%d")
            except (ValueError, OverflowError):
                return None

    # Try "DD Month YYYY"
    dd_textual_match = re.match(
        r"^(\d{1,2})\s+([A-Za-z]+),?\s+(\d{4})$",
        cleaned.strip(),
    )
    if dd_textual_match:
        month_name = dd_textual_match.group(2).lower()
        if month_name in MONTH_NAMES:
            try:
                d = int(dd_textual_match.group(1))
                m = MONTH_NAMES[month_name]
                y = int(dd_textual_match.group(3))
                validated = date(y, m, d)
                return validated.strftime("%Y-%m-%d")
            except (ValueError, OverflowError):
                return None

    # 4. Standard strptime parsing fallback
    for fmt in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ):
        try:
            parsed = datetime.strptime(cleaned, fmt).date()
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def _extract_date_from_text(text: str) -> str | None:
    """Search arbitrary text for a full date with year."""
    if not text:
        return None

    # Search for YYYY-MM-DD or YYYY/MM/DD
    m1 = re.search(r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b", text)
    if m1:
        res = normalize_date_string(m1.group(0))
        if res:
            return res

    # Search for MM/DD/YYYY
    m2 = re.search(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b", text)
    if m2:
        res = normalize_date_string(m2.group(0))
        if res:
            return res

    # Search for Month DD, YYYY
    m3 = re.search(
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})\b",
        text,
        re.IGNORECASE,
    )
    if m3:
        res = normalize_date_string(m3.group(0))
        if res:
            return res

    return None


def _extract_entities_from_text(text: str) -> list[str]:
    """Extract known and recognized named entities from text."""
    found: list[str] = []
    text_lower = text.lower()

    # Match canonical people
    for person in CANONICAL_PEOPLE:
        pattern = rf"\b{re.escape(person.lower())}\b"
        if re.search(pattern, text_lower):
            if person not in found:
                found.append(person)

    # Match common organizations
    for org in COMMON_ORGANIZATIONS:
        pattern = rf"\b{re.escape(org.lower())}\b"
        if re.search(pattern, text_lower):
            if org not in found:
                found.append(org)

    return found


def _extract_category_hint_from_text(text: str) -> str:
    """Infer category hint from text keywords."""
    tl = text.lower()
    if (
        any(k in tl for k in ["bank statement", "account statement", "checking statement", "savings statement"])
        or ("statement" in tl and any(w in tl for w in ["bank", "account", "checking", "savings", "balance"]))
        or (any(w in tl for w in ["bank", "checking", "savings"]) and "balance" in tl)
    ):
        return "Bank Statement"
    if "invoice" in tl:
        return "Invoice"
    if any(k in tl for k in ["utility bill", "electric bill", "power bill", "water bill", "bill", "amount due", "due date"]):
        return "Bill"
    if any(k in tl for k in ["receipt", "reciept", "order total", "subtotal", "purchase receipt"]):
        return "Receipt"
    if any(
        k in tl
        for k in [
            "medical",
            "clinic",
            "hospital",
            "patient",
            "doctor",
            "dr.",
            "dr ",
            "physician",
            "prescription",
            "rx",
            "pediatric",
        ]
    ):
        return "Medical Record"
    if any(k in tl for k in ["tax", "w-2", "1099", "irs", "w2", "treasury"]):
        return "Tax Document"
    if any(k in tl for k in ["court", "lawsuit", "docket", "subpoena", "summons", "legal", "pleading"]):
        return "Legal"
    if any(k in tl for k in ["manual", "user guide", "operating instructions", "instruction manual"]):
        return "Manual"
    if any(k in tl for k in ["photo", "picture", "image"]):
        return "Photo"
    return "Document"


def _clean_json_string(raw: str) -> str:
    """Strip code fences, conversational framing, and trailing commas from JSON string."""
    cleaned = raw.strip()

    # Extract markdown code fence if present
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    else:
        # Search for outermost JSON object brackets
        bracket_match = re.search(r"(\{[\s\S]*\})", cleaned)
        if bracket_match:
            cleaned = bracket_match.group(1).strip()

    # Remove trailing commas before closing braces or brackets: , } -> }
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return cleaned


def parse_llm_json_response(raw_output: str) -> UnderstandingResult:
    """Parse raw LLM generation into a structured UnderstandingResult.

    Accepts markdown-fenced JSON, raw JSON strings, or conversational output.
    Provides robust regex and heuristic fallback if output is malformed or non-JSON.
    Never raises uncaught exceptions.
    """
    if not raw_output or not raw_output.strip():
        return UnderstandingResult(
            content_date=None,
            file_description="document",
            detected_entities=[],
            category_hint="Misc",
            summary="",
        )

    raw_text = raw_output.strip()

    # Attempt 1: Direct JSON parsing
    cleaned_candidate = _clean_json_string(raw_text)
    if cleaned_candidate.startswith("{") and cleaned_candidate.endswith("}"):
        try:
            data = json.loads(cleaned_candidate)
            if isinstance(data, dict):
                # Extract and normalize fields
                raw_date = data.get("content_date")
                norm_date = normalize_date_string(raw_date)

                # Description
                raw_desc = data.get("file_description") or ""
                desc_slug = sanitize_slug(str(raw_desc))
                if not desc_slug:
                    desc_slug = "document"

                # Entities
                raw_entities = data.get("detected_entities")
                entities: list[str] = []
                if isinstance(raw_entities, list):
                    for item in raw_entities:
                        if item is not None:
                            val = str(item).strip()
                            if val and val not in entities:
                                entities.append(val)
                elif isinstance(raw_entities, str) and raw_entities.strip():
                    for item in raw_entities.split(","):
                        val = item.strip()
                        if val and val not in entities:
                            entities.append(val)

                category_hint = str(data.get("category_hint") or "").strip()
                summary = str(data.get("summary") or "").strip()

                return UnderstandingResult(
                    content_date=norm_date,
                    file_description=desc_slug,
                    detected_entities=entities,
                    category_hint=category_hint,
                    summary=summary,
                )
        except Exception as exc:
            logger.debug("JSON decode failed (%s), proceeding to heuristic fallback", exc)

    # Attempt 2: Robust heuristic fallback for non-JSON or conversational output
    try:
        norm_date = _extract_date_from_text(raw_text)
        entities = _extract_entities_from_text(raw_text)
        category_hint = _extract_category_hint_from_text(raw_text)

        # Derive file description
        # Strip common conversational lead-in phrases
        cleaned_text = re.sub(
            r"^(i think this is an?|this is an?|here is an?|it looks like an?|summary:?)\s+",
            "",
            raw_text,
            flags=re.IGNORECASE,
        ).strip()

        # If entities and category found, construct concise phrase
        if entities and category_hint and category_hint != "Document":
            desc_seed = f"{entities[0]}_{category_hint.lower()}"
        elif category_hint and category_hint != "Document":
            desc_seed = category_hint.lower()
        else:
            # Slugify the first 4-5 words of the cleaned text
            words = cleaned_text.split()[:5]
            desc_seed = " ".join(words)

        file_description = sanitize_slug(desc_seed)
        if not file_description:
            file_description = "document"

        # Summary: first non-empty line or first sentence
        first_line = raw_text.splitlines()[0].strip()
        summary = first_line[:200]

        return UnderstandingResult(
            content_date=norm_date,
            file_description=file_description,
            detected_entities=entities,
            category_hint=category_hint,
            summary=summary,
        )
    except Exception as exc:
        logger.error("Heuristic understanding fallback encountered error: %s", exc)
        return UnderstandingResult(
            content_date=None,
            file_description="document",
            detected_entities=[],
            category_hint="Document",
            summary=raw_text[:100],
        )


def _load_transformer_model(
    model_id: str,
    device: str = "auto",
) -> tuple[Any, Any]:
    """Load Hugging Face transformers model and processor with 4-bit quantization.

    Falls back to CPU loading if CUDA is unavailable or out-of-memory.
    """
    import torch
    from transformers import AutoModelForVision2Seq, AutoProcessor, BitsAndBytesConfig

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    if torch.cuda.is_available() and device != "cpu":
        try:
            processor = AutoProcessor.from_pretrained(model_id)
            model = AutoModelForVision2Seq.from_pretrained(
                model_id,
                quantization_config=bnb_config,
                device_map=device,
            )
            return model, processor
        except (torch.cuda.OutOfMemoryError, RuntimeError, Exception) as exc:
            logger.warning("CUDA initialization failed or OOM (%s); falling back to CPU", exc)
            processor = AutoProcessor.from_pretrained(model_id)
            model = AutoModelForVision2Seq.from_pretrained(
                model_id,
                device_map="cpu",
                torch_dtype=torch.float32,
            )
            return model, processor
    else:
        processor = AutoProcessor.from_pretrained(model_id)
        model = AutoModelForVision2Seq.from_pretrained(
            model_id,
            device_map="cpu",
            torch_dtype=torch.float32,
        )
        return model, processor


class GemmaUnderstander:
    """Multimodal document understander using Gemma 4 E2B (google/gemma-4-E2B-it).

    Handles text documents and visual image inputs, extracting content dates,
    descriptive filename slugs, detected entities, category hints, and summaries.
    Supports lazy model loading, 4-bit BitsAndBytes quantization, CPU fallback
    on CUDA OOM, and a built-in deterministic/mock mode for fast offline testing.
    """

    def __init__(
        self,
        model_id: str = "google/gemma-4-E2B-it",
        mock: bool = False,
        device: str = "auto",
        mock_response: Any = None,
        mock_handler: Any = None,
    ) -> None:
        """Initialize Gemma understander.

        Args:
            model_id: Hugging Face model identifier (default: google/gemma-4-E2B-it).
            mock: If True, uses deterministic offline extraction without loading weights.
            device: Target device mapping ('auto', 'cuda', 'cpu').
            mock_response: Optional fixed response (UnderstandingResult, string, or callable).
            mock_handler: Optional custom callback for mock execution.
        """
        self.model_id = model_id
        self.mock = mock
        self.device = device
        self.mock_response = mock_response
        self.mock_handler = mock_handler

        self._model: Any = None
        self._processor: Any = None
        self._is_loaded: bool = False

    def generate_prompt(
        self,
        content: ExtractedContent,
        filename_hint: str | None = None,
    ) -> str:
        """Generate structured prompt instructing the model to produce target JSON."""
        parts: list[str] = [
            "You are an intelligent, precise local file organization assistant.",
            "Analyze the provided file content and extract 5 pieces of information:",
            "1. content_date: Primary document date in YYYY-MM-DD format (or null if no date).",
            "2. file_description: A concise, descriptive snake_case slug summarizing the file.",
            "3. detected_entities: Array of names of people, companies, banks, or accounts.",
            "4. category_hint: Document category (e.g. Bank Statement, Bill, Receipt, Medical Record, Tax Document, Manual, Photo, Misc).",
            "5. summary: A 1-sentence summary of the content.",
            "",
            "Respond with ONLY a JSON object formatted as:",
            "```json",
            "{",
            '  "content_date": "YYYY-MM-DD",',
            '  "file_description": "concise_slug",',
            '  "detected_entities": ["Entity1"],',
            '  "category_hint": "Category",',
            '  "summary": "1-sentence summary"',
            "}",
            "```",
            "",
        ]

        if filename_hint:
            parts.append(f"Original filename: {filename_hint}")

        if content.exif_date:
            parts.append(f"Embedded metadata date hint: {content.exif_date}")

        if content.metadata_hints:
            hints_str = ", ".join(f"{k}: {v}" for k, v in content.metadata_hints.items() if v)
            if hints_str:
                parts.append(f"Format metadata hints: {hints_str}")

        if content.text_content:
            text_snippet = content.text_content.strip()
            if len(text_snippet) > 4000:
                text_snippet = text_snippet[:4000] + "... [truncated]"
            parts.extend([
                "",
                "Document Text Content:",
                "---",
                text_snippet,
                "---",
            ])

        if content.image_content is not None:
            parts.extend([
                "",
                "[Visual image input provided: examine the document visual layout, headings, and stamps]",
            ])

        return "\n".join(parts)

    def _ensure_loaded(self) -> None:
        """Lazy load transformer model and processor."""
        if self._is_loaded or self.mock:
            return

        try:
            self._model, self._processor = _load_transformer_model(
                self.model_id,
                device=self.device,
            )
            self._is_loaded = True
        except Exception as exc:
            logger.warning(
                "Unable to load transformer model %s (%s); switching to mock/deterministic mode",
                self.model_id,
                exc,
            )
            self.mock = True
            self._is_loaded = False

    def understand(
        self,
        content: ExtractedContent,
        filename_hint: str | None = None,
    ) -> UnderstandingResult:
        """Analyze extracted content and return an UnderstandingResult."""
        # 1. Custom mock overrides
        if self.mock_response is not None:
            if isinstance(self.mock_response, UnderstandingResult):
                return self.mock_response
            if isinstance(self.mock_response, str):
                return parse_llm_json_response(self.mock_response)
            if callable(self.mock_response):
                res = self.mock_response(content, filename_hint)
                if isinstance(res, UnderstandingResult):
                    return res
                if isinstance(res, str):
                    return parse_llm_json_response(res)

        if self.mock_handler is not None and callable(self.mock_handler):
            res = self.mock_handler(content, filename_hint)
            if isinstance(res, UnderstandingResult):
                return res

        # 2. Mock / deterministic mode
        if self.mock:
            return self._understand_deterministic(content, filename_hint)

        # 3. Model loading
        self._ensure_loaded()
        if self.mock or self._model is None or self._processor is None:
            return self._understand_deterministic(content, filename_hint)

        # 4. Neural inference
        try:
            prompt = self.generate_prompt(content, filename_hint)
            processor = self._processor
            model = self._model

            # Multimodal vs text-only input tokenization
            if content.image_content is not None:
                inputs = processor(
                    text=prompt,
                    images=content.image_content,
                    return_tensors="pt",
                ).to(model.device)
            else:
                inputs = processor(
                    text=prompt,
                    return_tensors="pt",
                ).to(model.device)

            outputs = model.generate(**inputs, max_new_tokens=256)
            input_len = inputs.input_ids.shape[1]
            generated_tokens = outputs[0][input_len:]
            raw_output = processor.decode(generated_tokens, skip_special_tokens=True)

            result = parse_llm_json_response(raw_output)

            # Fall back to EXIF date if LLM missed date
            if result.content_date is None and content.exif_date:
                result.content_date = normalize_date_string(content.exif_date)

            return result
        except Exception as exc:
            logger.warning("Neural understanding failed (%s); falling back to deterministic mode", exc)
            return self._understand_deterministic(content, filename_hint)

    def __call__(
        self,
        content: ExtractedContent,
        filename_hint: str | None = None,
    ) -> UnderstandingResult:
        """Alias for understand."""
        return self.understand(content, filename_hint=filename_hint)

    def _understand_deterministic(
        self,
        content: ExtractedContent,
        filename_hint: str | None = None,
    ) -> UnderstandingResult:
        """High-speed deterministic extraction for offline execution and testing."""
        # 1. Content Date
        content_date: str | None = None
        if content.exif_date:
            content_date = normalize_date_string(content.exif_date)

        text = (content.text_content or "").strip()
        if not content_date and text:
            content_date = _extract_date_from_text(text)

        # 2. Entities
        entities: list[str] = []
        if text:
            entities = _extract_entities_from_text(text)

        # Audio hints if available
        artist = content.metadata_hints.get("artist")
        if artist and str(artist).strip() and str(artist).strip() not in entities:
            entities.append(str(artist).strip())

        # 3. Category Hint
        if content.metadata_hints.get("tool") == "audio_extractor" or "Audio Track Metadata" in text:
            category_hint = "Audio"
        elif content.image_content is not None and not text:
            category_hint = "Photo"
        elif text:
            category_hint = _extract_category_hint_from_text(text)
        else:
            category_hint = "Document"

        # 4. Description Slug
        desc_parts: list[str] = []
        if category_hint == "Audio":
            title = content.metadata_hints.get("title")
            if artist and title:
                desc_parts.append(f"{artist}_{title}")
            elif title:
                desc_parts.append(str(title))
            elif filename_hint:
                desc_parts.append(Path(filename_hint).stem)
            else:
                desc_parts.append("audio_track")
        elif category_hint == "Bank Statement":
            bank = next((e for e in entities if "bank" in e.lower() or e in {"Chase", "Wells Fargo", "Citibank"}), None)
            if bank:
                desc_parts.append(f"{bank}_statement")
            else:
                desc_parts.append("bank_statement")
        elif category_hint == "Medical Record":
            person = next((e for e in entities if e in CANONICAL_PEOPLE), None)
            if person:
                desc_parts.append(f"medical_record_{person}")
            else:
                desc_parts.append("medical_record")
        elif category_hint == "Receipt":
            store = entities[0] if entities else "receipt"
            desc_parts.append(f"receipt_{store}")
        elif category_hint == "Bill":
            provider = entities[0] if entities else "bill"
            desc_parts.append(f"bill_{provider}")
        elif category_hint == "Photo":
            if filename_hint:
                desc_parts.append(Path(filename_hint).stem)
            else:
                desc_parts.append("photo")
        else:
            # Check for header markdown
            m_header = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            if m_header:
                desc_parts.append(m_header.group(1))
            elif filename_hint:
                desc_parts.append(Path(filename_hint).stem)
            elif entities:
                desc_parts.append(f"{entities[0]}_{category_hint.lower()}")
            else:
                desc_parts.append("document")

        raw_desc = "_".join(desc_parts)
        file_description = sanitize_slug(raw_desc)
        if not file_description:
            file_description = "document"

        # 5. Summary
        if category_hint == "Bank Statement":
            summary = f"Bank statement for {entities[0]}" if entities else "Bank statement"
        elif category_hint == "Medical Record":
            summary = f"Medical record for {entities[0]}" if entities else "Medical record"
        elif category_hint == "Audio":
            summary = f"Audio track: {file_description}"
        elif category_hint == "Photo":
            summary = "Image or photograph"
        elif text:
            first_line = text.splitlines()[0].strip()
            summary = first_line[:200]
        else:
            summary = f"{category_hint} file"

        return UnderstandingResult(
            content_date=content_date,
            file_description=file_description,
            detected_entities=entities,
            category_hint=category_hint,
            summary=summary,
        )


def understand_content(
    content: ExtractedContent,
    filename_hint: str | None = None,
    model_id: str = "google/gemma-4-E2B-it",
    mock: bool = False,
    device: str = "auto",
) -> UnderstandingResult:
    """Convenience top-level function to perform content understanding."""
    return GemmaUnderstander(
        model_id=model_id,
        mock=mock,
        device=device,
    ).understand(content, filename_hint=filename_hint)
