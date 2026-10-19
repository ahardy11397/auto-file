"""Tests for Gemma 4 E2B multimodal understander and LLM response parsing."""

from unittest.mock import MagicMock, patch
from PIL import Image
import pytest

from auto_file.core.extractors.base import ExtractedContent
from auto_file.core.understander import (
    GemmaUnderstander,
    UnderstandingResult,
    normalize_date_string,
    parse_llm_json_response,
    understand_content,
)


# ==============================================================================
# JSON Parsing and Normalization Tests
# ==============================================================================


def test_parse_valid_json_response():
    """Verify parsing markdown-fenced JSON output."""
    raw_output = (
        '```json\n{"content_date": "2026-02-14", "file_description": "chase_statement", '
        '"detected_entities": ["Chase"], "category_hint": "Bank Statement", '
        '"summary": "Bank statement"}\n```'
    )
    result = parse_llm_json_response(raw_output)
    assert isinstance(result, UnderstandingResult)
    assert result.content_date == "2026-02-14"
    assert result.file_description == "chase_statement"
    assert "Chase" in result.detected_entities
    assert result.category_hint == "Bank Statement"
    assert result.summary == "Bank statement"


def test_parse_malformed_json_fallback():
    """Verify graceful regex/heuristic fallback for unstructured text."""
    raw_output = "I think this is an invoice from Alpha on March 1st."
    result = parse_llm_json_response(raw_output)
    assert isinstance(result, UnderstandingResult)
    assert result.file_description != ""
    assert "Alpha" in result.detected_entities
    assert result.category_hint in {"Invoice", "Bill", "Bills", "Document"}
    assert "invoice" in result.summary.lower()


def test_parse_raw_json_without_fences():
    """Verify parsing raw JSON without markdown code fences."""
    raw_output = (
        '{"content_date": "2025-11-30", "file_description": "medical_summary", '
        '"detected_entities": ["Dr. Smith", "Charlie"], "category_hint": "Medical Record", '
        '"summary": "Pediatric checkup summary"}'
    )
    result = parse_llm_json_response(raw_output)
    assert result.content_date == "2025-11-30"
    assert result.file_description == "medical_summary"
    assert result.detected_entities == ["Dr. Smith", "Charlie"]
    assert result.category_hint == "Medical Record"
    assert result.summary == "Pediatric checkup summary"


def test_parse_conversational_wrapped_json():
    """Verify extraction of JSON block embedded inside conversational commentary."""
    raw_output = (
        "Here is the extraction for the provided document:\n\n"
        "```json\n"
        "{\n"
        '  "content_date": "2026-01-15",\n'
        '  "file_description": "electric_utility_bill",\n'
        '  "detected_entities": ["Pacific Power"],\n'
        '  "category_hint": "Bill",\n'
        '  "summary": "Monthly electric utility bill for residential service"\n'
        "}\n"
        "```\n\n"
        "Let me know if you need any additional metadata!"
    )
    result = parse_llm_json_response(raw_output)
    assert result.content_date == "2026-01-15"
    assert result.file_description == "electric_utility_bill"
    assert result.detected_entities == ["Pacific Power"]
    assert result.category_hint == "Bill"


def test_parse_json_with_trailing_commas():
    """Verify handling of JSON with trailing commas (common LLM generation artifact)."""
    raw_output = (
        "```json\n"
        "{\n"
        '  "content_date": "2024-07-04",\n'
        '  "file_description": "parade_flyer",\n'
        '  "detected_entities": ["City Park",],\n'
        '  "category_hint": "Misc",\n'
        '  "summary": "Annual 4th of July parade announcement",\n'
        "}\n"
        "```"
    )
    result = parse_llm_json_response(raw_output)
    assert result.content_date == "2024-07-04"
    assert result.file_description == "parade_flyer"
    assert result.detected_entities == ["City Park"]


def test_parse_date_normalization_formats():
    """Verify diverse date formats get normalized to ISO YYYY-MM-DD or None."""
    assert normalize_date_string("2026-02-14") == "2026-02-14"
    assert normalize_date_string("2026/02/14") == "2026-02-14"
    assert normalize_date_string("02/14/2026") == "2026-02-14"
    assert normalize_date_string("February 14, 2026") == "2026-02-14"
    assert normalize_date_string("Feb 14, 2026") == "2026-02-14"
    assert normalize_date_string("14 February 2026") == "2026-02-14"
    assert normalize_date_string("2026-02-14T15:30:00Z") == "2026-02-14"
    assert normalize_date_string("null") is None
    assert normalize_date_string("None") is None
    assert normalize_date_string("") is None
    assert normalize_date_string(None) is None
    # Invalid dates should return None
    assert normalize_date_string("2026-02-31") is None
    assert normalize_date_string("not-a-date") is None


