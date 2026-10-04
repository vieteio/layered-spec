"""T-20: general subsection ownership, typed dispatch and rendering consistency."""

import pytest

from spec_validation.api import validate_documents
from spec_validation.models import (
    DerivationsSubsection, DocumentSet, DocumentSnapshot, InvariantCheckpoint,
    InvariantDerivation, MarkdownSubsection, ParsedDocument, RationaleSubsection,
    StateInvariantsSubsection, ValidEntry, ValidationOptions,
)
from spec_validation.parser import parse_document
from spec_markdown.rendering import reconstruct_markdown, render_markdown
from spec_markdown.roundtrip import check_roundtrip, compare_documents


PREFIX = "## Use cases\n\n### 1. Build\nx --build--> y\n\nInvariants:\n"
STATES = "- State invariants:\n  - `I1` at `x`: Valid.\n  - `I2` at `y`: Complete.\n\n"
DERIVATIONS = "- Derivations:\n  - `D1: I1 -> I2`\n    - workflow transition: build\n    - justification: Construction establishes completeness.\n\n"
RATIONALE = "- Rationale:\n  - `N1`:\n    - note: Construction covers all elements.\n    - assessment: supported\n    - used by: D1\n\n"
CUSTOM = "- Design considerations:\n  - The representation may change later.\n\n"


def inputs(tmp_path, body):
    return DocumentSet(documents=[DocumentSnapshot.from_text("spec.md", PREFIX + body)], options=ValidationOptions(workspace_root=tmp_path))


def inspect(tmp_path, body):
    source = inputs(tmp_path, body)
    result = validate_documents(source, include_documents=True)
    return source, result, result.documents[0].entities[0].layers[0]


@pytest.mark.parametrize("position", range(4))
def test_custom_subsection_closes_every_typed_predecessor(tmp_path, position):
    sections = [STATES, DERIVATIONS, RATIONALE]
    sections.insert(position, CUSTOM)
    source, result, layer = inspect(tmp_path, "".join(sections))
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    assert isinstance(layer.subsections[position], MarkdownSubsection)
    assert layer.subsections[position].name == "Design considerations"
    assert layer.subsections[position].body.markdown == "  - The representation may change later.\n\n"
    assert layer.entries == []
    assert len(layer.all_entries) == 4
    for entry in layer.all_entries:
        assert isinstance(entry, ValidEntry)
        value = entry.value
        if isinstance(value, InvariantDerivation):
            assert value.justification.markdown.strip() == "Construction establishes completeness."
        if isinstance(value, InvariantCheckpoint):
            assert "Design considerations" not in value.assertion.markdown
    assert check_roundtrip(source).status == "passed"


def test_custom_only_expected_model_markdown_and_json(tmp_path):
    source, result, layer = inspect(tmp_path, CUSTOM)
    assert result.report.status == "passed"
    assert layer.all_entries == []
    assert [(section.kind, section.name) for section in layer.subsections] == [("markdown", "Design considerations")]
    expected = "## Use cases\n\n### UC1 — Build ###\n```workflow\nx --build--> y\n```\n\nInvariants:\n" + CUSTOM
    assert render_markdown(result.documents[0]) == expected
    serialized = layer.model_dump()
    assert "all_entries" not in serialized
    assert serialized["subsections"][0]["body"]["markdown"] == "  - The representation may change later.\n\n"
    assert ParsedDocument.model_validate_json(result.documents[0].model_dump_json()) == result.documents[0]
    assert check_roundtrip(source).status == "passed"


def test_known_entries_have_one_subsection_owner(tmp_path):
    _, result, layer = inspect(tmp_path, STATES + DERIVATIONS + RATIONALE)
    assert [type(section) for section in layer.subsections] == [StateInvariantsSubsection, DerivationsSubsection, RationaleSubsection]
    serialized = layer.model_dump()
    assert serialized["entries"] == []
    assert sum(len(section["entries"]) for section in serialized["subsections"]) == 4
    assert [entry.value.entry_kind for entry in layer.all_entries] == ["invariant", "invariant", "derivation", "rationale"]
    assert result.report.status == "passed"


def test_repeated_custom_names_preserve_occurrences(tmp_path):
    second = CUSTOM.replace("may change later", "has changed")
    source, result, layer = inspect(tmp_path, CUSTOM + second)
    assert result.report.status == "passed"
    assert [section.name for section in layer.subsections] == ["Design considerations", "Design considerations"]
    assert [section.body.markdown for section in layer.subsections] == [
        "  - The representation may change later.\n\n", "  - The representation has changed.\n\n",
    ]
    assert check_roundtrip(source).status == "passed"


