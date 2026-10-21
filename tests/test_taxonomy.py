"""Tests for the YAML folder-structure taxonomy and config-driven routing."""

import json
import textwrap
from pathlib import Path

from typer.testing import CliRunner

from auto_file.cli import app
from auto_file.config import get_structure_path, set_config_value
from auto_file.core.executor import FilePipelineExecutor
from auto_file.core.router import TaxonomyRouter
from auto_file.core.taxonomy import (
    Taxonomy,
    default_taxonomy,
    load_taxonomy,
    sanitize_folder_name,
    taxonomy_to_yaml,
)

runner = CliRunner()


CUSTOM_YAML = textwrap.dedent(
    """
    people: [Wanda, Gus]
    person_subfolders: [Health, Papers, Misc]
    person_root: Family
    roots:
      Family:
        Papers: {keywords: [document, record]}
        Misc: {}
      Money:
        role: Financial
        subfolders:
          Bank Statements: {}
          Purchases: {keywords: [receipt]}
          Misc: {}
      Misc: {}
    """
)


def _write_custom_structure(tmp_path: Path) -> Path:
    structure = tmp_path / "structure.yaml"
    structure.write_text(CUSTOM_YAML, encoding="utf-8")
    return structure


DYNAMIC_YAML = textwrap.dedent(
    """
    people: [Alpha]
    person_subfolders: [Records, Misc]
    roots:
      Financial:
        role: Financial
        subfolders:
          Bills:
            dynamic: true
            subfolders: [Receipts, Due]
          Misc: {}
      Misc: {}
    """
)


def _write_dynamic_structure(tmp_path: Path) -> Path:
    structure = tmp_path / "dynamic.yaml"
    structure.write_text(DYNAMIC_YAML, encoding="utf-8")
    return structure


# ==============================================================================
# Default taxonomy
# ==============================================================================


def test_default_taxonomy_matches_builtin_constants():
    tax = default_taxonomy()
    assert tax.roots == ["People", "Financial", "Legal", "Property", "Manuals", "Misc"]
    assert tax.people == ["Alpha", "Bravo", "Charlie", "Delta", "Echo"]
    assert tax.person_root == "People"
    assert "Medical" in tax.person_subfolders


def test_default_taxonomy_exact_spelling():
    tax = default_taxonomy(exact_spelling=True)
    assert "Docuements" in tax.person_subfolders
    assert "Reciepts" in tax.children["Financial"]


# ==============================================================================
# YAML loading
# ==============================================================================


def test_load_taxonomy_custom_yaml(tmp_path):
    tax = load_taxonomy(_write_custom_structure(tmp_path))
    assert tax.roots == ["Family", "Money", "Misc"]
    assert tax.people == ["Wanda", "Gus"]
    assert tax.person_root == "Family"
    assert tax.person_subfolders == ["Health", "Papers", "Misc"]
    assert tax.root_for_role("Financial") == "Money"
    assert tax.child("Money", "bank statement") == "Bank Statements"