def test_parse_entities_normalization():
    """Verify comma-separated string entities are parsed into clean string lists."""
    raw_output = (
        '```json\n{"content_date": null, "file_description": "tax_form", '
        '"detected_entities": "IRS, US Treasury, Alpha", "category_hint": "Tax Document", '
        '"summary": "W-2 Tax Form"}\n```'
    )
    result = parse_llm_json_response(raw_output)
    assert result.content_date is None
    assert result.detected_entities == ["IRS", "US Treasury", "Alpha"]


def test_parse_empty_and_garbage_input_safety():
    """Verify parse_llm_json_response never crashes on empty, null, or garbage inputs."""
    res_empty = parse_llm_json_response("")
    assert isinstance(res_empty, UnderstandingResult)
    assert res_empty.file_description != ""

    res_spaces = parse_llm_json_response("     \n\t  ")
    assert isinstance(res_spaces, UnderstandingResult)
    assert res_spaces.file_description != ""

    res_garbage = parse_llm_json_response("!!!???@@@#$%^&*()_+=-{}[]")
    assert isinstance(res_garbage, UnderstandingResult)
    assert res_garbage.file_description != ""


# ==============================================================================
# GemmaUnderstander Execution Tests (Mock / Deterministic Mode)
# ==============================================================================


def test_understander_deterministic_text_bank_statement():
    """Test deterministic understander processing bank statement text."""
    understander = GemmaUnderstander(mock=True)
    content = ExtractedContent(
        text_content="CHASE BANK\nAccount ending in 4321\nStatement Date: 2026-01-31\nBalance: $4,200.00"
    )
    result = understander.understand(content)
    assert result.content_date == "2026-01-31"
    assert "chase" in result.file_description
    assert "Chase" in result.detected_entities or "Chase Bank" in result.detected_entities
    assert result.category_hint == "Bank Statement"


def test_understander_deterministic_medical_record():
    """Test deterministic understander processing medical record with person entity."""
    understander = GemmaUnderstander(mock=True)
    content = ExtractedContent(
        text_content="Patient: Alpha\nClinic Visit Summary\nDr. Welby MD\nDate: 2025-10-12\nPrescription provided."
    )
    result = understander.understand(content)
    assert result.content_date == "2025-10-12"
    assert "Alpha" in result.detected_entities
    assert result.category_hint == "Medical Record"


def test_understander_deterministic_image_with_exif():
    """Test deterministic understander processing image with EXIF date."""
    understander = GemmaUnderstander(mock=True)
    img = Image.new("RGB", (200, 200), color="red")
    content = ExtractedContent(
        image_content=img,
        exif_date="2025-08-20",
        metadata_hints={"camera": "Pixel 8"},
    )
    result = understander.understand(content, filename_hint="IMG_4002.jpg")
    assert result.content_date == "2025-08-20"
    assert result.category_hint in {"Photo", "Picture"}
    assert result.file_description != ""


def test_understander_deterministic_audio_metadata():
    """Test deterministic understander processing audio metadata hints."""
    understander = GemmaUnderstander(mock=True)
    content = ExtractedContent(
        text_content="Audio Track Metadata:\nTitle: Bohemian Rhapsody\nArtist: Queen\nAlbum: A Night at the Opera\nDate: 1975-10-31",
        exif_date="1975-10-31",
        metadata_hints={"artist": "Queen", "title": "Bohemian Rhapsody", "tool": "audio_extractor"},
    )
    result = understander.understand(content, filename_hint="track.mp3")
    assert result.content_date == "1975-10-31"
    assert "Queen" in result.detected_entities
    assert result.category_hint in {"Audio", "Music"}


def test_understander_prompt_generation():
    """Verify prompt generation formats text and image inputs appropriately."""
    understander = GemmaUnderstander(mock=True)

    # Text prompt
    text_content = ExtractedContent(text_content="Important contract agreement between Alpha and Charlie.")
    prompt = understander.generate_prompt(text_content)
    assert "Important contract agreement" in prompt
    assert "content_date" in prompt
    assert "file_description" in prompt
    assert "detected_entities" in prompt

    # Image prompt
    img = Image.new("RGB", (50, 50), color="blue")
    image_content = ExtractedContent(image_content=img)
    img_prompt = understander.generate_prompt(image_content)
    assert "image" in img_prompt.lower()
    assert "content_date" in img_prompt


