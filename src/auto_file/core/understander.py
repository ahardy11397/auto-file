"""Multimodal document understander using Gemma 4 E2B with JSON parsing and fallback."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
import json
import logging
import os
import subprocess
import threading
import time
import urllib.request
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
    understood: bool = True

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
    if any(k in tl for k in ["resume", "curriculum vitae", "work experience", "professional experience"]):
        return "Resume"
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
            "insurance",
            "renter's insurance",
            "renters insurance",
            "policy number",
            "premium",
            "deductible",
            "coverage",
            "proof of insurance",
        ]
    ):
        return "Insurance"
    if any(
        k in tl
        for k in [
            "medical record",
            "medical history",
            "patient",
            "clinic",
            "hospital",
            "doctor",
            "dr.",
            "dr ",
            "physician",
            "prescription",
            "rx",
            "pediatric",
            "checkup",
            "appointment",
            "dental",
            "dentist",
            "diagnosis",
            "immunization",
            "vaccination",
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

    # Search for outermost JSON object brackets (handles text/comments before/after '{')
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
    Passes local_files_only=True to prevent remote network attempts, with
    graceful fallback if offline or local files are missing.
    """
    import torch
    try:
        # transformers >= 5
        from transformers import AutoModelForImageTextToText as _VisionModelCls
    except ImportError:
        # transformers < 5
        from transformers import AutoModelForVision2Seq as _VisionModelCls
    from transformers import AutoProcessor, BitsAndBytesConfig

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    def _from_pretrained(loader_cls: Any, **kwargs: Any) -> Any:
        try:
            return loader_cls.from_pretrained(model_id, local_files_only=True, **kwargs)
        except (OSError, ValueError) as exc:
            logger.debug(
                "Loading %s with local_files_only=True failed (%s); attempting standard load",
                loader_cls,
                exc,
            )
            return loader_cls.from_pretrained(model_id, **kwargs)

    if torch.cuda.is_available() and device != "cpu":
        try:
            processor = _from_pretrained(AutoProcessor)
            model = _from_pretrained(
                _VisionModelCls,
                quantization_config=bnb_config,
                device_map=device,
            )
            return model, processor
        except (torch.cuda.OutOfMemoryError, RuntimeError, Exception) as exc:
            logger.warning("CUDA initialization failed or OOM (%s); falling back to CPU", exc)
            processor = _from_pretrained(AutoProcessor)
            model = _from_pretrained(
                _VisionModelCls,
                device_map="cpu",
                torch_dtype=torch.float32,
            )
            return model, processor
    else:
        processor = _from_pretrained(AutoProcessor)
        model = _from_pretrained(
            _VisionModelCls,
            device_map="cpu",
            torch_dtype=torch.float32,
        )
        return model, processor