def test_load_taxonomy_missing_file(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        load_taxonomy(tmp_path / "nope.yaml")


def test_load_taxonomy_missing_roots(tmp_path):
    import pytest

    bad = tmp_path / "bad.yaml"
    bad.write_text("people: [Alpha]\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_taxonomy(bad)


def test_taxonomy_to_yaml_round_trip(tmp_path):
    tax = default_taxonomy()
    text = taxonomy_to_yaml(tax)
    structure = tmp_path / "structure.yaml"
    structure.write_text(text, encoding="utf-8")

    loaded = load_taxonomy(structure)
    assert loaded.roots == tax.roots
    assert loaded.people == tax.people
    assert loaded.person_subfolders == tax.person_subfolders
    assert loaded.person_root == tax.person_root
    assert loaded.children["Financial"] == tax.children["Financial"]
    assert loaded.grandchildren["Financial"]["Bills"] == tax.grandchildren["Financial"]["Bills"]


# ==============================================================================
# Folder tree enumeration and LLM path validation
# ==============================================================================


def test_all_paths_covers_roots_children_grandchildren_and_people():
    """all_paths() is the single source of truth for the LLM prompt."""
    tax = default_taxonomy()
    paths = tax.all_paths()

    assert "People" in paths
    assert "Financial/Bills" in paths
    assert "Financial/Bills/Receipts" in paths
    # Per-person folders are part of the tree the model may choose from.
    assert "People/Alpha" in paths
    assert "People/Alpha/Medical" in paths
    # No duplicates
    assert len(paths) == len(set(paths))


def test_all_paths_uses_custom_people(tmp_path):
    tax = load_taxonomy(_write_custom_structure(tmp_path))
    paths = tax.all_paths()
    assert "Family/Wanda" in paths
    assert "Family/Wanda/Health" in paths
    assert "Money/Bank Statements" in paths


def test_every_listed_path_is_accepted_by_the_validator(tmp_path):
    """The model can never be asked to choose a path the validator rejects."""
    for tax in (default_taxonomy(), load_taxonomy(_write_dynamic_structure(tmp_path))):
        for path in tax.all_paths():
            assert tax.is_valid_folder(path) is not None, path


def test_is_valid_folder_accepts_person_subfolder():
    tax = default_taxonomy()
    assert tax.is_valid_folder("People/Alpha/Medical") == "People/Alpha/Medical"


def test_is_valid_folder_rejects_unknown_person():
    tax = default_taxonomy()
    assert tax.is_valid_folder("People/Zeta/Medical") is None


def test_is_valid_folder_rejects_path_traversal():
    """'..' must never resolve to a folder outside the destination root."""
    tax = default_taxonomy()
    assert tax.is_valid_folder("Financial/../etc") is None
    assert tax.is_valid_folder("Financial/Bills/..") is None
    assert tax.is_valid_folder("../etc/passwd") is None


def test_is_valid_folder_rejects_paths_deeper_than_the_tree():
    tax = default_taxonomy()
    assert tax.is_valid_folder("Financial/Bills/Receipts/Extra") is None


def test_is_valid_folder_is_case_insensitive():
    tax = default_taxonomy()
    assert tax.is_valid_folder("financial/bills") == "Financial/Bills"
    assert tax.is_valid_folder("PEOPLE/alpha") == "People/Alpha"


def test_is_valid_folder_accepts_dynamic_component(tmp_path):
    """A 'dynamic: true' folder accepts one new final component."""
    tax = load_taxonomy(_write_dynamic_structure(tmp_path))
    assert tax.is_valid_folder("Financial/Bills/Acme Corp") == "Financial/Bills/Acme_Corp"
    # The display case the model chose is preserved (not lowercased).
    assert tax.is_valid_folder("Financial/Bills/AcmeCorp") == "Financial/Bills/AcmeCorp"


def test_is_valid_folder_rejects_dot_component_in_dynamic_folder(tmp_path):
    tax = load_taxonomy(_write_dynamic_structure(tmp_path))
    assert tax.is_valid_folder("Financial/Bills/..") is None
    assert tax.is_valid_folder("Financial/Bills/.") is None


def test_dynamic_paths_lists_dynamic_folders(tmp_path):
    tax = load_taxonomy(_write_dynamic_structure(tmp_path))
    assert tax.dynamic_paths() == ["Financial/Bills"]
    # Folders that are not dynamic are not advertised as such.
    assert "Financial/Misc" not in tax.dynamic_paths()


def test_dynamic_paths_empty_for_default_taxonomy():
    assert default_taxonomy().dynamic_paths() == []


def test_taxonomy_to_yaml_emits_dynamic_flag(tmp_path):
    tax = load_taxonomy(_write_dynamic_structure(tmp_path))
    text = taxonomy_to_yaml(tax)
    assert "dynamic: true" in text

    # And the flag survives a round trip through the file.
    structure = tmp_path / "roundtrip.yaml"
    structure.write_text(text, encoding="utf-8")
    assert load_taxonomy(structure).dynamic_paths() == ["Financial/Bills"]


def test_sanitize_folder_name_rejects_dot_and_dotdot():
    assert sanitize_folder_name("..") == ""
    assert sanitize_folder_name(".") == ""
    assert sanitize_folder_name("Acme Corp") == "Acme_Corp"


def test_dynamic_taxonomy_grandchildren_still_win_over_dynamic_component(tmp_path):
    """A declared grandchild is preferred over inventing a new folder."""
    tax = load_taxonomy(_write_dynamic_structure(tmp_path))
    assert tax.is_valid_folder("Financial/Bills/Receipts") == "Financial/Bills/Receipts"


def test_custom_taxonomy_is_valid_folder_unknown_root():
    tax = Taxonomy(roots=["Financial"], children={"Financial": ["Bills"]})
    assert tax.is_valid_folder("Legal/Court") is None
    assert tax.is_valid_folder("Financial/Bills") == "Financial/Bills"


# ==============================================================================
# Router driven by a structure file
# ==============================================================================


def test_router_uses_custom_people_and_folders(tmp_path):
    router = TaxonomyRouter(taxonomy=load_taxonomy(_write_custom_structure(tmp_path)))

    # Custom person, custom medical folder name
    assert router.resolve_destination(entities=["Wanda"], category_hint="medical") == Path("Family/Wanda/Health")
    # Summary-driven medical routing
    assert router.resolve_destination(entities=["Gus"], summary="doctor visit notes") == Path("Family/Gus/Health")
    # Child matched via configured keywords (Papers)
    assert router.resolve_destination(entities=["Gus"], category_hint="document") == Path("Family/Gus/Papers")
    # Renamed root with role mapping receives financial traffic
    assert router.resolve_destination(category_hint="receipt", summary="store receipt") == Path("Money/Purchases")
    # Unmatched content falls back to the Misc root
    assert router.resolve_destination(summary="random unknown stuff") == Path("Misc")


def test_router_root_keywords_route_traffic(tmp_path):
    structure = tmp_path / "structure.yaml"
    structure.write_text(
        textwrap.dedent(
            """
            roots:
              Financial:
                keywords: [premium]
                subfolders:
                  Insurance: {keywords: [insurance, policy]}
                  Misc: {}
              Misc: {}
            """
        ),
        encoding="utf-8",
    )
    router = TaxonomyRouter(taxonomy=load_taxonomy(structure))
    # 'insurance' alone is not a built-in financial keyword; the root and
    # child keywords declared in the structure file pull it in.
    assert router.resolve_destination(summary="insurance premium statement") == Path("Financial/Insurance")


def test_heuristic_hint_insurance_letter():
    """A renters-insurance verification letter must not be mistaken for a
    medical record even when it mentions medical coverage."""
    from auto_file.core.understander import _extract_category_hint_from_text

    text = (
        "RENTERS INSURANCE VERIFICATION LETTER\n"
        "Policy number: RIV-4471\n"
        "This letter verifies renter's insurance coverage including "
        "medical payments to others coverage for the above-named tenant."
    )
    assert _extract_category_hint_from_text(text) == "Insurance"


def test_router_insurance_letter_routes_to_insurance_child(tmp_path):
    structure = tmp_path / "structure.yaml"
    structure.write_text(
        textwrap.dedent(
            """
            roots:
              Financial:
                subfolders:
                  Insurance: {}
                  Misc: {}
              Misc: {}
            """
        ),
        encoding="utf-8",
    )
    router = TaxonomyRouter(taxonomy=load_taxonomy(structure))
    # 'insurance' triggers the Financial branch; the Insurance child matches
    # by name and the letter must not land in Misc.
    assert (
        router.resolve_destination(summary="renters insurance verification letter with policy number")
        == Path("Financial/Insurance")
    )


def test_router_default_insurance_falls_back_gracefully():
    router = TaxonomyRouter()
    result = router.resolve_destination(summary="renters insurance verification letter with policy number")
    # Default taxonomy has no Insurance folder; must land under Financial, not Misc
    assert result.parts[0] == "Financial"


def test_router_person_from_filename(tmp_path):
    """Filenames carry the owner's name with underscores; routing must use it."""
    router = TaxonomyRouter()
    result = router.resolve_destination(
        summary="resume with work history",
        category_hint="Document",
        filename_hint="Alpha_Hardy_Resume.pdf",
    )
    assert result == Path("People/Alpha/Documents")


def test_router_no_false_person_from_partial_name():
    """'Edie' must not match inside 'edible'."""
    router = TaxonomyRouter()
    assert (
        router.resolve_destination(summary="grocery list", filename_hint="edible_plants.pdf")
        == Path("Misc")
    )


def test_heuristic_medical_requires_specific_terms():
    """Bare 'medical' (e.g. a resume mentioning a medical office) is not a
    medical record; patient/clinic/prescription are."""
    from auto_file.core.understander import _extract_category_hint_from_text

    assert _extract_category_hint_from_text("Worked at a medical office front desk") == "Document"
    assert _extract_category_hint_from_text("Patient diagnosis summary from clinic") == "Medical Record"


def test_heuristic_resume_outranks_medical():
    """A resume mentioning patient care must be a Resume, not a medical record."""
    from auto_file.core.understander import _extract_category_hint_from_text

    text = (
        "Aaron Hardy Resume\n"
        "Work experience: medical assistant at Lakeside Clinic, "
        "patient scheduling and vitals"
    )
    assert _extract_category_hint_from_text(text) == "Resume"


def test_router_resume_goes_to_documents_not_medical():
    router = TaxonomyRouter()
    result = router.resolve_destination(
        summary="resume with patient care experience",
        category_hint="Resume",
        filename_hint="Alpha_Hardy_Resume.pdf",
    )
    assert result == Path("People/Alpha/Documents")


def test_router_scanned_document_files_by_filename(tmp_path):
    """A scanned PDF has no text; 'OneMain Financial.pdf' must land in the
    existing Bills/OneMain vendor folder via the filename alone."""
    structure = tmp_path / "structure.yaml"
    structure.write_text(
        textwrap.dedent(
            """
            roots:
              Financial:
                subfolders:
                  Bills:
                    subfolders: [OneMain, Due]
                  Misc: {}
              Misc: {}
            """
        ),
        encoding="utf-8",
    )
    router = TaxonomyRouter(taxonomy=load_taxonomy(structure))
    result = router.resolve_destination(
        summary="Document file",  # all the heuristic gets from a scan
        category_hint="Document",
        filename_hint="OneMain Financial.pdf",
    )
    assert result == Path("Financial/Bills/OneMain")


def test_router_default_taxonomy_unchanged_behavior():
    router = TaxonomyRouter()
    assert router.resolve_destination(entities=["Alpha"], category_hint="medical") == Path("People/Alpha/Medical")
    assert router.resolve_destination(summary="bank statement from Chase") == Path("Financial/Bank Statements")
    assert router.resolve_destination(summary="manual for dishwasher") == Path("Manuals/Appliances")


def test_resolve_destination_structure_argument(tmp_path):
    structure = _write_custom_structure(tmp_path)
    result = __import__("auto_file.core.router", fromlist=["resolve_destination"]).resolve_destination(
        entities=["Wanda"],
        summary="doctor visit",
        structure=structure,
    )
    assert result == Path("Family/Wanda/Health")


# ==============================================================================
# Executor and config plumbing
# ==============================================================================


def test_executor_loads_structure_file(tmp_path):
    structure = _write_custom_structure(tmp_path)
    executor = FilePipelineExecutor(target_root=tmp_path, structure=structure)
    assert executor.router.taxonomy.people == ["Wanda", "Gus"]
    assert executor.router.taxonomy.root_for_role("Financial") == "Money"


def test_get_structure_path(tmp_path):
    cfg = tmp_path / "config.json"
    assert get_structure_path(cfg) is None
    set_config_value("structure", "/tmp/some/structure.yaml", cfg)
    assert get_structure_path(cfg) == Path("/tmp/some/structure.yaml")


# ==============================================================================
# CLI setup command
# ==============================================================================


def test_cli_setup_noninteractive_generates_structure(tmp_path):
    cfg = tmp_path / "config.json"
    inbox = tmp_path / "Inbox"
    dest = tmp_path / "Sorted"
    structure = tmp_path / "structure.yaml"

    result = runner.invoke(
        app,
        [
            "setup",
            "--inbox", str(inbox),
            "--dest", str(dest),
            "--structure", str(structure),
            "--generate-structure",
            "--config-file", str(cfg),
        ],
    )
    assert result.exit_code == 0, result.output
    assert inbox.is_dir() and dest.is_dir()

    config = json.loads(cfg.read_text())
    assert config["inbox"] == str(inbox)
    assert config["dest"] == str(dest)
    assert config["structure"] == str(structure)

    # Generated starter file is valid and loadable
    assert structure.is_file()
    tax = load_taxonomy(structure)
    assert tax.roots == default_taxonomy().roots


def test_cli_setup_rejects_invalid_existing_structure(tmp_path):
    cfg = tmp_path / "config.json"
    structure = tmp_path / "broken.yaml"
    structure.write_text("roots: [not, a, mapping]\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "setup",
            "--inbox", str(tmp_path / "Inbox"),
            "--dest", str(tmp_path / "Sorted"),
            "--structure", str(structure),
            "--no-generate-structure",
            "--config-file", str(cfg),
        ],
    )
    assert result.exit_code == 1


def test_cli_sort_uses_configured_structure(tmp_path):
    cfg = tmp_path / "config.json"
    inbox = tmp_path / "Inbox"
    inbox.mkdir()
    dest = tmp_path / "Sorted"
    structure = _write_custom_structure(tmp_path)
    set_config_value("inbox", str(inbox), cfg)
    set_config_value("dest", str(dest), cfg)
    set_config_value("structure", str(structure), cfg)

    result = runner.invoke(app, ["sort", "--dry-run", "--config-file", str(cfg)])
    assert result.exit_code == 0, result.output


def test_cli_sort_rejects_invalid_structure_file(tmp_path):
    cfg = tmp_path / "config.json"
    inbox = tmp_path / "Inbox"
    inbox.mkdir()
    structure = tmp_path / "broken.yaml"
    structure.write_text("not: valid: yaml: [", encoding="utf-8")
    set_config_value("inbox", str(inbox), cfg)
    set_config_value("dest", str(tmp_path / "Sorted"), cfg)
    set_config_value("structure", str(structure), cfg)

    result = runner.invoke(app, ["sort", "--dry-run", "--config-file", str(cfg)])
    assert result.exit_code == 1