def test_understander_lazy_initialization():
    """Verify model and processor are not loaded on class construction."""
    understander = GemmaUnderstander(model_id="google/gemma-4-E2B-it", mock=False)
    assert understander._is_loaded is False
    assert understander._model is None
    assert understander._processor is None


def test_understander_custom_mock_response():
    """Verify custom mock response overrides for downstream testing."""
    custom = UnderstandingResult(
        content_date="2026-03-01",
        file_description="custom_mock_doc",
        detected_entities=["CustomEntity"],
        category_hint="CustomCategory",
        summary="Custom summary",
    )
    understander = GemmaUnderstander(mock=True, mock_response=custom)
    res = understander.understand(ExtractedContent(text_content="anything"))
    assert res == custom

    # Also test mock string JSON response
    json_str = '```json\n{"content_date": "2026-04-01", "file_description": "from_string", "detected_entities": ["StrCorp"], "category_hint": "Bill", "summary": "Str bill"}\n```'
    understander_str = GemmaUnderstander(mock=True, mock_response=json_str)
    res2 = understander_str.understand(ExtractedContent(text_content="anything"))
    assert res2.content_date == "2026-04-01"
    assert res2.file_description == "from_string"


def test_understander_standalone_function():
    """Test top-level understand_content convenience function."""
    content = ExtractedContent(text_content="Receipt from Home Depot on 2026-02-28 for $50")
    result = understand_content(content, mock=True)
    assert isinstance(result, UnderstandingResult)
    assert result.content_date == "2026-02-28"
    assert "Home Depot" in result.detected_entities or "receipt" in result.file_description


def test_understander_model_loading_and_cuda_oom_fallback():
    """Test lazy loading with 4-bit BitsAndBytesConfig and CPU fallback on CUDA OOM."""
    from auto_file.core.understander import _load_transformer_model

    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = True
    mock_torch.cuda.OutOfMemoryError = type("OutOfMemoryError", (RuntimeError,), {})

    mock_processor = MagicMock()
    mock_model_gpu = MagicMock()
    mock_model_cpu = MagicMock()

    mock_auto_proc = MagicMock()
    mock_auto_proc.from_pretrained.return_value = mock_processor

    mock_auto_model = MagicMock()
    # First call (GPU 4-bit) raises CUDA OOM, second call (CPU) succeeds
    mock_auto_model.from_pretrained.side_effect = [
        mock_torch.cuda.OutOfMemoryError("CUDA out of memory"),
        mock_model_cpu,
    ]

    mock_bnb_config_cls = MagicMock()

    with patch.dict(
        "sys.modules",
        {
            "torch": mock_torch,
            "transformers": MagicMock(
                AutoProcessor=mock_auto_proc,
                AutoModelForImageTextToText=mock_auto_model,
                BitsAndBytesConfig=mock_bnb_config_cls,
            ),
        },
    ):
        model, processor = _load_transformer_model("google/gemma-4-E2B-it", device="auto")
        assert model is mock_model_cpu
        assert processor is mock_processor
        # Verify 4-bit quantization config was attempted
        mock_bnb_config_cls.assert_called_once_with(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=mock_torch.float16,
            bnb_4bit_use_double_quant=True,
        )


def test_understanding_result_to_dict():
    """Verify UnderstandingResult serialization to dictionary."""
    res = UnderstandingResult(
        content_date="2026-02-14",
        file_description="tax_doc",
        detected_entities=["IRS"],
        category_hint="Tax Document",
        summary="Tax document",
    )
    d = res.to_dict()
    assert d == {
        "content_date": "2026-02-14",
        "file_description": "tax_doc",
        "detected_entities": ["IRS"],
        "category_hint": "Tax Document",
        "summary": "Tax document",
        "understood": True,
    }


def test_understander_callable_interface():
    """Verify GemmaUnderstander is directly callable."""
    understander = GemmaUnderstander(mock=True)
    content = ExtractedContent(text_content="Receipt from Home Depot on 2026-02-28")
    result = understander(content)
    assert isinstance(result, UnderstandingResult)
    assert result.content_date == "2026-02-28"