@pytest.mark.parametrize("name", ["Outline", "Definitions", "Rationale", "State invariants", "Derivations"])
def test_standard_duplicates_remain_errors(tmp_path, name):
    _, result, layer = inspect(tmp_path, f"- {name}:\n\n- {name}:\n")
    assert any(issue.code == "DUPLICATE_INVARIANT_SECTION" for issue in result.report.diagnostics)
    assert len(layer.subsections) == 2


@pytest.mark.parametrize("name", ["Outline", "Definitions", "Notes", "implementation notes", "Choice: A or B"])
def test_general_body_does_not_infer_declarations_or_nested_boundaries(tmp_path, name):
    body = f"- {name}:\n" + (
        "  - `I404` at `some state`: only an example.\n"
        "  - `N1`:\n    - assessment: invented\n"
        "  - Derivations:\n    - `D0: I404 -> I405`\n"
        "  - Rationale:\n    - note: A nested example.\n"
        "\n```md\n- Standalone-looking example:\n```\n\n"
        "  > - Quoted example:\n\n"
    ) + CUSTOM
    source, result, layer = inspect(tmp_path, body)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    assert layer.all_entries == []
    assert [section.name for section in layer.subsections] == [name, "Design considerations"]
    assert "assessment: invented" in layer.subsections[0].body.markdown
    assert check_roundtrip(source).status == "passed"


def test_malformed_known_subsection_is_not_general_markdown(tmp_path):
    source, result, layer = inspect(tmp_path, "- Derivations:\n  - Invalid entry.\n" + CUSTOM + RATIONALE.replace("    - used by: D1\n", ""))
    assert isinstance(layer.subsections[0], DerivationsSubsection)
    assert not layer.subsections[0].complete
    assert isinstance(layer.subsections[1], MarkdownSubsection)
    assert isinstance(layer.subsections[2], RationaleSubsection)
    assert layer.subsections[2].complete
    assert any(issue.code == "INVALID_INVARIANT_STRUCTURE" for issue in result.report.diagnostics)
    assert reconstruct_markdown(result.documents[0]) == source.documents[0].source_text
    assert [check.status for check in check_roundtrip(source).checks] == ["passed", "blocked", "blocked"]


def test_requirements_between_subsections_keep_independent_ownership(tmp_path):
    body = CUSTOM + "R1: An obligation.\n\n" + STATES + "R2: Another obligation.\n\n" + CUSTOM
    source, result, layer = inspect(tmp_path, body)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    assert [entry.value.requirement_id for entry in layer.entries] == ["R1", "R2"]
    assert [section.name for section in layer.subsections] == ["Design considerations", "State invariants", "Design considerations"]
    assert all("obligation" not in section.body.markdown for section in layer.subsections)
    assert [entry.value.definition.markdown for entry in layer.entries] == ["An obligation.\n\n", "Another obligation.\n\n"]
    assert check_roundtrip(source).status == "passed"


@pytest.mark.parametrize("ending", ["", "\n", "\r\n"])
def test_empty_custom_subsection_and_body_mutation(tmp_path, ending):
    source, result, layer = inspect(tmp_path, "- Empty:" + ending)
    assert result.report.status == "passed"
    assert layer.subsections[0].body.markdown == ""
    assert check_roundtrip(source).status == "passed"
    changed = result.documents[0].model_copy(deep=True)
    changed.entities[0].layers[0].subsections[0].body.markdown = "  Added body.\n"
    assert "  Added body.\n" in render_markdown(changed)


def test_name_body_and_order_participate_in_structural_comparison(tmp_path):
    source, result, _ = inspect(tmp_path, CUSTOM + "- Alternatives:\n  Keep the current representation.\n")
    original = result.documents[0]
    changed = original.model_copy(deep=True)
    first = changed.entities[0].layers[0].subsections[0]
    first.name = "Constraints"
    first.body.markdown = "  New constraint.\n\n"
    rendered = render_markdown(changed)
    assert "- Constraints:\n  New constraint.\n" in rendered
    after = parse_document(DocumentSnapshot.from_text("spec.md", rendered), source.options)
    changes = compare_documents([original], [after], source)["spec.md"]
    assert any("subsections[0].name" in change.path for change in changes)
    assert any("subsections[0].body.markdown" in change.path for change in changes)
    reordered = original.model_copy(deep=True)
    reordered.entities[0].layers[0].subsections.reverse()
    assert compare_documents([original], [reordered], source)["spec.md"]


def test_general_body_exact_crlf_unicode_and_tabs(tmp_path):
    body = "- Notes:\r\n  Meaning 😀\t  \r\n\r\n  ```text\r\n  A -> B\r\n  ```\r\n"
    source, result, layer = inspect(tmp_path, body)
    assert result.report.status == "passed"
    section = layer.subsections[0]
    assert section.body.markdown == body.split("\r\n", 1)[1]
    span = section.body.source
    assert source.documents[0].source_text[span.start_offset:span.end_offset] == section.body.markdown
    assert check_roundtrip(source).status == "passed"