class LlamaServerManager:
    """On-demand llama.cpp server lifecycle for the packaged Gemma model.

    Starts ``llama-server`` bound to localhost only when a document needs
    understanding, and shuts it down after an idle timeout — so there is no
    standing network service. Single-flight by design (the watcher processes
    one file at a time).
    """

    def __init__(
        self,
        binary: str,
        model: str,
        mmproj: str | None = None,
        port: int = 8082,
        idle_seconds: int = 300,
        start_timeout: int = 900,
    ) -> None:
        self.binary = str(Path(binary).expanduser())
        self.model = str(Path(model).expanduser())
        self.mmproj = str(Path(mmproj).expanduser()) if mmproj else None
        self.port = int(port)
        self.idle_seconds = int(idle_seconds)
        self.start_timeout = int(start_timeout)
        self.url = f"http://127.0.0.1:{self.port}"
        self._proc: subprocess.Popen | None = None
        self._idle_timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._in_flight = 0
        self._pidfile = Path.home() / ".local" / "state" / "auto-file" / "llama-server.pid"

    def _pidfile_pid(self) -> int | None:
        """Return the pid of a server we previously spawned, if still alive."""
        try:
            pid = int(self._pidfile.read_text().strip())
            Path(f"/proc/{pid}").resolve()  # raises if gone
            return pid
        except (OSError, ValueError):
            return None

    def _write_pidfile(self, pid: int) -> None:
        try:
            self._pidfile.parent.mkdir(parents=True, exist_ok=True)
            self._pidfile.write_text(str(pid))
        except OSError:
            pass

    def _clear_pidfile(self) -> None:
        try:
            self._pidfile.unlink(missing_ok=True)
        except OSError:
            pass

    def _kill_stale_orphan(self) -> None:
        """Kill a leftover llama-server we spawned earlier (tracked by pidfile)."""
        pid = self._pidfile_pid()
        if pid is not None:
            logger.warning("Killing stale llama-server orphan (pid %s)", pid)
            try:
                os.kill(pid, 9)
            except OSError:
                pass
            self._clear_pidfile()
            time.sleep(1)

    def _healthy(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.url}/health", timeout=3) as resp:
                return b"ok" in resp.read()
        except Exception:
            return False

    def ensure_running(self) -> bool:
        """Make sure the server is up; spawn it if needed. True when healthy."""
        with self._lock:
            if self._healthy():
                # Adopt a server we previously spawned (tracked by pidfile)
                # so its idle shutdown can still stop it later.
                if self._pidfile_pid() is not None or self._proc is not None:
                    self._reset_idle_timer()
                    return True
                # Healthy but untracked — we cannot manage its lifecycle
                # safely; treat as unavailable rather than leave it standing.
                logger.warning("Port %s is served by an untracked llama-server; not adopting", self.port)
                return False

            # A previous spawn may have outlived its manager (crash, race):
            # adopt it if healthy, otherwise kill our own orphan before retry.
            orphan = self._pidfile_pid()
            if orphan is not None:
                self._kill_stale_orphan()

            self._stop_locked()

            env = dict(os.environ)
            build_bin = Path(self.binary).resolve().parent
            env["LD_LIBRARY_PATH"] = str(build_bin) + ":" + env.get("LD_LIBRARY_PATH", "")
            cmd = [
                self.binary,
                "-m", self.model,
                "-c", "4096",
                "--host", "127.0.0.1",
                "--port", str(self.port),
                "--jinja",
                "-ngl", "0",
            ]
            if self.mmproj:
                cmd += ["--mmproj", self.mmproj]

            try:
                log_path = Path.home() / ".local" / "state" / "auto-file"
                log_path.mkdir(parents=True, exist_ok=True)
                log_file = open(log_path / "llama-server.log", "ab")
                self._proc = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    env=env,
                    start_new_session=True,
                )
                self._write_pidfile(self._proc.pid)
            except OSError as exc:
                logger.warning("Could not spawn llama-server (%s); using deterministic fallback", exc)
                return False

            deadline = time.time() + self.start_timeout
            while True:
                if self._proc.poll() is not None:
                    logger.warning("llama-server exited during startup (code %s)", self._proc.returncode)
                    self._proc = None
                    return False
                if self._healthy():
                    logger.info("llama-server started on %s", self.url)
                    self._reset_idle_timer()
                    return True
                # Model loads can take minutes on a busy disk; wait as long as
                # the server process itself is alive. Hard-stop well past any
                # reasonable load to avoid an infinite wait.
                if time.time() > deadline and deadline > 0:
                    logger.warning("llama-server still loading after %ss; giving up", self.start_timeout)
                    self._stop_locked()
                    return False
                time.sleep(2)

    def begin_request(self) -> None:
        """Mark a request in flight so the idle shutdown cannot kill it."""
        with self._lock:
            self._in_flight += 1
            if self._idle_timer is not None:
                self._idle_timer.cancel()
                self._idle_timer = None

    def end_request(self) -> None:
        """Request finished; re-arm the idle shutdown."""
        with self._lock:
            self._in_flight = max(0, self._in_flight - 1)
            self._reset_idle_timer()

    def _reset_idle_timer(self) -> None:
        if self._idle_timer is not None:
            self._idle_timer.cancel()
        if self.idle_seconds > 0:
            self._idle_timer = threading.Timer(self.idle_seconds, self._idle_shutdown)
            self._idle_timer.daemon = True
            self._idle_timer.start()

    def _idle_shutdown(self) -> None:
        with self._lock:
            if self._in_flight > 0:
                # A request is running; re-arm and wait for it to finish.
                self._reset_idle_timer()
                return
            if self._healthy():
                logger.info("llama-server idle for %ss; shutting down", self.idle_seconds)
                self._stop_locked()

    def _stop_locked(self) -> None:
        if self._idle_timer is not None:
            self._idle_timer.cancel()
            self._idle_timer = None
        proc = self._proc
        pid = self._pidfile_pid()
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        if proc is None and pid is not None:
            # Spawned by a previous manager instance that died before cleanup.
            try:
                os.kill(pid, 15)
                time.sleep(2)
                os.kill(pid, 9)
            except OSError:
                pass
        self._proc = None
        self._clear_pidfile()

    def shutdown(self) -> None:
        with self._lock:
            self._stop_locked()


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
        mock: bool | None = None,
        device: str = "auto",
        mock_response: Any = None,
        mock_handler: Any = None,
        llama_url: str | None = None,
        llama_server: dict[str, Any] | None = None,
    ) -> None:
        """Initialize Gemma understander.

        Args:
            model_id: Hugging Face model identifier (default: google/gemma-4-E2B-it).
            mock: If True, uses deterministic offline extraction without loading
                weights. If None (default), AUTO_FILE_UNDERSTANDER=mock forces
                deterministic mode (used by the test suite); otherwise the real
                model loads.
            device: Target device mapping ('auto', 'cuda', 'cpu').
            mock_response: Optional fixed response (UnderstandingResult, string, or callable).
            mock_handler: Optional custom callback for mock execution.
            llama_url: Optional OpenAI-compatible LLM server base URL (e.g.
                'http://127.0.0.1:8081' for the packaged llama.cpp Gemma service).
                When set, this server is the primary understanding path: it is
                much faster than in-process transformers and supports vision for
                scanned documents. Unreachable servers fall back to the
                deterministic path.
            llama_server: Optional on-demand server config dict with keys
                'binary', 'model', 'mmproj', 'port', 'idle_seconds'. When set,
                llama-server is spawned for the duration of a sorting batch and
                shut down after the idle timeout — no standing network service.
        """
        self.model_id = model_id
        self.mock = mock
        self.device = device
        self.mock_response = mock_response
        self.mock_handler = mock_handler
        self.llama_url = (llama_url or "").rstrip("/") or None
        self._server_mgr = LlamaServerManager(**llama_server) if llama_server else None

        # Test hook: AUTO_FILE_UNDERSTANDER=mock forces deterministic mode so
        # the test suite never attempts a real model download or GPU load.
        # An explicit mock=False always takes the real path.
        if self.mock is None and os.environ.get("AUTO_FILE_UNDERSTANDER", "").strip().lower() == "mock":
            self.mock = True

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

        # 2.5 Packaged Gemma via llama.cpp — primary neural path: fast on this
        # hardware and supports vision for scans. On-demand mode spawns the
        # server for the batch and shuts it down after idling; an external
        # server (llama_url) is used as-is. Any failure falls straight to the
        # deterministic path rather than the very slow in-process
        # transformers route.
        if self._server_mgr is not None:
            if not self._server_mgr.ensure_running():
                return self._understand_deterministic(content, filename_hint)
            self._server_mgr.begin_request()
            try:
                result = self._understand_via_llama_server(content, filename_hint, self._server_mgr.url)
            finally:
                self._server_mgr.end_request()
            if result is not None:
                return result
            return self._understand_deterministic(content, filename_hint)

        if self.llama_url:
            result = self._understand_via_llama_server(content, filename_hint)
            if result is not None:
                return result
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

            # The model ran but understood nothing (empty or garbage output
            # that even the fallback parser got nothing from): flag for
            # review instead of renaming the file into a generic folder.
            raw_clean = raw_output.strip()
            generic_result = (
                result.category_hint in {"", "Document"}
                and result.file_description in {"", "document"}
                and len(result.summary.strip()) < 15
            )
            if not raw_clean or len(raw_clean) < 20 or generic_result:
                result.understood = False

            # Fall back to EXIF date if LLM missed date
            if result.content_date is None and content.exif_date:
                result.content_date = normalize_date_string(content.exif_date)

            return result
        except Exception as exc:
            logger.warning("Neural understanding failed (%s); falling back to deterministic mode", exc)
            return self._understand_deterministic(content, filename_hint)

    def _understand_via_llama_server(
        self,
        content: ExtractedContent,
        filename_hint: str | None = None,
        url: str | None = None,
    ) -> UnderstandingResult | None:
        """Understand via the packaged llama.cpp OpenAI-compatible server.

        Returns None when the server is unreachable so the caller can fall
        back to the deterministic path. Vision: extracted page images are
        sent as base64 data URLs when the server was started with an mmproj.
        """
        import base64
        import io
        import json as _json
        import urllib.request

        prompt = self.generate_prompt(content, filename_hint)
        content_parts: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if content.image_content is not None:
            buf = io.BytesIO()
            content.image_content.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            content_parts.append(
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
            )

        payload = _json.dumps(
            {
                "model": "gemma-4-E2B-it",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a document classifier. Respond with ONLY the requested "
                            "JSON object. Do not think out loud and do not explain."
                        ),
                    },
                    {"role": "user", "content": content_parts},
                ],
                "temperature": 0,
                "max_tokens": 1024,
                "stream": False,
                "chat_template_kwargs": {"enable_thinking": False},
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            f"{url or self.llama_url}/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = _json.loads(resp.read().decode("utf-8"))
            message = body["choices"][0]["message"]
            # Thinking-disabled servers fill content; if thinking still leaks
            # into reasoning_content, fall back to parsing that.
            raw_output = message.get("content") or message.get("reasoning_content") or ""
        except Exception as exc:
            logger.warning("LLM server at %s unreachable or failed (%s); using deterministic fallback", url or self.llama_url, exc)
            return None

        try:
            result = parse_llm_json_response(raw_output)

            # Garbage check: the model ran but understood nothing (empty
            # output, or it punted to a generic/unclassified category with
            # nothing usable for a description) — flag for review instead of
            # renaming the file into a generic folder.
            raw_clean = (raw_output or "").strip()
            uninformative = result.category_hint in {
                "",
                "Document",
                "Misc",
                "Unknown",
                "Uncategorized",
            }
            if not raw_clean or uninformative:
                result.understood = False

            if result.content_date is None and content.exif_date:
                result.content_date = normalize_date_string(content.exif_date)

            return result
        except Exception as exc:
            logger.warning("LLM server output could not be parsed (%s); using deterministic fallback", exc)
            return None

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
        elif category_hint == "Insurance":
            insurer = next(
                (
                    e
                    for e in entities
                    if any(
                        w in e.lower()
                        for w in ["insurance", "state farm", "allstate", "geico", "progressive", "liberty mutual", "usaa", "farmers"]
                    )
                ),
                None,
            )
            if insurer:
                desc_parts.append(f"insurance_{insurer}")
            else:
                desc_parts.append("insurance_letter")
        elif category_hint == "Medical Record":
            person = next((e for e in entities if e in CANONICAL_PEOPLE), None)
            if person:
                desc_parts.append(f"medical_record_{person}")
            else:
                desc_parts.append("medical_record")
        elif category_hint == "Receipt":
            if entities:
                desc_parts.append(f"receipt_{entities[0]}")
            else:
                desc_parts.append("receipt")
        elif category_hint == "Bill":
            if entities:
                desc_parts.append(f"bill_{entities[0]}")
            else:
                desc_parts.append("bill")
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
            text_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            summary = " ".join(text_lines[:3])[:240]
        else:
            summary = f"{category_hint} file"

        # 6. Understanding confidence: only claim understanding when there is
        # real evidence — a specific category derived from content, or enough
        # readable text. Scans with no extractable text and unidentifiable
        # documents are flagged so the pipeline leaves them untouched.
        text_words = len(text.split())
        text_ok = text_words >= 25 and len(text) >= 120
        specific_hint = category_hint not in {"", "Document", "Photo", "Audio"}
        photo_ok = category_hint == "Photo" and bool(content.exif_date)
        audio_ok = category_hint == "Audio" and bool(
            content.metadata_hints.get("title") or content.metadata_hints.get("artist")
        )
        understood = specific_hint or text_ok or photo_ok or audio_ok

        return UnderstandingResult(
            content_date=content_date,
            file_description=file_description,
            detected_entities=entities,
            category_hint=category_hint,
            summary=summary,
            understood=understood,
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
