"""Configurable folder-structure taxonomy for the Auto-File system.

The destination folder tree is loaded from a user-editable YAML file
(config key ``structure``) so routing is data-driven instead of hardcoded.
When no structure file is configured, a built-in default taxonomy — matching
the original FOLDER_STRUCTURE.md — keeps behavior unchanged.

YAML schema (all keys optional unless noted)::

    # Optional: person folder names. Defaults to the children of the
    # "People" root when that root exists.
    people:
      - Alpha
      - Bravo

    # Optional: subfolders created for each person.
    person_subfolders: [Records, Medical, Documents, Pictures, Misc]

    # Optional: which root holds the per-person folders (default "People").
    person_root: People

    # Optional: explicit role for a renamed root, so keyword routing finds it.
    # Allowed roles: People, Financial, Legal, Property, Manuals, Misc.
    roots:
      Money:
        role: Financial
        keywords: [money]       # optional extra routing words for this root
        subfolders:
          Bank Statements:      # plain child folder
            subfolders: []      # optional grandchild folders
          Receipts:
            keywords: [reciept] # optional extra matching words for this child
          Bills:
            subfolders: [Receipts, Due]
      Misc: {}                  # a root with no subfolders
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
import unicodedata
from pathlib import Path

import yaml

CANONICAL_PEOPLE: list[str] = ["Alpha", "Bravo", "Charlie", "Delta", "Echo"]

ROOT_CATEGORIES: list[str] = [
    "People",
    "Financial",
    "Legal",
    "Property",
    "Manuals",
    "Misc",
]

DEFAULT_PERSON_SUBFOLDERS: list[str] = [
    "Records",
    "Medical",
    "Documents",
    "Pictures",
    "Misc",
]

_MISC_NAMES = {"misc", "miscellaneous", "general", "other", "others", "uncategorized"}
_MIN_SUBSTR_LEN = 4


def _norm(name: str) -> str:
    """Normalize a folder name or keyword for fuzzy matching."""
    text = name.strip().lower()
    text = text.replace("-", " ").replace("_", " ")
    return " ".join(text.split())


def _matches(candidate: str, slots: list[str], extra_keywords: list[str] | None = None) -> bool:
    """Return True when a folder name (or its keywords) matches any slot."""
    norm = _norm(candidate)
    for slot in slots:
        s = _norm(slot)
        if not s:
            continue
        if s == norm:
            return True
        if len(s) >= _MIN_SUBSTR_LEN and (s in norm or norm in s):
            return True
    for keyword in extra_keywords or []:
        k = _norm(keyword)
        if k and any(k == _norm(s) for s in slots):
            return True
    return False


@dataclass
class Taxonomy:
    """A folder tree used to route files inside the destination root."""

    roots: list[str]
    children: dict[str, list[str]] = field(default_factory=dict)
    child_keywords: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    grandchildren: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    root_keywords: dict[str, list[str]] = field(default_factory=dict)
    person_root: str | None = None
    person_subfolders: list[str] = field(default_factory=lambda: list(DEFAULT_PERSON_SUBFOLDERS))
    people: list[str] = field(default_factory=list)
    roles: dict[str, str] = field(default_factory=dict)
    # Child folders (keyed "root/child" normalized) that accept a dynamic
    # final component — the "by entity" folders (Bills/<vendor>, Court/<case>).
    dynamic_children: dict[str, set[str]] = field(default_factory=dict)

    # -- lookups used by the router --------------------------------------

    def root_for_role(self, role: str) -> str | None:
        """Find the root serving a canonical role (e.g. 'Financial').

        Matches either the root's own name or an explicit 'role' declared
        for it in the structure file.
        """
        target = _norm(role)
        for root in self.roots:
            if _norm(root) == target:
                return root
            if _norm(self.roles.get(root, "")) == target:
                return root
        return None

    def fallback_root(self) -> str | None:
        """Preferred catch-all root: one named Misc, else the last root."""
        for root in self.roots:
            if _norm(root) in _MISC_NAMES:
                return root
        return self.roots[-1] if self.roots else None

    def child(self, root: str, *slots: str) -> str | None:
        """Find a direct child of ``root`` matching any slot word."""
        return self._match(self.children.get(root, []), self.child_keywords.get(root, {}), list(slots))

    def grandchild(self, root: str, child: str, *slots: str) -> str | None:
        """Find a grandchild of ``root/child`` matching any slot word."""
        return self._match(self.grandchildren.get(root, {}).get(child, []), {}, list(slots))

    def folder_by_filename(self, root: str, filename: str) -> tuple[str, ...] | None:
        """Find a child or grandchild of ``root`` whose name appears in a filename.

        Scanned documents often have no extractable text, leaving the filename
        as the only signal (e.g. 'OneMain Financial.pdf' -> Bills/OneMain).
        Grandchildren are preferred over their parent child. Short names
        (under 5 characters) are skipped to avoid false matches.
        """
        norm_file = _norm(filename)
        if not norm_file:
            return None
        for child in self.children.get(root, []):
            grandkids = self.grandchildren.get(root, {}).get(child, [])
            for descendant in list(grandkids) + [child]:
                n = _norm(descendant)
                if len(n) >= 5 and n in norm_file:
                    if descendant == child:
                        return (child,)
                    return (child, descendant)
        return None

    def all_paths(self) -> list[str]:
        """Every folder path in the tree, as 'Root/Child/Grandchild' strings."""
        out: list[str] = []
        for root in self.roots:
            out.append(root)
            for child in self.children.get(root, []):
                out.append(f"{root}/{child}")
                for grandchild in self.grandchildren.get(root, {}).get(child, []):
                    out.append(f"{root}/{child}/{grandchild}")
        return out

    def is_valid_folder(self, path: str) -> str | None:
        """Validate an LLM-chosen folder path against the tree.

        Returns the canonical path when every component matches a tree node
        (case/spacing-insensitive), allowing one dynamic final component
        under a folder marked 'dynamic: true'. Returns None when invalid.
        """
        parts = [_norm(p) for p in path.split("/") if p.strip()]
        if not parts:
            return None
        root = next((r for r in self.roots if _norm(r) == parts[0]), None)
        if root is None:
            return None
        if len(parts) == 1:
            return root
        child = next((c for c in self.children.get(root, []) if _norm(c) == parts[1]), None)
        if child is None:
            return None
        if len(parts) == 2:
            return f"{root}/{child}"
        if len(parts) > 3:
            return None
        grandchild = next(
            (g for g in self.grandchildren.get(root, {}).get(child, []) if _norm(g) == parts[2]),
            None,
        )
        if grandchild is not None:
            return f"{root}/{child}/{grandchild}"
        # Dynamic final component under a 'by entity' folder
        if child_key(child) in self.dynamic_children.get(child_key(root), set()):
            entity = sanitize_folder_name(parts[2])
            if entity:
                return f"{root}/{child}/{entity}"
        return None

    def misc_child(self, root: str) -> str | None:
        """Find the catch-all child of ``root`` (Misc/General/Other), if any."""
        for child in self.children.get(root, []):
            if _norm(child) in _MISC_NAMES:
                return child
        return None

    def child_by_keywords(self, root: str, text: str) -> str | None:
        """Find a direct child of ``root`` whose declared keywords appear in text."""
        norm_text = _norm(text)
        if not norm_text:
            return None
        keywords = self.child_keywords.get(root, {})
        for child in self.children.get(root, []):
            for keyword in keywords.get(child_key(child), []):
                k = _norm(keyword)
                if k and k in norm_text:
                    return child
        return None

    def match_person_folder(self, *slots: str) -> str | None:
        """Find a per-person subfolder matching any slot word.

        Checks ``person_subfolders`` first, then the declared children of
        the person root (which may carry their own keywords).
        """
        hit = self._match(self.person_subfolders, {}, list(slots))
        if hit:
            return hit
        if self.person_root:
            hit = self.child(self.person_root, *slots)
            if hit and _norm(hit) not in {p.lower() for p in self.people}:
                return hit
        return None

    def person_misc_folder(self) -> str | None:
        """Find the catch-all per-person subfolder (Misc/General), if any."""
        for folder in self.person_subfolders:
            if _norm(folder) in _MISC_NAMES:
                return folder
        return None

    @staticmethod
    def _match(names: list[str], keywords: dict[str, list[str]], slots: list[str]) -> str | None:
        for name in names:
            if _matches(name, slots, keywords.get(child_key(name))):
                return name
        return None


def sanitize_folder_name(name: str) -> str:
    """Sanitize an entity, case, or account string for directory path safety."""
    if not name:
        return ""
    text = unicodedata.normalize("NFKD", name)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\-.]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def child_key(name: str) -> str:
    """Stable dict key for a folder name inside parsed YAML structures."""
    return _norm(name).replace(" ", "_")


def default_taxonomy(exact_spelling: bool = False) -> Taxonomy:
    """Build the built-in taxonomy matching the original FOLDER_STRUCTURE.md.

    ``exact_spelling`` reproduces the verbatim (misspelled) folder names from
    the original file ('Docuements', 'Reciepts').
    """
    doc = "Docuements" if exact_spelling else "Documents"
    receipts = "Reciepts" if exact_spelling else "Receipts"

    roots = list(ROOT_CATEGORIES)
    children: dict[str, list[str]] = {
        "People": list(CANONICAL_PEOPLE),
        "Financial": ["Bank Statements", "Bills", receipts, "Documents", "Misc"],
        "Legal": ["Court", "Misc"],
        "Property": ["Vehicles", "Real Estate", "Misc"],
        "Manuals": ["Appliances", "Electronics", "Vehicles", "Tools", "General"],
        "Misc": [],
    }
    grandchildren: dict[str, dict[str, list[str]]] = {
        "Financial": {"Bills": [receipts, "Due"]},
    }
    return Taxonomy(
        roots=roots,
        children=children,
        grandchildren=grandchildren,
        person_root="People",
        person_subfolders=[
            "Records",
            "Medical",
            doc,
            "Pictures",
            "Misc",
        ],
        people=list(CANONICAL_PEOPLE),
    )


def _parse_folder_spec(
    spec: object,
) -> tuple[list[str], dict[str, list[str]], dict[str, list[str]], set[str]]:
    """Parse a folder mapping into (children, child keywords, grandchildren,
    dynamic children — folders marked 'dynamic: true' that accept a free
    final component, e.g. Bills/<vendor>)."""
    children: list[str] = []
    child_keywords: dict[str, list[str]] = {}
    grandchildren: dict[str, list[str]] = {}
    dynamic: set[str] = set()

    if spec is None:
        return children, child_keywords, grandchildren, dynamic

    if isinstance(spec, list):
        for item in spec:
            children.append(str(item))
        return children, child_keywords, grandchildren, dynamic

    if not isinstance(spec, dict):
        raise ValueError(f"Invalid folder spec: {spec!r}")

    subfolders = spec.get("subfolders", spec)
    if subfolders is None:
        subfolders = {}
    if not isinstance(subfolders, dict):
        raise ValueError(f"Invalid 'subfolders' value: {subfolders!r}")

    for name, child_spec in subfolders.items():
        child_name = str(name)
        children.append(child_name)
        if isinstance(child_spec, dict):
            keywords = child_spec.get("keywords") or []
            if keywords:
                child_keywords[child_key(child_name)] = [str(k) for k in keywords]
            if child_spec.get("dynamic"):
                dynamic.add(child_key(child_name))
            subs = child_spec.get("subfolders") or []
            if isinstance(subs, dict):
                # Mapping form: {Grandchild: {...}} — preserve declaration order.
                grandchildren[child_name] = [str(s) for s in subs]
            elif isinstance(subs, (list, tuple)):
                grandchildren[child_name] = [str(s) for s in subs]
        elif isinstance(child_spec, (list, tuple)):
            grandchildren[child_name] = [str(s) for s in child_spec]

    return children, child_keywords, grandchildren, dynamic


def load_taxonomy(path: Path | str) -> Taxonomy:
    """Load a taxonomy from a YAML structure file.

    Raises FileNotFoundError when the file is missing and ValueError when the
    YAML is malformed or lacks a 'roots' mapping.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Folder structure file not found: {file_path}")

    try:
        data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {file_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Folder structure file must contain a YAML mapping: {file_path}")

    roots_spec = data.get("roots")
    if not isinstance(roots_spec, dict) or not roots_spec:
        raise ValueError(f"Folder structure file must define a non-empty 'roots' mapping: {file_path}")

    roots: list[str] = []
    children: dict[str, list[str]] = {}
    child_keywords: dict[str, dict[str, list[str]]] = {}
    grandchildren: dict[str, dict[str, list[str]]] = {}
    root_keywords: dict[str, list[str]] = {}
    roles: dict[str, str] = {}
    dynamic_children: dict[str, set[str]] = {}

    for root_name, root_spec in roots_spec.items():
        root = str(root_name)
        roots.append(root)
        if isinstance(root_spec, dict):
            keywords = root_spec.get("keywords") or []
            if keywords:
                root_keywords[root] = [str(k) for k in keywords]
            role = root_spec.get("role")
            if role:
                roles[root] = str(role)
            folder_spec = root_spec.get("subfolders", root_spec)
            if isinstance(folder_spec, dict):
                folder_spec = {k: v for k, v in folder_spec.items() if k not in ("keywords", "role")}
        else:
            folder_spec = root_spec
        kids, ck, gc, dyn = _parse_folder_spec(folder_spec)
        children[root] = kids
        if ck:
            child_keywords[root] = ck
        if gc:
            grandchildren[root] = gc
        if dyn:
            dynamic_children[child_key(root)] = dyn

    taxonomy = Taxonomy(
        roots=roots,
        children=children,
        child_keywords=child_keywords,
        grandchildren=grandchildren,
        root_keywords=root_keywords,
        roles=roles,
        dynamic_children=dynamic_children,
    )

    person_root = data.get("person_root")
    if person_root:
        taxonomy.person_root = str(person_root)
    else:
        for root in roots:
            if _norm(root) == "people":
                taxonomy.person_root = root
                break

    people = data.get("people")
    if isinstance(people, (list, tuple)) and people:
        taxonomy.people = [str(p) for p in people]
    elif taxonomy.person_root is not None:
        taxonomy.people = list(children.get(taxonomy.person_root, []))

    person_subfolders = data.get("person_subfolders")
    if isinstance(person_subfolders, (list, tuple)) and person_subfolders:
        taxonomy.person_subfolders = [str(p) for p in person_subfolders]

    return taxonomy


def taxonomy_to_yaml(taxonomy: Taxonomy | None = None) -> str:
    """Render a taxonomy (default: built-in) as a commented YAML structure file."""
    tax = taxonomy or default_taxonomy()

    lines: list[str] = [
        "# Auto-File folder structure",
        "#",
        "# This file defines where auto-file puts files. Edit freely — routing",
        "# follows whatever tree is written here. It is independent of the",
        "# destination root: point auto-file at it with:",
        "#   auto-file config set structure <path to this file>",
        "#",
        "# Person folders. Routing matches these names against names found in",
        "# document content.",
    ]

    if tax.people:
        lines.append("people:")
        lines.extend(f"  - {person}" for person in tax.people)
    else:
        lines.append("people: []")

    lines.append("")
    lines.append("# Subfolders created for each person.")
    lines.append("person_subfolders:")
    lines.extend(f"  - {folder}" for folder in tax.person_subfolders)

    if tax.person_root:
        lines.append("")
        lines.append(f"person_root: {tax.person_root}")

    lines.append("")
    lines.append("# Top-level folders inside your destination root, and their subfolders.")
    lines.append("# Optional 'keywords' add extra words that route files there.")
    lines.append("roots:")

    def _emit(name: str, depth: int, subfolders: list[str], keywords: list[str]) -> None:
        indent = "  " * depth
        if subfolders or keywords:
            lines.append(f"{indent}{name}:")
            if keywords:
                lines.append(f"{indent}  keywords: [{', '.join(keywords)}]")
            if subfolders:
                lines.append(f"{indent}  subfolders:")
                for sub in subfolders:
                    lines.append(f"{indent}    {sub}: []")
        else:
            lines.append(f"{indent}{name}: []")

    for root in tax.roots:
        root_kws = tax.root_keywords.get(root, [])
        role = tax.roles.get(root)
        kids = tax.children.get(root, [])
        if kids or root_kws or role:
            lines.append(f"  {root}:")
            if role:
                lines.append(f"    role: {role}")
            if root_kws:
                lines.append(f"    keywords: [{', '.join(root_kws)}]")
            if kids:
                lines.append("    subfolders:")
                for kid in kids:
                    _emit(
                        kid,
                        3,
                        tax.grandchildren.get(root, {}).get(kid, []),
                        tax.child_keywords.get(root, {}).get(kid, []),
                    )
        else:
            lines.append(f"  {root}: []")

    return "\n".join(lines) + "\n"
