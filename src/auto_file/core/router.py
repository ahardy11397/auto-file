"""Taxonomical destination router for the Auto-File system."""

from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Any
import unicodedata

logger = logging.getLogger(__name__)

CANONICAL_PEOPLE: list[str] = ["Alpha", "Bravo", "Charlie", "Delta", "Echo"]

ROOT_CATEGORIES: list[str] = [
    "People",
    "Financial",
    "Legal",
    "Property",
    "Manuals",
    "Misc",
]


def sanitize_folder_name(name: str) -> str:
    """Sanitize an entity, case, or account string for directory path safety."""
    if not name:
        return ""
    # Normalize unicode to ASCII base equivalents
    text = unicodedata.normalize("NFKD", name)
    text = text.encode("ascii", "ignore").decode("ascii")
    # Replace non-alphanumeric and non-hyphen/period characters with underscore
    text = re.sub(r"[^\w\-.]+", "_", text)
    # Collapse consecutive underscores
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def _create_onnx_session(model_path: Path | str) -> Any:
    """Create an ONNX runtime inference session.

    Separated into a standalone helper for test mockability and error handling.
    """
    import onnxruntime as ort  # type: ignore[import-untyped]

    return ort.InferenceSession(str(model_path))


class TaxonomyRouter:
    """Encodes the hierarchical taxonomy from FOLDER_STRUCTURE.md.

    Routes files into relative paths according to classified entities,
    semantic summary, and category hints.
    """

    def __init__(
        self,
        model_path: Path | str | None = None,
        exact_spelling: bool = False,
    ) -> None:
        """Initialize the taxonomy router.

        Args:
            model_path: Optional path to Laya ONNX decision model weights.
            exact_spelling: If True, uses verbatim spelling from FOLDER_STRUCTURE.md
                (e.g. 'Docuements' and 'Reciepts'). Defaults to False (standard spelling).
        """
        self.default_model_path = Path(model_path) if model_path is not None else None
        self.exact_spelling = exact_spelling

    @property
    def doc_folder_name(self) -> str:
        return "Docuements" if self.exact_spelling else "Documents"

    @property
    def receipts_folder_name(self) -> str:
        return "Reciepts" if self.exact_spelling else "Receipts"

    def resolve_destination(
        self,
        entities: list[str] | None = None,
        category_hint: str | None = None,
        summary: str | None = None,
        model_path: Path | str | None = None,
    ) -> Path:
        """Resolve destination path relative to target root.

        Args:
            entities: Optional list of named entities extracted from file content.
            category_hint: Optional category classification hint from LLM.
            summary: Optional short content summary.
            model_path: Optional path to Laya ONNX decision model weights.

        Returns:
            Relative Path object representing target folder (e.g. Path('People/Alpha/Medical')).
        """
        active_model = model_path if model_path is not None else self.default_model_path
        entity_list = [e.strip() for e in (entities or []) if e and e.strip()]
        hint = (category_hint or "").strip()
        text_summary = (summary or "").strip()

        # Step 1: Optional ONNX root category prediction
        onnx_root: str | None = None
        if active_model is not None:
            onnx_root = self._predict_onnx_root(entity_list, hint, text_summary, active_model)

        # Step 2: Hierarchical deterministic taxonomy resolution
        return self._resolve_hierarchy(
            entities=entity_list,
            hint=hint,
            summary=text_summary,
            onnx_root=onnx_root,
        )

    def route_destination(
        self,
        summary: str | None = None,
        entities: list[str] | None = None,
        category_hint: str | None = None,
        model_path: Path | str | None = None,
    ) -> Path:
        """Alias matching alternative argument ordering."""
        return self.resolve_destination(
            entities=entities,
            category_hint=category_hint,
            summary=summary,
            model_path=model_path,
        )

    def _predict_onnx_root(
        self,
        entities: list[str],
        hint: str,
        summary: str,
        model_path: Path | str,
    ) -> str | None:
        """Run Laya ONNX session ranking for top root categories."""
        try:
            session = _create_onnx_session(model_path)
            inputs = session.get_inputs()
            input_names = [inp.name for inp in inputs] if inputs else ["input"]

            prompt_text = (
                f"entities: {', '.join(entities)}, "
                f"category_hint: {hint}, "
                f"summary: {summary}"
            )

            feed: dict[str, Any] = {}
            for name in input_names:
                feed[name] = [prompt_text]

            outputs = session.run(None, feed)
            if not outputs:
                return None

            raw_out = outputs[0]
            if isinstance(raw_out, (list, tuple)) and len(raw_out) > 0:
                first_item = raw_out[0]
                if isinstance(first_item, (list, tuple)):
                    scores = list(first_item)
                else:
                    scores = list(raw_out)

                if scores and len(scores) == len(ROOT_CATEGORIES):
                    max_idx = max(range(len(scores)), key=lambda i: scores[i])
                    return ROOT_CATEGORIES[max_idx]

            if isinstance(raw_out, str) and raw_out in ROOT_CATEGORIES:
                return raw_out

            return None
        except Exception as exc:
            logger.debug("ONNX taxonomy inference failed, falling back: %s", exc)
            return None

    def _find_person(self, entities: list[str], hint: str, summary: str) -> str | None:
        """Find a canonical person name matching entities, summary, or hint."""
        # 1. Inspect explicit entities list
        for entity in entities:
            entity_norm = entity.strip().lower()
            for person in CANONICAL_PEOPLE:
                if person.lower() == entity_norm:
                    return person

        # 2. Inspect summary and hint using whole-word matching
        combined_text = f"{hint} {summary}".lower()
        for person in CANONICAL_PEOPLE:
            pattern = rf"\b{re.escape(person.lower())}\b"
            if re.search(pattern, combined_text):
                return person

        return None

    def _resolve_hierarchy(
        self,
        entities: list[str],
        hint: str,
        summary: str,
        onnx_root: str | None = None,
    ) -> Path:
        """Execute hierarchical deterministic branch resolution."""
        hint_lower = hint.lower()
        summary_lower = summary.lower()
        combined = f"{hint_lower} {summary_lower}"

        person = self._find_person(entities, hint, summary)

        # Check if root is explicitly constrained to non-People by hints
        is_explicit_financial = any(
            k in hint_lower
            for k in ["bank statement", "bill", "financial", "receipt", "tax", "w-2", "1099"]
        )
        is_explicit_legal = any(k in hint_lower for k in ["court", "lawsuit", "legal"])
        is_explicit_property = any(k in hint_lower for k in ["vehicle", "real estate", "property"])
        is_explicit_manuals = any(k in hint_lower for k in ["manual", "user guide"])

        # ----------------------------------------------------------------------
        # Branch 1: People
        # ----------------------------------------------------------------------
        if person is not None and not (
            is_explicit_financial or is_explicit_legal or is_explicit_property or is_explicit_manuals
        ):
            return self._resolve_person_subpath(person, hint_lower, summary_lower, combined)

        # If onnx predicted People and person is known
        if onnx_root == "People" and person is not None:
            return self._resolve_person_subpath(person, hint_lower, summary_lower, combined)

        # ----------------------------------------------------------------------
        # Branch 2: Financial
        # ----------------------------------------------------------------------
        if (
            onnx_root == "Financial"
            or is_explicit_financial
            or any(
                k in combined
                for k in [
                    "bank statement",
                    "bank account",
                    "checking statement",
                    "savings statement",
                    "bill",
                    "receipt",
                    "reciep",
                    "invoice",
                    "tax",
                    "w-2",
                    "1099",
                    "irs",
                    "financial",
                    "ledger",
                ]
            )
        ):
            return self._resolve_financial_subpath(entities, hint_lower, summary_lower, combined)

        # ----------------------------------------------------------------------
        # Branch 3: Legal
        # ----------------------------------------------------------------------
        if (
            onnx_root == "Legal"
            or is_explicit_legal
            or any(
                k in combined
                for k in [
                    "court",
                    "case",
                    "docket",
                    "summons",
                    "subpoena",
                    "lawsuit",
                    "litigation",
                    "attorney",
                    "pleading",
                    "affidavit",
                    "legal",
                ]
            )
        ):
            return self._resolve_legal_subpath(entities, hint_lower, summary_lower, combined)

        # ----------------------------------------------------------------------
        # Branch 4: Property
        # ----------------------------------------------------------------------
        if (
            onnx_root == "Property"
            or is_explicit_property
            or any(
                k in combined
                for k in [
                    "vehicle",
                    "car",
                    "truck",
                    "motorcycle",
                    "auto",
                    "real estate",
                    "house",
                    "home",
                    "mortgage",
                    "deed",
                    "property tax",
                    "lease",
                    "property",
                ]
            )
        ):
            return self._resolve_property_subpath(entities, hint_lower, summary_lower, combined)

        # ----------------------------------------------------------------------
        # Branch 5: Manuals
        # ----------------------------------------------------------------------
        if (
            onnx_root == "Manuals"
            or is_explicit_manuals
            or any(k in combined for k in ["manual", "operating guide", "user guide", "instructions"])
        ):
            return self._resolve_manuals_subpath(entities, hint_lower, summary_lower, combined)

        # ----------------------------------------------------------------------
        # Branch 6: Fallback to Person if person found earlier
        # ----------------------------------------------------------------------
        if person is not None:
            return self._resolve_person_subpath(person, hint_lower, summary_lower, combined)

        # Default fallback
        return Path("Misc")

    def _resolve_person_subpath(
        self,
        person: str,
        hint_lower: str,
        summary_lower: str,
        combined: str,
    ) -> Path:
        """Resolve subfolder under People/<Person>/."""
        doc_folder = "Docuements" if (self.exact_spelling or "docuem" in hint_lower) else "Documents"

        # 1. Prioritize explicit category hint
        if any(
            k in hint_lower
            for k in [
                "medical",
                "doctor",
                "dr.",
                "dr ",
                "health",
                "clinic",
                "hospital",
                "prescription",
                "rx",
                "dental",
                "dentist",
                "vision",
                "physician",
                "vaccine",
                "vaccination",
                "appointment",
                "pharmacy",
                "patient",
            ]
        ):
            return Path("People") / person / "Medical"

        if any(
            k in hint_lower
            for k in [
                "picture",
                "photo",
                "image",
                "portrait",
                "snapshot",
                "pic",
                "gallery",
            ]
        ):
            return Path("People") / person / "Pictures"

        if any(k in hint_lower for k in ["docuement", "document"]):
            return Path("People") / person / doc_folder

        if any(
            k in hint_lower
            for k in [
                "record",
                "birth certificate",
                "transcript",
                "diploma",
                "ssn",
                "social security",
                "vital record",
                "certificate",
                "immunization",
            ]
        ):
            return Path("People") / person / "Records"

        if hint_lower in {"doc", "form", "application", "agreement", "resume", "cv", "contract", "passport"}:
            return Path("People") / person / doc_folder

        if hint_lower in {"misc", "general"}:
            return Path("People") / person / "Misc"

        # 2. Inspect summary text when hint is generic or absent
        if any(
            k in summary_lower
            for k in [
                "medical",
                "doctor",
                "dr.",
                "dr ",
                "health",
                "clinic",
                "hospital",
                "prescription",
                "rx",
                "dental",
                "dentist",
                "vision",
                "physician",
                "vaccine",
                "vaccination",
                "appointment",
                "pharmacy",
                "patient",
            ]
        ):
            return Path("People") / person / "Medical"

        if any(
            k in summary_lower
            for k in [
                "picture",
                "photo",
                "image",
                "portrait",
                "snapshot",
                "pic",
                "gallery",
            ]
        ):
            return Path("People") / person / "Pictures"

        if any(
            k in summary_lower
            for k in [
                "document",
                "doc",
                "docuement",
                "form",
                "agreement",
                "application",
                "resume",
                "cv",
                "identification",
                "id",
                "passport",
                "contract",
                "letter",
                "license",
            ]
        ):
            return Path("People") / person / doc_folder

        if any(
            k in summary_lower
            for k in [
                "record",
                "birth certificate",
                "transcript",
                "diploma",
                "school",
                "grade",
                "ssn",
                "social security",
                "vital record",
                "certificate",
                "immunization",
            ]
        ):
            return Path("People") / person / "Records"

        # Default for person
        return Path("People") / person / "Misc"

    def _resolve_financial_subpath(
        self,
        entities: list[str],
        hint_lower: str,
        summary_lower: str,
        combined: str,
    ) -> Path:
        """Resolve subfolder under Financial/."""
        receipts_name = "Reciepts" if (self.exact_spelling or "reciep" in hint_lower) else "Receipts"

        # 1. Bank Statements
        if any(
            k in combined
            for k in [
                "bank statement",
                "account statement",
                "checking statement",
                "savings statement",
            ]
        ) or (hint_lower == "bank statement"):
            if entities:
                # Pick entity: prefer entity matching summary, or non-numeric entity
                selected = entities[0]
                for ent in entities:
                    if ent.lower() in summary_lower:
                        selected = ent
                        break
                    if not ent.isdigit() and selected.isdigit():
                        selected = ent
                clean_ent = sanitize_folder_name(selected)
                if clean_ent:
                    return Path("Financial") / "Bank Statements" / clean_ent
            return Path("Financial") / "Bank Statements"

        # 2. Bills
        if any(k in combined for k in ["bill", "utility", "invoice", "power", "water bill", "electric"]):
            if any(k in combined for k in ["receipt", "reciep", "paid", "confirmation", "payment"]):
                return Path("Financial") / "Bills" / receipts_name
            if any(k in combined for k in ["due", "unpaid", "pending", "notice", "past due"]):
                return Path("Financial") / "Bills" / "Due"
            # Default for bill
            return Path("Financial") / "Bills" / "Due"

        # 3. Receipts
        if any(k in combined for k in ["receipt", "reciep"]):
            if entities:
                clean_ent = sanitize_folder_name(entities[0])
                if clean_ent:
                    return Path("Financial") / receipts_name / clean_ent
            return Path("Financial") / receipts_name

        # 4. Documents (e.g. Tax, IRS, Investment)
        if any(
            k in combined
            for k in [
                "tax",
                "w-2",
                "w2",
                "1099",
                "irs",
                "investment",
                "dividend",
                "fidelity",
                "vanguard",
                "payroll",
                "paystub",
                "stub",
                "document",
            ]
        ):
            if entities:
                clean_ent = sanitize_folder_name(entities[0])
                if clean_ent:
                    return Path("Financial") / "Documents" / clean_ent
            return Path("Financial") / "Documents"

        # Default for financial
        return Path("Financial") / "Misc"

    def _resolve_legal_subpath(
        self,
        entities: list[str],
        hint_lower: str,
        summary_lower: str,
        combined: str,
    ) -> Path:
        """Resolve subfolder under Legal/."""
        if any(
            k in combined
            for k in [
                "court",
                "case",
                "docket",
                "summons",
                "subpoena",
                "lawsuit",
                "litigation",
                "pleading",
                "affidavit",
            ]
        ):
            if entities:
                clean_case = sanitize_folder_name(entities[0])
                if clean_case:
                    return Path("Legal") / "Court" / clean_case
            return Path("Legal") / "Court"

        return Path("Legal") / "Misc"

    def _resolve_property_subpath(
        self,
        entities: list[str],
        hint_lower: str,
        summary_lower: str,
        combined: str,
    ) -> Path:
        """Resolve subfolder under Property/."""
        if any(k in combined for k in ["vehicle", "car", "truck", "motorcycle", "auto", "vin"]):
            return Path("Property") / "Vehicles"

        if any(
            k in combined
            for k in ["real estate", "house", "home", "mortgage", "deed", "property tax", "closing"]
        ):
            return Path("Property") / "Real Estate"

        return Path("Property") / "Misc"

    def _resolve_manuals_subpath(
        self,
        entities: list[str],
        hint_lower: str,
        summary_lower: str,
        combined: str,
    ) -> Path:
        """Resolve subfolder under Manuals/."""
        if any(
            k in combined
            for k in [
                "appliance",
                "dishwasher",
                "microwave",
                "oven",
                "refrigerator",
                "fridge",
                "washer",
                "dryer",
                "blender",
                "toaster",
                "stove",
                "bosch",
            ]
        ):
            return Path("Manuals") / "Appliances"

        if any(
            k in combined
            for k in [
                "electronic",
                "tv",
                "television",
                "oled",
                "sony",
                "samsung",
                "radio",
                "audio",
                "speaker",
                "computer",
                "router",
                "monitor",
                "camera",
                "headphone",
            ]
        ):
            return Path("Manuals") / "Electronics"

        if any(k in combined for k in ["vehicle", "car", "truck", "motorcycle", "auto"]):
            return Path("Manuals") / "Vehicles"

        if any(
            k in combined
            for k in [
                "tool",
                "drill",
                "saw",
                "mower",
                "dewalt",
                "milwaukee",
                "makita",
                "craftsman",
                "hammer",
                "wrench",
            ]
        ):
            return Path("Manuals") / "Tools"

        return Path("Manuals") / "General"


def resolve_destination(
    entities: list[str] | None = None,
    category_hint: str | None = None,
    summary: str | None = None,
    model_path: Path | str | None = None,
) -> Path:
    """Convenience top-level function to resolve file destination relative path."""
    return TaxonomyRouter(model_path=model_path).resolve_destination(
        entities=entities,
        category_hint=category_hint,
        summary=summary,
        model_path=model_path,
    )


def route_destination(
    summary: str | None = None,
    entities: list[str] | None = None,
    category_hint: str | None = None,
    model_path: Path | str | None = None,
) -> Path:
    """Convenience top-level function with alternative argument ordering."""
    return resolve_destination(
        entities=entities,
        category_hint=category_hint,
        summary=summary,
        model_path=model_path,
    )
