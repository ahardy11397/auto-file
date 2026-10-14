"""Tests for Laya tool dispatcher and taxonomy router."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from auto_file.core.detector import FileMetadata
from auto_file.core.dispatcher import LayaDispatcher, dispatch_tool
from auto_file.core.router import TaxonomyRouter, resolve_destination, route_destination


def _make_metadata(
    path: str = "test_file.bin",
    mime_type: str = "application/octet-stream",
    extension: str = ".bin",
    size_bytes: int = 1024,
) -> FileMetadata:
    return FileMetadata(
        path=Path(path),
        mime_type=mime_type,
        extension=extension,
        size_bytes=size_bytes,
        ctime=datetime(2026, 1, 1),
        mtime=datetime(2026, 1, 1),
        sha256="abc123mockhash",
    )


# ==============================================================================
# Dispatcher Unit Tests
# ==============================================================================


def test_dispatch_pdf_by_mime_and_extension():
    dispatcher = LayaDispatcher()
    pdf_meta = _make_metadata(path="doc.pdf", mime_type="application/pdf", extension=".pdf")
    assert dispatcher.dispatch_tool(pdf_meta) == "pdf_extractor"

    pdf_ext_meta = _make_metadata(path="scan.pdf", mime_type="application/octet-stream", extension=".pdf")
    assert dispatcher.dispatch_tool(pdf_ext_meta) == "pdf_extractor"


def test_dispatch_images():
    dispatcher = LayaDispatcher()
    for ext, mime in [(".jpg", "image/jpeg"), (".png", "image/png"), (".webp", "image/webp")]:
        meta = _make_metadata(path=f"pic{ext}", mime_type=mime, extension=ext)
        assert dispatcher.dispatch_tool(meta) == "image_extractor"


def test_dispatch_text_files():
    dispatcher = LayaDispatcher()
    for ext, mime in [
        (".txt", "text/plain"),
        (".csv", "text/csv"),
        (".json", "application/json"),
        (".md", "text/markdown"),
        (".py", "text/x-python"),
    ]:
        meta = _make_metadata(path=f"file{ext}", mime_type=mime, extension=ext)
        assert dispatcher.dispatch_tool(meta) == "text_extractor"


def test_dispatch_audio_files():
    dispatcher = LayaDispatcher()
    for ext, mime in [(".mp3", "audio/mpeg"), (".wav", "audio/wav"), (".flac", "audio/flac")]:
        meta = _make_metadata(path=f"track{ext}", mime_type=mime, extension=ext)
        assert dispatcher.dispatch_tool(meta) == "audio_extractor"


def test_dispatch_fallback_extractor():
    dispatcher = LayaDispatcher()
    unknown_meta = _make_metadata(path="archive.bin", mime_type="application/octet-stream", extension=".bin")
    assert dispatcher.dispatch_tool(unknown_meta) == "fallback_extractor"


def test_dispatch_standalone_function():
    meta = _make_metadata(path="receipt.pdf", mime_type="application/pdf", extension=".pdf")
    assert dispatch_tool(meta) == "pdf_extractor"


def test_dispatcher_onnx_invocation():
    """Test dispatcher using mock ONNX session when model path is provided."""
    dispatcher = LayaDispatcher()
    meta = _make_metadata(path="unknown.dat", mime_type="application/octet-stream", extension=".dat")

    mock_session = MagicMock()
    # Output ranking logits for ["pdf_extractor", "image_extractor", "text_extractor", "audio_extractor", "fallback_extractor"]
    # Suppose index 2 ("text_extractor") has the highest score
    mock_session.run.return_value = [[0.1, 0.2, 0.9, 0.1, 0.0]]
    mock_input = MagicMock()
    mock_input.name = "input_text"
    mock_session.get_inputs.return_value = [mock_input]

    with patch("auto_file.core.dispatcher._create_onnx_session", return_value=mock_session):
        tool = dispatcher.dispatch_tool(meta, model_path="mock_model.onnx")
        assert tool == "text_extractor"


def test_dispatcher_onnx_fallback_on_error():
    """Test dispatcher safely falls back to deterministic rule if ONNX inference raises."""
    dispatcher = LayaDispatcher()
    meta = _make_metadata(path="invoice.pdf", mime_type="application/pdf", extension=".pdf")

    with patch("auto_file.core.dispatcher._create_onnx_session", side_effect=RuntimeError("ONNX crash")):
        tool = dispatcher.dispatch_tool(meta, model_path="broken_model.onnx")
        assert tool == "pdf_extractor"


# ==============================================================================
# Taxonomy Router Unit Tests
# ==============================================================================


def test_route_person_medical():
    router = TaxonomyRouter()
    subpath = router.resolve_destination(
        entities=["Alpha"],
        category_hint="Medical Record",
        summary="Dr visit receipt for Alpha",
    )
    assert subpath == Path("People/Alpha/Medical")


def test_route_financial_bank_statement():
    router = TaxonomyRouter()
    subpath = router.resolve_destination(
        entities=["Chase Bank", "1234"],
        category_hint="Bank Statement",
        summary="Chase bank account statement",
    )
    assert subpath == Path("Financial/Bank Statements/Chase_Bank")


def test_route_all_people():
    router = TaxonomyRouter()
    people = ["Alpha", "Bravo", "Charlie", "Delta", "Echo"]

    # Records
    for person in people:
        sub = router.resolve_destination(
            entities=[person],
            category_hint="Records",
            summary=f"Birth certificate of {person}",
        )
        assert sub == Path(f"People/{person}/Records")

    # Pictures
    sub_pic = router.resolve_destination(
        entities=["Bravo"],
        category_hint="Pictures",
        summary="Family portrait of Bravo at vacation",
    )
    assert sub_pic == Path("People/Bravo/Pictures")

    # Documents
    sub_doc = router.resolve_destination(
        entities=["Delta"],
        category_hint="Documents",
        summary="Delta school application form",
    )
    assert sub_doc == Path("People/Delta/Documents")

    # Misc
    sub_misc = router.resolve_destination(
        entities=["Echo"],
        category_hint="Misc",
        summary="Personal note for Echo",
    )
    assert sub_misc == Path("People/Echo/Misc")


def test_route_person_from_summary_fallback():
    router = TaxonomyRouter()
    sub = router.resolve_destination(
        entities=[],
        category_hint="Medical",
        summary="Prescription refill for Charlie at Walgreens",
    )
    assert sub == Path("People/Charlie/Medical")


def test_route_financial_bills():
    router = TaxonomyRouter()
    # Bill due
    sub_due = router.resolve_destination(
        entities=["Duke Energy"],
        category_hint="Bills",
        summary="Electric bill due on May 15",
    )
    assert sub_due == Path("Financial/Bills/Due")

    # Bill receipt
    sub_paid = router.resolve_destination(
        entities=["Duke Energy"],
        category_hint="Bills",
        summary="Payment receipt for electric utility bill",
    )
    assert sub_paid == Path("Financial/Bills/Receipts")


def test_route_financial_receipts_by_entity():
    router = TaxonomyRouter()
    sub = router.resolve_destination(
        entities=["Home Depot"],
        category_hint="Receipts",
        summary="Hardware supplies receipt",
    )
    assert sub == Path("Financial/Receipts/Home_Depot")


def test_route_financial_documents_by_entity():
    router = TaxonomyRouter()
    sub = router.resolve_destination(
        entities=["IRS"],
        category_hint="Documents",
        summary="Form W-2 tax transcript",
    )
    assert sub == Path("Financial/Documents/IRS")


def test_route_financial_misc():
    router = TaxonomyRouter()
    sub = router.resolve_destination(
        entities=[],
        category_hint="Financial",
        summary="General financial ledger overview",
    )
    assert sub == Path("Financial/Misc")


def test_route_legal():
    router = TaxonomyRouter()
    # Court by case
    sub_court = router.resolve_destination(
        entities=["Case 2026-CV-42"],
        category_hint="Court",
        summary="Court docket filing for case 2026-CV-42",
    )
    assert sub_court == Path("Legal/Court/Case_2026-CV-42")

    # Legal misc
    sub_misc = router.resolve_destination(
        entities=[],
        category_hint="Legal",
        summary="General legal terms and conditions",
    )
    assert sub_misc == Path("Legal/Misc")


def test_route_property():
    router = TaxonomyRouter()
    sub_veh = router.resolve_destination(
        entities=["Toyota Tacoma"],
        category_hint="Vehicles",
        summary="Vehicle title and registration",
    )
    assert sub_veh == Path("Property/Vehicles")

    sub_re = router.resolve_destination(
        entities=[],
        category_hint="Real Estate",
        summary="Residential property deed and title policy",
    )
    assert sub_re == Path("Property/Real Estate")

    sub_misc = router.resolve_destination(
        entities=[],
        category_hint="Property",
        summary="Storage unit lease contract",
    )
    assert sub_misc == Path("Property/Misc")


def test_route_manuals():
    router = TaxonomyRouter()
    sub_app = router.resolve_destination(
        entities=["Bosch"],
        category_hint="Manuals",
        summary="Bosch Dishwasher user instruction manual",
    )
    assert sub_app == Path("Manuals/Appliances")

    sub_elec = router.resolve_destination(
        entities=["Sony"],
        category_hint="Manuals",
        summary="Sony OLED TV operating guide",
    )
    assert sub_elec == Path("Manuals/Electronics")

    sub_tools = router.resolve_destination(
        entities=["DeWalt"],
        category_hint="Manuals",
        summary="Cordless drill safety instructions",
    )
    assert sub_tools == Path("Manuals/Tools")


def test_route_misc_default():
    router = TaxonomyRouter()
    assert router.resolve_destination(entities=[], category_hint=None, summary=None) == Path("Misc")
    assert router.resolve_destination(entities=["Unknown"], category_hint="Random", summary="Unknown data") == Path("Misc")


def test_route_exact_structure_spelling():
    """Verify exact verbatim spelling from FOLDER_STRUCTURE.md when requested."""
    router = TaxonomyRouter(exact_spelling=True)
    sub_doc = router.resolve_destination(
        entities=["Alpha"],
        category_hint="Documents",
        summary="Personal document for Alpha",
    )
    assert sub_doc == Path("People/Alpha/Docuements")

    sub_receipt = router.resolve_destination(
        entities=["Target"],
        category_hint="Receipts",
        summary="Target receipt",
    )
    assert sub_receipt == Path("Financial/Reciepts/Target")

    sub_bill_receipt = router.resolve_destination(
        entities=["Utility"],
        category_hint="Bills",
        summary="Bill receipt",
    )
    assert sub_bill_receipt == Path("Financial/Bills/Reciepts")


def test_standalone_resolve_and_route_destination():
    sub1 = resolve_destination(
        entities=["Alpha"],
        category_hint="Medical Record",
        summary="Dr visit receipt for Alpha",
    )
    assert sub1 == Path("People/Alpha/Medical")

    sub2 = route_destination(
        summary="Chase bank account statement",
        entities=["Chase Bank", "1234"],
        category_hint="Bank Statement",
    )
    assert sub2 == Path("Financial/Bank Statements/Chase_Bank")


def test_router_onnx_inference():
    """Test router using mock ONNX session for ranking top categories."""
    router = TaxonomyRouter()

    mock_session = MagicMock()
    # Mock output ranking logits over ["People", "Financial", "Legal", "Property", "Manuals", "Misc"]
    # Set index 1 ("Financial") highest
    mock_session.run.return_value = [[0.0, 1.0, 0.0, 0.0, 0.0, 0.0]]
    mock_input = MagicMock()
    mock_input.name = "input_text"
    mock_session.get_inputs.return_value = [mock_input]

    with patch("auto_file.core.router._create_onnx_session", return_value=mock_session):
        sub = router.resolve_destination(
            entities=["Chase Bank"],
            category_hint="Bank Statement",
            summary="Chase account details",
            model_path="mock_router.onnx",
        )
        assert sub == Path("Financial/Bank Statements/Chase_Bank")


class _MockNdarray:
    """Mock object mimicking numpy ndarray with tolist() method."""

    def __init__(self, data):
        self._data = data

    def tolist(self):
        return self._data


def test_dispatcher_onnx_ndarray_support():
    """Verify dispatcher properly normalizes numpy ndarrays with tolist()."""
    dispatcher = LayaDispatcher()
    meta = _make_metadata(path="scan.bin", mime_type="application/octet-stream", extension=".bin")

    mock_session = MagicMock()
    # Candidate tools: ["pdf_extractor", "image_extractor", "text_extractor", "audio_extractor", "fallback_extractor"]
    # Set index 0 ("pdf_extractor") highest
    mock_session.run.return_value = [_MockNdarray([[0.95, 0.01, 0.01, 0.01, 0.02]])]
    mock_input = MagicMock()
    mock_input.name = "input_text"
    mock_session.get_inputs.return_value = [mock_input]

    with patch("auto_file.core.dispatcher._create_onnx_session", return_value=mock_session):
        tool = dispatcher.dispatch_tool(meta, model_path="mock_dispatcher.onnx")
        assert tool == "pdf_extractor"


def test_router_onnx_ndarray_support():
    """Verify router properly normalizes numpy ndarrays with tolist()."""
    router = TaxonomyRouter()

    mock_session = MagicMock()
    # Root categories: ["People", "Financial", "Legal", "Property", "Manuals", "Misc"]
    # Set index 2 ("Legal") highest
    mock_session.run.return_value = [_MockNdarray([[0.0, 0.0, 1.0, 0.0, 0.0, 0.0]])]
    mock_input = MagicMock()
    mock_input.name = "input_text"
    mock_session.get_inputs.return_value = [mock_input]

    with patch("auto_file.core.router._create_onnx_session", return_value=mock_session):
        sub = router.resolve_destination(
            entities=[],
            category_hint="Legal Notice",
            summary="Subpoena legal notice",
            model_path="mock_router.onnx",
        )
        assert sub == Path("Legal/Court")
