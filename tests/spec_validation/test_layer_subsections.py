"""T-21: optional grouping retains parent-layer semantics and source ownership."""

import pytest

from spec_validation.api import validate_documents
from spec_validation.models import (
    DocumentSet, DocumentSnapshot, InvalidWorkflowChain, MarkdownSubsection, ParsedDocument,
    TypedSubsection, ValidationOptions, WorkflowSubsection,
)
from spec_markdown.rendering import reconstruct_markdown, render_markdown
from spec_markdown.roundtrip import check_roundtrip, compare_documents


PREFIX = "## Use cases\n\n### 1. Build\nx --build--> y\n\n"


def inspect(tmp_path, body):
    inputs = DocumentSet(documents=[DocumentSnapshot.from_text("spec.md", PREFIX + body)], options=ValidationOptions(workspace_root=tmp_path))
    result = validate_documents(inputs, include_documents=True)
    return inputs, result, result.documents[0].entities[0].layers[0]


@pytest.mark.parametrize("name", ["Logic", "Types", "Tests", "Extension/Details", "Requirements"])
def test_grouped_requirements_retain_layer_semantics(tmp_path, name):
    source, result, layer = inspect(tmp_path, name + ":\n- Configuration:\n  R1: Must build.\n\n- Other:\n  Requirement: Custom title\n  Must finish.\n")
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    assert layer.entries == []
    assert [s.name for s in layer.subsections] == ["Configuration", "Other"]
    assert all(isinstance(s, TypedSubsection) for s in layer.subsections)
    assert [entry.value.requirement_id for entry in layer.all_entries] == ["R1", "Custom title"]
    assert all(entry.value.defining_layer_name == name for entry in layer.all_entries)
    assert ParsedDocument.model_validate_json(result.documents[0].model_dump_json()) == result.documents[0]
    rendered = render_markdown(result.documents[0])
    assert '- Configuration:\n  Requirement: "R1"\nMust build.\n' in rendered
    report = check_roundtrip(source)
    assert report.status == "passed", report.model_dump_json(indent=2)


def test_grouped_mappings_are_resolved_and_reciprocal(tmp_path):
    body = ('Requirements:\n- Contract:\n  R1: Must build.\n\n'
            'Realized by:\n- Implementations:\n  - R1 -> UC2/R2\n\n'
            '### 2. Implement\nx --implement--> y\n\n'
            'Requirements:\n- Contract:\n  R2: Implement build.\n\n'
            'Realizes:\n- Sources:\n  - UC1/R1\n')
    source, result, _ = inspect(tmp_path, body)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    assert result.report.metrics.normalized_edges == 2
    assert result.documents[0].entities[0].layers[1].subsections[0].entries[0].value.entry_kind == "forward"
    report = check_roundtrip(source)
    assert report.status == "passed", report.model_dump_json(indent=2)
    broken = source.model_copy(update={"documents": [DocumentSnapshot.from_text("spec.md", PREFIX + body.replace("UC1/R1", "UC1/R404"))]})
    assert validate_documents(broken).status == "failed"


@pytest.mark.parametrize("name, row, kind", [
    ("Uses", '"build" -> UC1', "uses"),
    ("Workflow anchors", "step1: build", "anchor"),
    ("Tests", "requirements: R1", "reference_field"),
    ("Requirement representations", "source: R1", "reference_field"),
])
def test_grouped_rows_use_their_layer_parser(tmp_path, name, row, kind):
    source, result, layer = inspect(tmp_path, f"{name}:\n- Group:\n  - {row}\n\nRequirements:\nR1: Build.\n")
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    assert layer.subsections[0].entries[0].value.entry_kind == kind
    report = check_roundtrip(source)
    assert report.status == "passed", report.model_dump_json(indent=2)


def test_plain_markdown_is_ordered_and_protected(tmp_path):
    body = ('Logic:\n- Details:\n  - Nested:\n    - R404: example\n'
            '\n```md\n- Fake:\n  R9: example\n```\n\n'
            '- Details:\n  Plain text.\n')
    source, result, layer = inspect(tmp_path, body)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    assert [s.name for s in layer.subsections] == ["Details", "Details"]
    assert all(isinstance(s, MarkdownSubsection) for s in layer.subsections)
    assert layer.all_entries == []
    assert reconstruct_markdown(result.documents[0]) == PREFIX + body
    assert check_roundtrip(source).status == "passed"


def test_known_anchor_syntax_keeps_errors_and_recovers(tmp_path):
    source, result, layer = inspect(tmp_path, 'Workflow anchors:\n- step1:\n- Group:\n  - state2:\n\n- Valid:\n  - step3: build\n')
    assert result.report.status == "failed"
    assert [s.name for s in layer.subsections] == ["Group", "Valid"]
    assert layer.entries[0].status == "invalid"
    assert not layer.subsections[0].complete
    assert layer.subsections[1].entries[0].value.anchor_id == "step3"
    assert len([d for d in result.report.diagnostics if d.code == "MALFORMED_MAPPING"]) == 2
    checks = check_roundtrip(source).checks
    assert checks[0].status == "passed"
    assert checks[1].status == "blocked"