def test_understander_image_without_exif():
    """Verify image understanding when EXIF date is absent."""
    understander = GemmaUnderstander(mock=True)
    img = Image.new("RGB", (100, 100), color="green")
    content = ExtractedContent(image_content=img)
    result = understander.understand(content, filename_hint="scan01.png")
    assert result.content_date is None
    assert result.category_hint == "Photo"
    assert result.file_description == "scan01"


def test_understander_deterministic_markdown_header_slug():
    """Verify document slug generated from markdown H1 header."""
    understander = GemmaUnderstander(mock=True)
    content = ExtractedContent(text_content="# Project Roadmap 2026\nQuarterly goals and milestones.")
    result = understander.understand(content)
    assert "project_roadmap_2026" in result.file_description


def test_understander_long_text_truncation_in_prompt():
    """Verify text exceeding 4000 characters is safely truncated in prompt."""
    understander = GemmaUnderstander(mock=True)
    long_text = "Important content.\n" + ("x" * 6000)
    content = ExtractedContent(text_content=long_text)
    prompt = understander.generate_prompt(content)
    assert "[truncated]" in prompt
    assert len(prompt) < 6000


def test_understander_neural_inference_mocked():
    """Test full neural inference execution path with mocked model and processor."""
    understander = GemmaUnderstander(mock=False)
    mock_model = MagicMock()
    mock_model.device = "cpu"
    mock_processor = MagicMock()

    # Mock inputs
    mock_inputs = MagicMock()
    mock_inputs.input_ids.shape = (1, 10)
    mock_inputs.to.return_value = mock_inputs
    mock_processor.return_value = mock_inputs

    # Mock outputs
    mock_model.generate.return_value = [[0] * 20]
    mock_processor.decode.return_value = (
        '```json\n{"content_date": "2026-05-10", "file_description": "lease_agreement", '
        '"detected_entities": ["Bravo"], "category_hint": "Legal", "summary": "Residential lease"}\n```'
    )

    understander._model = mock_model
    understander._processor = mock_processor
    understander._is_loaded = True

    content = ExtractedContent(text_content="Lease agreement for Bravo")
    result = understander.understand(content)

    assert result.content_date == "2026-05-10"
    assert result.file_description == "lease_agreement"
    assert "Bravo" in result.detected_entities
    assert result.category_hint == "Legal"


def test_understander_neural_inference_exception_fallback():
    """Verify neural inference failure gracefully falls back to deterministic extraction."""
    understander = GemmaUnderstander(mock=False)
    mock_model = MagicMock()
    mock_model.device = "cpu"
    mock_processor = MagicMock()

    mock_inputs = MagicMock()
    mock_inputs.to.side_effect = RuntimeError("GPU failure")
    mock_processor.return_value = mock_inputs

    understander._model = mock_model
    understander._processor = mock_processor
    understander._is_loaded = True

    content = ExtractedContent(text_content="CHASE BANK statement on 2026-01-31")
    result = understander.understand(content)

    # Fallback deterministic extracted results
    assert result.content_date == "2026-01-31"
    assert result.category_hint == "Bank Statement"


def test_parse_llm_json_response_with_comments_before_brace_in_code_fence():
    """Verify JSON parsing succeeds when code fence contains introductory comments before '{'."""
    raw = """```json
    // Here is the analysis of the document:
    {
        "content_date": "2026-07-04",
        "file_description": "city_tax_assessment",
        "detected_entities": ["City of Portland"],
        "category_hint": "Tax Document",
        "summary": "Property tax assessment notice"
    }
    ```"""
    result = parse_llm_json_response(raw)
    assert result.content_date == "2026-07-04"
    assert result.file_description == "city_tax_assessment"
    assert result.detected_entities == ["City of Portland"]
    assert result.category_hint == "Tax Document"
    assert result.summary == "Property tax assessment notice"


