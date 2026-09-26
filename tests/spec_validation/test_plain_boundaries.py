"""T-16: source-level grammar, independent recovery and one public schema."""

import json

import pytest
from pydantic import ValidationError

from spec_validation.api import validate_documents
from spec_validation.models import (
    DocumentSet, DocumentSnapshot, InvalidEntry, InvalidWorkflowChain, Requirement,
    UnownedRequirementRef, ValidEntry, ValidationOptions, ValidationReport,
    ValidWorkflowChain,
)
from spec_validation.reporting import render_text
from validate_specs import build_parser


def inspect(body, tmp_path):
    snapshot = DocumentSnapshot.from_text("spec.md", body)
    return validate_documents(
        DocumentSet(documents=[snapshot], options=ValidationOptions(workspace_root=tmp_path)),
        include_documents=True,
    )


def document(body):
    return "## Use cases\n\n### 4. Process\ninput --process--> result\n\n" + body


def requirements(entity):
    return [
        entry.value for layer in entity.layers for entry in layer.entries
        if isinstance(entry, ValidEntry) and isinstance(entry.value, Requirement)
    ]


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
@pytest.mark.parametrize("marker", ["R4.1: Required 😀.", "  R4.1: Required 😀.", "  R4.1:\nRequired 😀."])
def test_requirement_forms_have_exact_original_spans(marker, newline, tmp_path):
    text = document("Requirements:\n\n" + marker + "\n\nLogic:\nInput: some\n  Outcome:\nordinary continuation\n")
    text = text.replace("\n", newline)
    result = inspect(text, tmp_path)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    owner = result.documents[0].entities[0]
    requirement, = requirements(owner)
    assert requirement.requirement_id == "R4.1"
    assert requirement.definition.markdown.strip() == "Required 😀."
    assert text[requirement.source.start_offset:requirement.source.end_offset].strip() == marker.split("\n")[0].strip()
    span = requirement.definition.source
    assert text[span.start_offset:span.end_offset] == requirement.definition.markdown
    assert [layer.name for layer in owner.layers] == ["Requirements", "Logic"]


@pytest.mark.parametrize("marker", ["R4.1:", "R4.1 contract:", " R4.1:", "   R4.1:"])
def test_invalid_requirement_marker_preserves_following_siblings(marker, tmp_path):
    text = document("Requirements:\n\n" + marker + "\nBad declaration body.\n\n  R4.2:\nGood declaration.\n\nLogic:\nNotes.\n\n### Later\nx --step--> y\n")
    result = inspect(text, tmp_path)
    issue = next(d for d in result.report.diagnostics if d.code == "INVALID_REQUIREMENT_DECLARATION")
    assert "two spaces" in issue.message
    owner, later = result.documents[0].entities
    invalid = owner.layers[0].entries[0]
    assert isinstance(invalid, InvalidEntry)
    assert "Bad declaration body." in invalid.raw_block.raw_markdown
    assert "R4.2" not in invalid.raw_block.raw_markdown
    assert [r.requirement_id for r in requirements(owner)] == ["R4.2"]
    assert owner.layers[-1].name == "Logic"
    assert later.value is not None
    assert result.report.status == "failed"


def test_internal_labels_and_generic_identifiers_in_multiline_definition(tmp_path):
    text = document("Requirements:\n\n  R4.1:\nFirst line.\n  Rules:\n- Keep all items.\n\nRequirement: Configuration requirement\nConfig definition.\n\nLogic:\nInput: some\ncontinuation\n  Input:\nmore continuation\n")
    result = inspect(text, tmp_path)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    found = requirements(result.documents[0].entities[0])
    assert [r.requirement_id for r in found] == ["R4.1", "Configuration requirement"]
    assert "  Rules:\n- Keep all items." in found[0].definition.markdown


@pytest.mark.parametrize("label,expected", [
    ("Realizess:", "UNKNOWN_LAYER"),
    ("Unknown custom:", "UNKNOWN_LAYER"),
    ("requirements:", "INVALID_LAYER_CAPITALIZATION"),
    ("Layer: Requirements", "OBSOLETE_LAYER_SYNTAX"),
])
def test_malformed_layers_recover_without_accepting_them(label, expected, tmp_path):
    text = document(label + "\nR4.1: Some body.\n\nLogic:\nLater content.\n\n### Later\nx --step--> y\n")
    result = inspect(text, tmp_path)
    assert expected in {d.code for d in result.report.diagnostics}
    owner, later = result.documents[0].entities
    assert not owner.layers[0].complete
    assert owner.layers[1].name == "Logic" and owner.layers[1].complete
    assert later.value is not None


def test_missing_separator_is_error_and_recovery_boundary(tmp_path):
    text = document("Logic:\nSome prose.\nRequirements:\nR4.1: Required.\n\nTests:\n- description: checked\n  requirements: R4.1\n")
    result = inspect(text, tmp_path)
    assert {d.code for d in result.report.diagnostics} == {"MISSING_LAYER_SEPARATOR", "CHECK_BLOCKED"}
    owner = result.documents[0].entities[0]
    assert [layer.name for layer in owner.layers] == ["Logic", "Requirements", "Tests"]
    assert not owner.layers[1].complete and owner.layers[2].complete
    assert "Requirements:" not in owner.layers[0].body.markdown


def test_first_state_body_layer_needs_no_blank(tmp_path):
    result = inspect("## States\n### State ready — Ready\nDescription:\nReady.\n", tmp_path)
    assert result.report.status == "passed"


