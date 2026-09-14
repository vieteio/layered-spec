from pathlib import Path

import pytest
from pydantic import ValidationError

from spec_validation.api import validate_documents
from spec_validation.models import (
    DocumentSet, DocumentSnapshot, Requirement, UseCase, ValidEntry,
    ValidationOptions, ValidationResult,
)
from spec_validation.parser import parse_document

FIXTURES = Path(__file__).parent / "fixtures"


def inspect(text, tmp_path, **limits):
    options = ValidationOptions(workspace_root=tmp_path, **limits)
    result = validate_documents(DocumentSet(documents=[DocumentSnapshot.from_text("spec.md", text)], options=options), include_documents=True)
    assert isinstance(result, ValidationResult)
    return result


def codes(result):
    return [issue.code for issue in result.report.diagnostics]


def test_named_numbered_fixture_and_raw_source(tmp_path):
    text = (FIXTURES / "named_and_numbered.md").read_text(encoding="utf-8")
    result = inspect(text, tmp_path)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    entities = result.documents[0].entities
    assert [(entity.number, entity.title) for entity in entities] == [
        ("4", "Render the diagram workflow graph view"), ("7", "Construct elements"), (None, "Check configuration"),
    ]
    assert all(isinstance(entity.value, UseCase) for entity in entities)
    requirements = [entry.value for layer in entities[0].layers for entry in layer.entries if isinstance(entry, ValidEntry) and isinstance(entry.value, Requirement)]
    assert [entry.requirement_id for entry in requirements] == ["R4.1", "Configuration requirement", "4.1"]
    for entry in requirements:
        span = entry.definition.source
        assert text[span.start_offset:span.end_offset] == entry.definition.markdown


@pytest.mark.parametrize("header,number,title", [
    ("2. Render", "2", "Render"), ("2.1 Render", "2.1", "Render"),
    ("UC2.1 — Render", "2.1", "Render"), ("Render", None, "Render"),
    ('"2. Render"', None, "2. Render"), ('"4"', None, "4"), ("UC helper", None, "UC helper"),
])
def test_heading_forms(header, number, title, tmp_path):
    result = inspect(f"## Use cases\n\n### {header}\ninput --read--> output\n", tmp_path)
    assert result.report.status == "passed"
    assert result.documents[0].entities[0].number == number
    assert result.documents[0].entities[0].title == title


@pytest.mark.parametrize("literal", [
    "```md\n### Fake\n\nRealizes:\n- UC9/R9\n```",
    "````md\n```text\n### Fake\n```\n\nRealizes:\n````",
    "~~~md\n### Fake\n\nRealizes:\n~~~",
    "> ### Fake\n> Realizes:\n> - UC9/R9",
    "    ### Fake\n    Realizes:\n    - UC9/R9",
    "<!--\n### Fake\n\nRealizes:\n-->",
    "<div>\n### Fake\nRealizes:\n</div>",
    "- Example:\n  ### Fake\n  Realizes:\n  - UC9/R9",
    "\\### Fake\n\\Realizes:",
])
def test_literal_contexts_do_not_declare_entities(literal, tmp_path):
    text = "## Use cases\n\n### Actual\nin --read--> out\n\nExtension/Notes:\n\n" + literal + "\n\n### Later\nin --write--> out\n"
    result = inspect(text, tmp_path)
    assert [entity.title for entity in result.documents[0].entities] == ["Actual", "Later"]
    assert result.report.status == "passed", codes(result)


def test_multiple_errors_and_partial_owner_recovery(tmp_path):
    text = """## Use cases

### 1. Missing workflow

Realized by:
- bad_source -> bad_target
- R1 -> UC2

Realizess:
- UC99/R1

### 2. Later
input --process--> output

Requirements:
Requirement: ""
Definition

Requirement: Good
Valid definition.
"""
    result = inspect(text, tmp_path)
    assert len([code for code in codes(result) if code == "MALFORMED_MAPPING"]) == 2
    assert {"MISSING_WORKFLOW", "UNKNOWN_LAYER", "INVALID_REQUIREMENT_DECLARATION", "TARGET_INVALID", "CHECK_BLOCKED"} <= set(codes(result))
    assert len(result.documents[0].entities) == 2
    assert result.documents[0].entities[0].value is None
    assert result.report.status == "failed"
    assert not result.report.analysis_complete


@pytest.mark.parametrize("identifier", ["4.1", "04.1", "CFG-01", "Configuration requirement", '"Input/output: production"'])
def test_general_requirements_are_exact_strings(identifier, tmp_path):
    result = inspect(f"## Use cases\n\n### 4. Read\nin --read--> out\n\nRequirements:\nRequirement: {identifier}\nDefinition.\n", tmp_path)
    assert result.report.status == "passed"
    value = result.documents[0].entities[0].layers[0].entries[0].value
    assert value.requirement_id == identifier.strip('"')


def test_requirement_definition_outside_requirements_and_duplicate(tmp_path):
    result = inspect("""## Use cases
### 1. Read
in --read--> out

Requirements:
R1: Required.

Extension/Configuration:
Requirement: R1
Also required.
""", tmp_path)
    assert "DUPLICATE_REQUIREMENT" in codes(result)