@pytest.mark.parametrize("layer, declaration", [
    ("Realized by", "R1"), ("Realizes", "UC1/R1"), ("Uses", '"build"'),
])
def test_malformed_mapping_cannot_become_generic_subsection(tmp_path, layer, declaration):
    _, result, parsed = inspect(tmp_path, f"{layer}:\n- {declaration}:\n- Notes:\n  Explanation.\n")
    assert result.report.status == "failed"
    assert [s.name for s in parsed.subsections] == ["Notes"]
    assert parsed.entries[0].status == "invalid"
    assert any(d.code == "MALFORMED_MAPPING" for d in result.report.diagnostics)


def test_invalid_grouped_requirements_recover_at_sibling(tmp_path):
    _, result, layer = inspect(tmp_path, 'Requirements:\n- Broken:\n  R1:\n\n- Valid:\n  R2 form: Defined.\n')
    assert result.report.status == "failed"
    assert not layer.subsections[0].complete
    assert layer.subsections[1].complete
    assert layer.subsections[1].entries[0].value.requirement_id == "R2"
    valid_source, _, _ = inspect(tmp_path, 'Requirements:\n- Valid:\n  R2 form: Defined.\n')
    report = check_roundtrip(valid_source)
    assert report.status == "passed", report.model_dump_json(indent=2)


def test_story_layers_support_grouped_uses_and_e2e_fields(tmp_path):
    text = ('## User stories\n\n### S1 — Build\nx --build--> y\n\n'
            'Uses:\n- Actions:\n  - "build" -> UC1\n\n'
            'E2E tests:\n- Acceptance:\n  - requirements: UC1/R1\n\n'
            + PREFIX + 'Requirements:\nR1: Build.\n')
    source = DocumentSet(documents=[DocumentSnapshot.from_text("spec.md", text)], options=ValidationOptions(workspace_root=tmp_path))
    result = validate_documents(source, include_documents=True)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    assert [s.name for layer in result.documents[0].entities[0].layers for s in layer.subsections] == ["Actions", "Acceptance"]
    assert check_roundtrip(source).status == "passed"


def test_detailed_workflow_grouping_preserves_named_chains(tmp_path):
    body = ('Detailed Workflow:\n- direct-name:\n  a --direct--> b\n\n'
            '- Recovery:\n  Explain recovery here.\n\n'
            '  - retry:\n    b --retry--> c\n\n'
            '  c --finish--> d\n\n'
            '- Notes:\n  No further workflows.\n')
    source, result, layer = inspect(tmp_path, body)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    assert [s.name for s in layer.subsections] == ["Recovery", "Notes"]
    assert all(isinstance(s, WorkflowSubsection) for s in layer.subsections)
    assert [chain.value.label for chain in layer.chains] == ["direct-name", "retry", None]
    assert [chain.value.label for chain in layer.subsections[0].chains] == ["retry", None]
    report = check_roundtrip(source)
    assert report.status == "passed", report.model_dump_json(indent=2)
    rendered = render_markdown(result.documents[0])
    assert "- Recovery:\n" in rendered
    assert "  #### retry ###\n\n  ```workflow\n" in rendered


def test_malformed_named_chain_is_not_generic_subsection(tmp_path):
    _, result, layer = inspect(tmp_path, 'Detailed Workflow:\n- broken:\n  a --run--> (b,\n\n- Notes:\n  Recovery text.\n')
    assert result.report.status == "failed"
    assert [s.name for s in layer.subsections] == ["Notes"]
    assert isinstance(layer.chains[0], InvalidWorkflowChain)


def test_duplicate_workflow_labels_across_groups(tmp_path):
    _, result, layer = inspect(tmp_path, 'Detailed Workflow:\n- One:\n  Prose.\n\n  - repeat:\n    a --run--> b\n\n- Two:\n  Prose.\n\n  - repeat:\n    b --run--> c\n')
    assert len(layer.chains) == 2
    assert any(d.code == "DUPLICATE_WORKFLOW_LABEL" for d in result.report.diagnostics)


def test_direct_requirements_resume_layer_ownership(tmp_path):
    source, result, layer = inspect(tmp_path, 'Requirements:\n- Group:\n  R1: Grouped.\n\nR2: Direct.\n\n- Other:\n  R3: Grouped again.\n')
    assert result.report.status == "passed"
    assert [entry.value.requirement_id for entry in layer.entries] == ["R2"]
    assert [entry.value.requirement_id for entry in layer.all_entries] == ["R1", "R2", "R3"]
    assert check_roundtrip(source).status == "passed"


@pytest.mark.parametrize("mutation", ["name", "order", "requirement"])
def test_structural_comparison_observes_group_changes(tmp_path, mutation):
    source, result, _ = inspect(tmp_path, 'Requirements:\n- One:\n  R1: First.\n\n- Two:\n  R2: Second.\n')
    original = result.documents[0]
    changed = original.model_copy(deep=True)
    layer = changed.entities[0].layers[0]
    match mutation:
        case "name":
            layer.subsections[0].name = "Changed"
        case "order":
            layer.subsections.reverse()
        case "requirement":
            layer.subsections[0].entries[0].value.requirement_id = "R9"
    assert compare_documents([original], [changed], source.options)


def test_crlf_unicode_and_empty_generic_body(tmp_path):
    source, result, layer = inspect(tmp_path, 'Logic:\r\n- Notes 😀:\r\n  Text\tkept.\r\n\r\n- Empty:\r\n')
    assert layer.subsections[0].body.markdown == "  Text\tkept.\r\n\r\n"
    assert layer.subsections[1].body.markdown == ""
    assert result.report.status == "passed"
    assert check_roundtrip(source).status == "passed"