@pytest.mark.parametrize("example", [
    "```md\nRequirements:\nR9:\n```",
    "~~~text\nRequirements:\nR9:\n~~~",
    "    Requirements:\n    R9:",
    "> Requirements:\n> R9:",
    "<!--\nRequirements:\nR9:\n-->",
    "<div>\nRequirements:\nR9:\n</div>",
    "- Example content\n  Requirements:\n  R9:",
    "\\Requirements:\n\\R9:",
])
def test_literal_contexts_never_create_requirements_or_layers(example, tmp_path):
    result = inspect(document("Logic:\n\n" + example + "\n\nRequirements:\nR4.1: Actual.\n"), tmp_path)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    assert [r.requirement_id for r in requirements(result.documents[0].entities[0])] == ["R4.1"]


def test_indented_named_workflows_share_main_ast_and_recover(tmp_path):
    text = document("Detailed Workflow:\n\n  Visit children:\ninput --process--> result\n\n  Broken child:\na --choose--> [\n\n  Later child:\nx --step--> y\n\nRequirements:\nR4.1: Still present.\n")
    result = inspect(text, tmp_path)
    owner = result.documents[0].entities[0]
    chains = owner.layers[0].chains
    assert [type(chain) for chain in chains] == [ValidWorkflowChain, InvalidWorkflowChain, ValidWorkflowChain]
    assert chains[0].value.label == "Visit children"
    assert chains[0].value.expression.kind == owner.workflow.expression.kind
    assert chains[2].value.label == "Later child"
    assert requirements(owner)[0].requirement_id == "R4.1"
    assert len([d for d in result.report.diagnostics if d.code == "INVALID_WORKFLOW"]) == 1


def test_column_zero_workflow_name_is_unknown_outer_layer(tmp_path):
    result = inspect(document("Detailed Workflow:\n\nVisit children:\nx --step--> y\n\nLogic:\nNotes.\n"), tmp_path)
    owner = result.documents[0].entities[0]
    assert owner.layers[0].chains == []
    assert owner.layers[1].name == "Visit children" and not owner.layers[1].complete
    assert "UNKNOWN_LAYER" in {d.code for d in result.report.diagnostics}


def test_numbered_story_alias_without_dialect(tmp_path):
    text = "## User stories\n### 2. Read result\nx --read--> y\n\nUses:\n- \"read\" -> UC4\n\nE2E tests:\n- description: result shown\n\n" + document("Logic:\nNotes.\n")
    result = inspect(text, tmp_path)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    assert result.documents[0].entities[0].entity_id == "S2"


def test_public_schemas_and_cli_have_no_dialect(tmp_path):
    result = inspect(document("Requirements:\nR4.1: Required.\n"), tmp_path)
    assert result.report.status == "passed"
    assert "dialect" not in ValidationOptions.model_fields
    assert "dialect" not in ValidationReport.model_fields
    assert "dialect" not in json.loads(result.report.model_dump_json())
    assert "dialect" not in render_text(result.report)
    assert "--dialect" not in build_parser().format_help()
    with pytest.raises(ValidationError):
        ValidationOptions(workspace_root=tmp_path, dialect="explicit")
    assert UnownedRequirementRef.__name__ == "UnownedRequirementRef"


def test_unknown_and_requirement_errors_accumulate_across_owners(tmp_path):
    text = document("Requirements:\n\nR4.1:\nInvalid marker body.\n\nUnknown layer:\nUninterpreted.\n\nLogic:\nValid body.\n\n### Later\nx --step--> y\n\nRequirements:\nR5: Valid requirement.\n")
    result = inspect(text, tmp_path)
    assert {"INVALID_REQUIREMENT_DECLARATION", "UNKNOWN_LAYER"} <= {d.code for d in result.report.diagnostics}
    first, later = result.documents[0].entities
    assert first.value is None and later.value is not None
    assert [r.requirement_id for r in requirements(later)] == ["R5"]


def test_owner_omitted_shorthand_requires_unique_known_local_group(tmp_path):
    text = document("Requirements:\nR4.1: First definition.\n\n### 4.2 Other owner\nx --step--> y\n\nRequirements:\nR4.1: Second definition.\n\n### 4.3 Caller\nx --step--> y\n\nRealizes:\n- R4.1\n")
    result = inspect(text, tmp_path)
    assert "AMBIGUOUS_REFERENCE" in {d.code for d in result.report.diagnostics}
    sources = result.documents[0].entities[-1].layers[0].entries[0].value.sources
    assert isinstance(sources[0], UnownedRequirementRef)


def test_four_space_requirement_example_does_not_become_an_entry(tmp_path):
    text = document("Requirements:\n\nR4.1: Actual requirement.\n\n    R4.2:\n    Example text.\n\n  R4.3:\nAnother requirement.\n")
    result = inspect(text, tmp_path)
    assert result.report.status == "passed"
    assert [r.requirement_id for r in requirements(result.documents[0].entities[0])] == ["R4.1", "R4.3"]


def test_empty_general_marker_recovers_the_next_requirement(tmp_path):
    text = document("Requirements:\n\nRequirement:\nMissing identifier.\n\nR4.2: Valid sibling.\n")
    result = inspect(text, tmp_path)
    assert "INVALID_REQUIREMENT_DECLARATION" in {d.code for d in result.report.diagnostics}
    owner = result.documents[0].entities[0]
    assert [r.requirement_id for r in requirements(owner)] == ["R4.2"]
    assert len(owner.layers) == 1