def test_understander_model_loading_passes_local_files_only():
    """Verify _load_transformer_model passes local_files_only=True to prevent remote network calls."""
    from auto_file.core.understander import _load_transformer_model

    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False
    mock_auto_proc = MagicMock()
    mock_auto_model = MagicMock()
    mock_processor = MagicMock()
    mock_model = MagicMock()
    mock_auto_proc.from_pretrained.return_value = mock_processor
    mock_auto_model.from_pretrained.return_value = mock_model

    with patch.dict(
        "sys.modules",
        {
            "torch": mock_torch,
            "transformers": MagicMock(
                AutoProcessor=mock_auto_proc,
                AutoModelForImageTextToText=mock_auto_model,
                BitsAndBytesConfig=MagicMock(),
            ),
        },
    ):
        model, processor = _load_transformer_model("google/gemma-4-E2B-it", device="cpu")
        assert model is mock_model
        assert processor is mock_processor
        mock_auto_proc.from_pretrained.assert_called_with(
            "google/gemma-4-E2B-it",
            local_files_only=True,
        )
        mock_auto_model.from_pretrained.assert_called_with(
            "google/gemma-4-E2B-it",
            local_files_only=True,
            device_map="cpu",
            torch_dtype=mock_torch.float32,
        )


# ==============================================================================
# Understanding Confidence Gate Tests
# ==============================================================================


def _content(text: str = "", **hints) -> ExtractedContent:
    return ExtractedContent(
        text_content=text,
        image_content=None,
        metadata_hints=dict(hints),
        exif_date=None,
    )


def test_deterministic_scan_without_text_is_not_understood():
    """A scan with no extractable text cannot be understood."""
    u = GemmaUnderstander(mock=True)
    result = u.understand(_content(), filename_hint="unknown_scan.pdf")
    assert result.understood is False
    assert result.category_hint == "Document"


def test_deterministic_specific_category_is_understood():
    u = GemmaUnderstander(mock=True)
    text = "Your electric bill for September is now available. Amount due: $84.12 by October 3rd."
    result = u.understand(_content(text), filename_hint="bill.pdf")
    assert result.understood is True
    assert result.category_hint == "Bill"


def test_deterministic_rich_generic_text_is_understood():
    """Readable text with no keyword category still counts as understood —
    the summary is real content, not a guess."""
    u = GemmaUnderstander(mock=True)
    text = (
        "Dear customer, thank you for your continued membership with our "
        "warehouse club. This letter confirms your annual renewal was "
        "processed successfully and your membership card remains active. "
        "Please contact member services with any questions about your account."
    )
    result = u.understand(_content(text), filename_hint="letter.pdf")
    assert result.understood is True
    assert result.summary.startswith("Dear customer")


def test_neural_empty_output_is_not_understood():
    """The model running but returning nothing means it did not understand."""
    u = GemmaUnderstander()
    u._model = MagicMock()
    u._processor = MagicMock()
    u._is_loaded = True

    proc_result = MagicMock()
    proc_result.input_ids.shape = (1, 10)
    u._processor.return_value = proc_result
    model_out = MagicMock()
    model_out.__getitem__ = lambda self, idx: MagicMock()
    u._model.generate.return_value = [MagicMock()]
    u._processor.decode.return_value = "..."

    result = u.understand(_content("some text"), filename_hint="mystery.pdf")
    assert result.understood is False


# ==============================================================================
# Packaged LLM Server (llama.cpp) Path Tests
# ==============================================================================


class _FakeResponse:
    def __init__(self, body: dict):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        import json
        return json.dumps(self._body).encode("utf-8")


def test_llama_server_path_parses_understanding():
    """The packaged llama.cpp server response is parsed into a result."""
    from unittest.mock import patch

    u = GemmaUnderstander(mock=False, llama_url="http://127.0.0.1:8081")
    body = {
        "choices": [
            {
                "message": {
                    "content": (
                        '```json\n{"content_date": "2026-05-07", "file_description": "insurance_letter", '
                        '"detected_entities": ["State Farm"], "category_hint": "Insurance", '
                        '"summary": "Renters insurance verification letter"}\n```'
                    )
                }
            }
        ]
    }
    with patch("urllib.request.urlopen", return_value=_FakeResponse(body)):
        result = u.understand(_content(" renters policy documents "), filename_hint="scan.pdf")

    assert result.understood is True
    assert result.category_hint == "Insurance"
    assert result.content_date == "2026-05-07"


def test_llama_server_unreachable_falls_back_to_deterministic():
    """An unreachable server must fall back to the deterministic path (which
    gates thin content to needs_review) instead of raising."""
    from unittest.mock import patch
    import urllib.error

    u = GemmaUnderstander(mock=False, llama_url="http://127.0.0.1:8081")

    def _refuse(*args, **kwargs):
        raise urllib.error.URLError("connection refused")

    with patch("urllib.request.urlopen", side_effect=_refuse):
        result = u.understand(_content(), filename_hint="scan.pdf")

    assert result.understood is False
    assert result.category_hint == "Document"
