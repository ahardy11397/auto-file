"""Taxonomical destination router for the Auto-File system.

Folder structure (roots, subfolders, person names) comes from a Taxonomy
built by auto_file.core.taxonomy — either from a user-editable YAML
structure file (config key ``structure``) or from the built-in defaults.
Keyword heuristics decide the branch; the taxonomy decides the actual
folder names.
"""

from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Any
import unicodedata

from auto_file.core.taxonomy import (
    CANONICAL_PEOPLE,
    ROOT_CATEGORIES,
    Taxonomy,
    default_taxonomy,
)

logger = logging.getLogger(__name__)

__all__ = [
    "CANONICAL_PEOPLE",
    "ROOT_CATEGORIES",
    "TaxonomyRouter",
    "resolve_destination",
    "route_destination",
    "sanitize_folder_name",
]


# Slot groups: content keywords that select a branch or target folder. The
# actual folder name is looked up in the active Taxonomy by name match or
# configured keywords, so renamed/edited structure files keep working.
_PERSON_MEDICAL_SLOTS = [
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
_PERSON_PICTURE_SLOTS = [
    "picture",
    "photo",
    "image",
    "portrait",
    "snapshot",
    "pic",
    "gallery",
]
_PERSON_DOCUMENT_SLOTS = [
    "document",
    "docuement",
    "doc",
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
_PERSON_RECORD_SLOTS = [
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
_PERSON_GENERIC_DOC_HINTS = {"doc", "form", "application", "agreement", "resume", "cv", "contract", "passport"}

_ROOT_FINANCIAL_HINT_SLOTS = ["bank statement", "bill", "financial", "receipt", "tax", "w-2", "1099"]
_ROOT_LEGAL_HINT_SLOTS = ["court", "lawsuit", "legal"]
_ROOT_PROPERTY_HINT_SLOTS = ["vehicle", "real estate", "property"]
_ROOT_MANUALS_HINT_SLOTS = ["manual", "user guide"]

_FINANCIAL_SLOTS = [
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
_LEGAL_SLOTS = [
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
_PROPERTY_SLOTS = [
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
_MANUALS_SLOTS = ["manual", "operating guide", "user guide", "instructions"]

_BILLS_SLOTS = ["bill", "utility", "invoice", "power", "water bill", "electric"]
_BILLS_PAID_SLOTS = ["receipt", "reciep", "paid", "confirmation", "payment"]
_BILLS_DUE_SLOTS = ["due", "unpaid", "pending", "notice", "past due"]
_RECEIPT_SLOTS = ["receipt", "reciep"]
_FINANCIAL_DOCS_SLOTS = [
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
_COURT_SLOTS = [
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
_VEHICLE_SLOTS = ["vehicle", "car", "truck", "motorcycle", "auto", "vin"]
_REAL_ESTATE_SLOTS = ["real estate", "house", "home", "mortgage", "deed", "property tax", "closing"]
_APPLIANCE_SLOTS = [
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
_ELECTRONICS_SLOTS = [
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
_TOOLS_SLOTS = [
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
    """Routes files into relative paths according to the active Taxonomy.

    Classification uses keyword heuristics over extracted entities, a
    category hint, and a content summary; destination folder names are
    resolved against the Taxonomy (built-in defaults or a YAML structure
    file).
    """

    def __init__(
        self,
        model_path: Path | str | None = None,
        exact_spelling: bool = False,
        taxonomy: Taxonomy | None = None,
    ) -> None:
        """Initialize the taxonomy router.

        Args:
            model_path: Optional path to Laya ONNX decision model weights.
            exact_spelling: If True, the built-in default taxonomy reproduces
                the verbatim spelling from the original FOLDER_STRUCTURE.md
                (e.g. 'Docuements' and 'Reciepts'). Ignored when a custom
                taxonomy is supplied.
            taxonomy: Optional pre-built Taxonomy. When omitted, the built-in
                default taxonomy is used.
        """
        self.default_model_path = Path(model_path) if model_path is not None else None
        self.exact_spelling = exact_spelling
        self.taxonomy = taxonomy if taxonomy is not None else default_taxonomy(exact_spelling=exact_spelling)

    @property
    def doc_folder_name(self) -> str:
        folder = self.taxonomy.match_person_folder("document", "docuement")
        return folder or ("Docuements" if self.exact_spelling else "Documents")

    @property
    def receipts_folder_name(self) -> str:
        financial = self._role_root("Financial")
        folder = financial and self.taxonomy.child(financial, "receipt", "reciep")
        return folder or ("Reciepts" if self.exact_spelling else "Receipts")

    # -- taxonomy helpers --------------------------------------------------

    def _role_root(self, role: str) -> str | None:
        return self.taxonomy.root_for_role(role)

    def _fallback_path(self) -> Path:
        root = self.taxonomy.fallback_root()
        return Path(root) if root else Path("Misc")

    def _root_or_misc(self, root: str, combined: str = "") -> Path:
        """Fallback under a root: keyword-matched child, then Misc, then root."""
        hit = self.taxonomy.child_by_keywords(root, combined)
        if hit:
            return Path(root) / hit
        misc = self.taxonomy.misc_child(root)
        return Path(root) / misc if misc else Path(root)

    # -- routing entry points ----------------------------------------------

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
            if hasattr(raw_out, "tolist"):
                raw_out = raw_out.tolist()

            if isinstance(raw_out, (list, tuple)) and len(raw_out) > 0:
                first_item = raw_out[0]
                if isinstance(first_item, (list, tuple)):
                    scores = list(first_item)
                else:
                    scores = list(raw_out)

                if scores and len(scores) == len(self.taxonomy.roots):
                    max_idx = max(range(len(scores)), key=lambda i: scores[i])
                    return self.taxonomy.roots[max_idx]

            if isinstance(raw_out, str) and raw_out in self.taxonomy.roots:
                return raw_out

            return None
        except Exception as exc:
            logger.debug("ONNX taxonomy inference failed, falling back: %s", exc)
            return None

    def _find_person(self, entities: list[str], hint: str, summary: str) -> str | None:
        """Find a canonical person name matching entities, summary, or hint."""
        people = self.taxonomy.people
        if not people:
            return None

        # 1. Inspect explicit entities list
        for entity in entities:
            entity_norm = entity.strip().lower()
            for person in people:
                if person.lower() == entity_norm:
                    return person

        # 2. Inspect summary and hint using whole-word matching
        combined_text = f"{hint} {summary}".lower()
        for person in people:
            pattern = rf"\b{re.escape(person.lower())}\b"
            if re.search(pattern, combined_text):
                return person

        return None

    def _trigger(
        self,
        root: str | None,
        onnx_root: str | None,
        explicit: bool,
        slots: list[str],
        combined: str,
    ) -> str | None:
        """Return the root name when a file triggers its branch: ONNX vote,
        explicit hint, built-in slot keywords, or extra keywords declared
        on the root. Returns None otherwise."""
        if root is None:
            return None
        if (
            onnx_root == root
            or explicit
            or any(k in combined for k in slots)
            or any(k in combined for k in self.taxonomy.root_keywords.get(root, []))
        ):
            return root
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
        person_root = self.taxonomy.person_root

        # Check if root is explicitly constrained to non-People by hints
        is_explicit_financial = any(k in hint_lower for k in _ROOT_FINANCIAL_HINT_SLOTS)
        is_explicit_legal = any(k in hint_lower for k in _ROOT_LEGAL_HINT_SLOTS)
        is_explicit_property = any(k in hint_lower for k in _ROOT_PROPERTY_HINT_SLOTS)
        is_explicit_manuals = any(k in hint_lower for k in _ROOT_MANUALS_HINT_SLOTS)

        # ----------------------------------------------------------------------
        # Branch 1: People
        # ----------------------------------------------------------------------
        if person is not None and person_root is not None and not (
            is_explicit_financial or is_explicit_legal or is_explicit_property or is_explicit_manuals
        ):
            return self._resolve_person_subpath(person_root, person, hint_lower, summary_lower)

        # If onnx predicted People and person is known
        if person_root is not None and onnx_root == person_root and person is not None:
            return self._resolve_person_subpath(person_root, person, hint_lower, summary_lower)

        # ----------------------------------------------------------------------
        # Branch 2: Financial
        # ----------------------------------------------------------------------
        financial = self._role_root("Financial")
        financial = self._trigger(financial, onnx_root, is_explicit_financial, _FINANCIAL_SLOTS, combined)
        if financial is not None:
            return self._resolve_financial_subpath(financial, entities, hint_lower, summary_lower, combined)

        # ----------------------------------------------------------------------
        # Branch 3: Legal
        # ----------------------------------------------------------------------
        legal = self._role_root("Legal")
        legal = self._trigger(legal, onnx_root, is_explicit_legal, _LEGAL_SLOTS, combined)
        if legal is not None:
            return self._resolve_legal_subpath(legal, entities, hint_lower, summary_lower, combined)

        # ----------------------------------------------------------------------
        # Branch 4: Property
        # ----------------------------------------------------------------------
        property_root = self._role_root("Property")
        property_root = self._trigger(property_root, onnx_root, is_explicit_property, _PROPERTY_SLOTS, combined)
        if property_root is not None:
            return self._resolve_property_subpath(property_root, entities, hint_lower, summary_lower, combined)

        # ----------------------------------------------------------------------
        # Branch 5: Manuals
        # ----------------------------------------------------------------------
        manuals = self._role_root("Manuals")
        manuals = self._trigger(manuals, onnx_root, is_explicit_manuals, _MANUALS_SLOTS, combined)
        if manuals is not None:
            return self._resolve_manuals_subpath(manuals, entities, hint_lower, summary_lower, combined)

        # ----------------------------------------------------------------------
        # Branch 6: Fallback to Person if person found earlier
        # ----------------------------------------------------------------------
        if person is not None and person_root is not None:
            return self._resolve_person_subpath(person_root, person, hint_lower, summary_lower)

        # Default fallback
        return self._fallback_path()

    def _resolve_person_subpath(
        self,
        person_root: str,
        person: str,
        hint_lower: str,
        summary_lower: str,
    ) -> Path:
        """Resolve subfolder under <person_root>/<Person>/."""
        taxonomy = self.taxonomy

        def folder_for(slots: list[str]) -> str | None:
            return taxonomy.match_person_folder(*slots)

        # 1. Prioritize explicit category hint
        if any(k in hint_lower for k in _PERSON_MEDICAL_SLOTS):
            folder = folder_for(_PERSON_MEDICAL_SLOTS)
            if folder:
                return Path(person_root) / person / folder

        if any(k in hint_lower for k in _PERSON_PICTURE_SLOTS):
            folder = folder_for(_PERSON_PICTURE_SLOTS)
            if folder:
                return Path(person_root) / person / folder

        if any(k in hint_lower for k in ["docuement", "document"]) or hint_lower in _PERSON_GENERIC_DOC_HINTS:
            folder = folder_for(_PERSON_DOCUMENT_SLOTS)
            if folder:
                return Path(person_root) / person / folder

        if any(k in hint_lower for k in _PERSON_RECORD_SLOTS):
            folder = folder_for(_PERSON_RECORD_SLOTS)
            if folder:
                return Path(person_root) / person / folder

        if hint_lower in {"misc", "general"}:
            misc = taxonomy.person_misc_folder()
            if misc:
                return Path(person_root) / person / misc

        # 2. Inspect summary text when hint is generic or absent
        if any(k in summary_lower for k in _PERSON_MEDICAL_SLOTS):
            folder = folder_for(_PERSON_MEDICAL_SLOTS)
            if folder:
                return Path(person_root) / person / folder

        if any(k in summary_lower for k in _PERSON_PICTURE_SLOTS):
            folder = folder_for(_PERSON_PICTURE_SLOTS)
            if folder:
                return Path(person_root) / person / folder

        if any(k in summary_lower for k in _PERSON_DOCUMENT_SLOTS):
            folder = folder_for(_PERSON_DOCUMENT_SLOTS)
            if folder:
                return Path(person_root) / person / folder

        if any(k in summary_lower for k in _PERSON_RECORD_SLOTS):
            folder = folder_for(_PERSON_RECORD_SLOTS)
            if folder:
                return Path(person_root) / person / folder

        # Default for person
        misc = taxonomy.person_misc_folder()
        return Path(person_root) / person / misc if misc else Path(person_root) / person

    def _resolve_financial_subpath(
        self,
        financial: str,
        entities: list[str],
        hint_lower: str,
        summary_lower: str,
        combined: str,
    ) -> Path:
        """Resolve subfolder under Financial/."""
        taxonomy = self.taxonomy

        def first_entity() -> str | None:
            if not entities:
                return None
            return sanitize_folder_name(entities[0]) or None

        # 1. Bank Statements
        bank = taxonomy.child(financial, "bank statement")
        if bank and (
            any(
                k in combined
                for k in ["bank statement", "account statement", "checking statement", "savings statement"]
            )
            or hint_lower == "bank statement"
        ):
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
                    return Path(financial) / bank / clean_ent
            return Path(financial) / bank

        # 2. Bills
        bills = taxonomy.child(financial, "bill")
        if bills and any(k in combined for k in _BILLS_SLOTS):
            if any(k in combined for k in _BILLS_PAID_SLOTS):
                receipt_folder = taxonomy.grandchild(financial, bills, *_RECEIPT_SLOTS)
                if receipt_folder:
                    return Path(financial) / bills / receipt_folder
            due_folder = taxonomy.grandchild(financial, bills, "due", "unpaid", "pending")
            if due_folder:
                return Path(financial) / bills / due_folder
            # Default for bill
            return Path(financial) / bills

        # 3. Receipts
        receipts = taxonomy.child(financial, *_RECEIPT_SLOTS)
        if receipts and any(k in combined for k in _RECEIPT_SLOTS):
            clean_ent = first_entity()
            if clean_ent:
                return Path(financial) / receipts / clean_ent
            return Path(financial) / receipts

        # 4. Documents (e.g. Tax, IRS, Investment)
        documents = taxonomy.child(financial, "document")
        if documents and any(k in combined for k in _FINANCIAL_DOCS_SLOTS):
            clean_ent = first_entity()
            if clean_ent:
                return Path(financial) / documents / clean_ent
            return Path(financial) / documents

        # Default for financial
        return self._root_or_misc(financial, combined)

    def _resolve_legal_subpath(
        self,
        legal: str,
        entities: list[str],
        hint_lower: str,
        summary_lower: str,
        combined: str,
    ) -> Path:
        """Resolve subfolder under Legal/."""
        court = self.taxonomy.child(legal, "court")
        if court and any(k in combined for k in _COURT_SLOTS):
            if entities:
                clean_case = sanitize_folder_name(entities[0])
                if clean_case:
                    return Path(legal) / court / clean_case
            return Path(legal) / court

        return self._root_or_misc(legal, combined)

    def _resolve_property_subpath(
        self,
        property_root: str,
        entities: list[str],
        hint_lower: str,
        summary_lower: str,
        combined: str,
    ) -> Path:
        """Resolve subfolder under Property/."""
        vehicles = self.taxonomy.child(property_root, "vehicle")
        if vehicles and any(k in combined for k in _VEHICLE_SLOTS):
            return Path(property_root) / vehicles

        real_estate = self.taxonomy.child(property_root, "real estate")
        if real_estate and any(k in combined for k in _REAL_ESTATE_SLOTS):
            return Path(property_root) / real_estate

        return self._root_or_misc(property_root, combined)

    def _resolve_manuals_subpath(
        self,
        manuals: str,
        entities: list[str],
        hint_lower: str,
        summary_lower: str,
        combined: str,
    ) -> Path:
        """Resolve subfolder under Manuals/."""
        taxonomy = self.taxonomy

        appliances = taxonomy.child(manuals, "appliance")
        if appliances and any(k in combined for k in _APPLIANCE_SLOTS):
            return Path(manuals) / appliances

        electronics = taxonomy.child(manuals, "electronic")
        if electronics and any(k in combined for k in _ELECTRONICS_SLOTS):
            return Path(manuals) / electronics

        vehicles = taxonomy.child(manuals, "vehicle")
        if vehicles and any(k in combined for k in _VEHICLE_SLOTS):
            return Path(manuals) / vehicles

        tools = taxonomy.child(manuals, "tool")
        if tools and any(k in combined for k in _TOOLS_SLOTS):
            return Path(manuals) / tools

        return self._root_or_misc(manuals, combined)


def resolve_destination(
    entities: list[str] | None = None,
    category_hint: str | None = None,
    summary: str | None = None,
    model_path: Path | str | None = None,
    structure: Path | str | None = None,
) -> Path:
    """Convenience top-level function to resolve file destination relative path."""
    taxonomy = None
    if structure is not None:
        from auto_file.core.taxonomy import load_taxonomy

        taxonomy = load_taxonomy(structure)
    return TaxonomyRouter(model_path=model_path, taxonomy=taxonomy).resolve_destination(
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
    structure: Path | str | None = None,
) -> Path:
    """Convenience top-level function with alternative argument ordering."""
    return resolve_destination(
        entities=entities,
        category_hint=category_hint,
        summary=summary,
        model_path=model_path,
        structure=structure,
    )