def test_arbitrary_colon_label_is_not_requirement(tmp_path):
    result = inspect("## Use cases\n### Read\nin --read--> out\n\nRequirements:\nConfiguration requirement:\nDefinition\n", tmp_path)
    assert "EMPTY_LAYER" in codes(result)
    assert result.documents[0].entities[0].layers[0].entries == []


def test_unclosed_fence_is_incomplete_and_does_not_promote_apparent_heading(tmp_path):
    text = "## Use cases\n### Actual\nin --read--> out\n\nExtension/Example:\n```md\n### Fake\nin --read--> out\n\nRealizes:\n- UC9/R9\n"
    result = inspect(text, tmp_path)
    assert [entity.title for entity in result.documents[0].entities] == ["Actual"]
    assert "UNCLOSED_LITERAL_BLOCK" in codes(result)
    assert not result.report.analysis_complete
    assert result.report.documents[0].opaque_spans


def test_empty_heading_recovers_next_owner(tmp_path):
    result = inspect("## Use cases\n###\n\nRealizes:\n- UC9/R9\n\n### Valid\nin --read--> out\n", tmp_path)
    assert "INVALID_ENTITY_HEADER" in codes(result)
    assert [entity.title for entity in result.documents[0].entities] == ["Valid"]


def test_missing_region_does_not_pass_vacuously(tmp_path):
    assert "MISSING_STRUCTURED_REGION" in codes(inspect("## Use casses\n### 1. Read\nin --read--> out\n", tmp_path))


def test_source_spans_crlf_unicode_and_bom_loader_boundary(tmp_path):
    text = "## Use cases\r\n\r\n### 4. Read 😀\r\nin --read--> out\r\n\r\nRealizes:\r\n- not_a_reference\r\n"
    result = inspect(text, tmp_path)
    issue = next(issue for issue in result.report.diagnostics if issue.code == "MALFORMED_MAPPING")
    source = issue.primary_location
    assert (source.start_line, source.start_column) == (7, 3)
    assert text[source.start_offset:source.end_offset] == "not_a_reference"
    assert result.documents[0].snapshot.source_text == text


def test_invariant_fixture_and_missing_target(tmp_path):
    text = (FIXTURES / "invariants.md").read_text(encoding="utf-8")
    result = inspect(text, tmp_path)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    broken = inspect(text.replace("D1: I1 -> I2", "D1: I1 -> I9"), tmp_path)
    assert "MISSING_MEMBER" in codes(broken)


def test_bad_invariant_indentation_does_not_hide_next_layer(tmp_path):
    text = (FIXTURES / "invariants.md").read_text(encoding="utf-8").replace("- State invariants:", "State invariants:")
    result = inspect(text, tmp_path)
    assert "INVALID_INVARIANT_NESTING" in codes(result)
    assert result.documents[0].entities[0].layers[-1].name == "Tests"


def test_derivation_missing_member_is_recoverable(tmp_path):
    text = (FIXTURES / "invariants.md").read_text(encoding="utf-8").replace("D1: I1 -> I2", "D1: UC1 -> I2")
    result = inspect(text, tmp_path)
    assert "INVALID_INVARIANT_STRUCTURE" in codes(result)
    assert result.documents[0].entities[0].layers[-1].name == "Tests"


@pytest.mark.parametrize("indent", ["", " ", "   "])
def test_invariant_entries_require_explicit_nesting(indent, tmp_path):
    text = "## Use cases\n### Read\nin --read--> out\n\nInvariants:\n- State invariants:\n" + indent + "- `I1` at `input`: Valid.\n\n### Later\nin --read--> out\n"
    result = inspect(text, tmp_path)
    assert "INVALID_INVARIANT_NESTING" in codes(result)
    assert result.documents[0].entities[-1].title == "Later"


@pytest.mark.parametrize("kind,value", [("invariant", "anything"), ("step", "step0"), ("requirement", "   ")])
def test_member_model_validates_kind_and_nonempty_identity(kind, value):
    from spec_validation.models import MemberSelector
    with pytest.raises(ValidationError):
        MemberSelector(kind=kind, value=value, source=DocumentSnapshot.from_text("s.md", "").span(0))


def test_local_shorthand_and_explanatory_deep_heading(tmp_path):
    text = (FIXTURES / "local_realization.md").read_text(encoding="utf-8")
    result = inspect(text, tmp_path)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    assert codes(result) == []
    ambiguous = inspect(text + "\n#### 4.1.1.1 Explanation or child\nin --read--> out\n", tmp_path)
    assert ambiguous.report.status == "passed"
    assert len(ambiguous.documents[0].entities) == len(result.documents[0].entities)


def test_depth_overflow_is_explicit(tmp_path):
    text = "## Use cases\n### Read\nin --read--> out\n\nExtension/Notes:\n- one\n  - two\n    - three\n      - four\n\n### Later\nin --read--> out\n"
    result = inspect(text, tmp_path, max_nesting_depth=3)
    assert "NESTING_LIMIT_EXCEEDED" in codes(result)
    assert result.documents[0].entities[-1].title == "Later"


def test_strict_pydantic_models_do_not_coerce_identifiers():
    snapshot = DocumentSnapshot.from_text("s.md", "x")
    with pytest.raises(ValidationError):
        from spec_validation.models import MemberSelector
        MemberSelector(kind="requirement", value=4.1, source=snapshot.span(0))
