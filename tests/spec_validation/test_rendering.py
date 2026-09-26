"""Independent renderer examples and three-check regressions (UC8/UC9)."""

from pathlib import Path

import pytest

from spec_validation.api import validate_documents
from spec_validation.loading import load_document_set
from spec_validation.models import DocumentSet, DocumentSnapshot, ValidationOptions
from spec_validation.parser import parse_document
from spec_markdown.rendering import RenderingError, reconstruct_bytes, reconstruct_markdown, render_markdown
from spec_markdown.roundtrip import check_roundtrip, compare_documents, differences


def inputs(tmp_path, text):
    return DocumentSet(documents=[DocumentSnapshot.from_text("spec.md", text)], options=ValidationOptions(workspace_root=tmp_path))


@pytest.mark.parametrize("fixture", sorted((Path(__file__).parent / "fixtures").glob("*.md")), ids=lambda p: p.name)
def test_existing_fixtures_pass_all_three_checks(tmp_path, fixture):
    source = inputs(tmp_path, fixture.read_text(encoding="utf-8"))
    report = check_roundtrip(source)
    assert report.status == "passed", report.model_dump_json(indent=2)
    assert len(report.checks) == 3


def test_expected_canonical_markdown_and_independent_model(tmp_path):
    text = "# Notes\n\n## Use cases\n\n### 4. Read\nx --read--> y\n\nRequirements:\nR4.1: Must read.\n"
    source = inputs(tmp_path, text)
    parsed = parse_document(source.documents[0], source.options)
    expected = '# Notes\n\n## Use cases\n\n### UC4 — Read ###\n```workflow\nx --read--> y\n```\n\nRequirements:\nRequirement: "R4.1"\nMust read.\n'
    assert render_markdown(parsed) == expected
    assert parsed.entities[0].number == "4"
    assert parsed.entities[0].workflow.expression.transitions[0].label == "read"
    assert parsed.entities[0].layers[0].entries[0].value.requirement_id == "R4.1"
    assert check_roundtrip(source).status == "passed"


@pytest.mark.parametrize("bom", [False, True])
@pytest.mark.parametrize("ending", ["", "\n", "\r\n"])
def test_exact_bytes_bom_crlf_tabs_and_final_newline(tmp_path, bom, ending):
    raw = (b"\xef\xbb\xbf" if bom else b"") + ("## Use cases\r\n\r\n### Read 😀\r\nx --read--> y\r\n\r\nLogic:\r\n  Input:\r\ntext\t  " + ending).encode("utf-8")
    path = tmp_path / "spec.md"
    path.write_bytes(raw)
    source = load_document_set([path], ValidationOptions(workspace_root=tmp_path))
    parsed = parse_document(source.documents[0], source.options)
    assert reconstruct_bytes(parsed) == raw
    assert parsed.snapshot.utf8_bom == bom
    assert check_roundtrip(source).status == "passed", check_roundtrip(source).model_dump_json(indent=2)


def test_malformed_regions_preserved_but_canonical_checks_blocked(tmp_path):
    text = "## Use cases\n### Broken\nx --read--> y\n\nLogic:\n```md\nRequirements:\n"
    source = inputs(tmp_path, text)
    parsed = parse_document(source.documents[0], source.options)
    assert reconstruct_markdown(parsed) == text
    with pytest.raises(RenderingError):
        render_markdown(parsed)
    report = check_roundtrip(source)
    assert [check.status for check in report.checks] == ["passed", "blocked", "blocked"]


def test_corrupted_source_partition_fails_preservation_only(tmp_path):
    source = inputs(tmp_path, "## Use cases\n### Read\nx --read--> y\n")
    parsed = parse_document(source.documents[0], source.options)
    parsed.blocks[0].raw_markdown = parsed.blocks[0].raw_markdown.replace("Read", "Gone")
    report = check_roundtrip(source, [parsed])
    assert [check.status for check in report.checks] == ["failed", "passed", "passed"]


def test_retained_body_corruption_is_not_hidden_by_snapshot_replay(tmp_path):
    source = inputs(tmp_path, "## Use cases\n### Read\nx --read--> y\n\nLogic:\nOriginal prose.\n")
    parsed = parse_document(source.documents[0], source.options)
    parsed.entities[0].layers[0].body.markdown = "Incorrectly retained prose.\n"
    report = check_roundtrip(source, [parsed])
    assert report.checks[0].status == "failed"
    assert any("body" in item.path for item in report.checks[0].differences)


def test_typed_mutation_changes_output_and_comparison_detects_it(tmp_path):
    source = inputs(tmp_path, "## Use cases\n### Read\nx --read--> y\n\nRequirements:\nR1: Original.\n")
    before = parse_document(source.documents[0], source.options)
    changed = before.model_copy(deep=True)
    changed.entities[0].layers[0].entries[0].value.requirement_id = "Configuration"
    output = render_markdown(changed)
    assert 'Requirement: "Configuration"' in output and 'Requirement: "R1"' not in output
    after = parse_document(DocumentSnapshot.from_text("spec.md", output), source.options)
    found = compare_documents([before], [after], source)["spec.md"]
    assert any("requirement_id" in item.path for item in found)


def test_all_differences_and_list_order_are_preserved():
    found = differences({"a": [1, 2, 2], "b": "text  "}, {"a": [2, 1], "b": "text"})
    assert [item.path for item in found] == ["$.a[0]", "$.a[1]", "$.a[2]", "$.b"]


def test_validation_never_runs_markdown_checks(tmp_path, monkeypatch):
    source = inputs(tmp_path, "## Use cases\n### Read\nx --read--> y\n")
    from spec_markdown import roundtrip
    from pydantic import ValidationError
    def forbidden(*args, **kwargs):
        raise AssertionError("Spec validation must not invoke development checks")
    monkeypatch.setattr(roundtrip, "check_roundtrip", forbidden)
    normal = validate_documents(source)
    assert normal.status == "passed"
    assert not {"preservation", "structural_roundtrip", "canonical_stability"} & {c.check for c in normal.checks}
    with pytest.raises(ValidationError):
        ValidationOptions(workspace_root=tmp_path, check_roundtrip=True)


def test_independent_readable_peer_continues_after_load_failure(tmp_path):
    source = inputs(tmp_path, "## Use cases\n### Read\nx --read--> y\n")
    missing = load_document_set(["missing.md"], source.options)
    source.failed_inputs = missing.failed_inputs
    report = check_roundtrip(source)
    assert report.status == "incomplete"
    assert all(c.status == "passed" for c in report.checks if c.document_id == "spec.md")


def test_cross_file_number_title_and_member_aliases_compare_equally(tmp_path):
    first = "## Use cases\n### 4. Read\nx --read--> y\n\nRequirements:\nR1: Required.\n\nRealized by:\n- R1 -> child.md#UC7\n"
    second = "## Use cases\n### 7. Child\nx --read--> y\n\nRealizes:\n- spec.md#UC4/R1\n"
    source = inputs(tmp_path, first)
    source.documents.append(DocumentSnapshot.from_text("child.md", second))
    assert check_roundtrip(source).status == "passed"
    before = [parse_document(s, source.options) for s in source.documents]
    changed = second.replace("UC4/R1", "use-case Read/requirement R1")
    after = [before[0], parse_document(DocumentSnapshot.from_text("child.md", changed), source.options)]
    assert compare_documents(before, after, source) == {"child.md": [], "spec.md": []}


def test_workflow_forms_labels_and_form_metadata_roundtrip(tmp_path):
    text = "## Use cases\n### \"2. A title\"\n```workflow\n{a --fork--> (b --step--> c, d)} --choose--> [x, | again: y --step--> z |]\n```\n\nRequirements:\n  R1 contract:\nKeep all items.\n\nDetailed Workflow:\n\n- `worker`:\n  a --step--> b\n\n#### Name with closing ### ###\nx --step--> y\n"
    source = inputs(tmp_path, text)
    report = check_roundtrip(source)
    assert report.status == "passed", report.model_dump_json(indent=2)


def test_story_states_anchors_uses_and_reference_fields(tmp_path):
    text = "## States\n### State ready — Ready\nDescription:\nReady.\n\nUses:\n- State/ready -> UC4\n\n## User stories\n### 2. Read\nx --read--> y\n\nWorkflow anchors:\n- step1: read\n\nUses:\n- S2.step1 -> UC4\n\nE2E tests:\n- description: visible result\n  requirements: UC4/R1\n\n## Use cases\n### 4. Produce\nx --step--> y\n\nRequirements:\nR1: Ready.\n\nRequirement representations:\n - source: UC4/R1\n"
    report = check_roundtrip(inputs(tmp_path, text))
    assert report.status == "passed", report.model_dump_json(indent=2)


def test_overlapping_typed_spans_are_rejected(tmp_path):
    source = inputs(tmp_path, "## Use cases\n### Read\nx --read--> y\n\nRequirements:\nR1: Text.\n")
    parsed = parse_document(source.documents[0], source.options)
    parsed.entities[0].layers[0].source = parsed.entities[0].source
    with pytest.raises(RenderingError, match="overlap"):
        render_markdown(parsed)


def test_broken_renderer_reports_structural_and_stability_differences(tmp_path, monkeypatch):
    from spec_markdown import roundtrip
    source = inputs(tmp_path, "## Use cases\n### Read\nx --read--> y\n")
    original = roundtrip.render_markdown
    calls = 0
    def broken(document):
        nonlocal calls
        calls += 1
        return original(document).replace("Read", "Changed", 1) + ("\n" * calls)
    monkeypatch.setattr(roundtrip, "render_markdown", broken)
    report = roundtrip.check_roundtrip(source)
    assert [check.status for check in report.checks] == ["passed", "failed", "failed"]
    assert any("title" in d.path for d in report.checks[1].differences)


@pytest.mark.parametrize("mode", ["canonical", "lossless"])
def test_renderer_cli_and_input_protection(tmp_path, capsys, mode):
    from render_specs import main
    text = b"\xef\xbb\xbf## Use cases\r\n### Read\r\nx --read--> y\r\n"
    source, output = tmp_path / "source.md", tmp_path / "output.md"
    source.write_bytes(text)
    args = ["source.md", "--workspace-root", str(tmp_path), "--output", str(output), "--mode", mode, "--log-file", str(tmp_path / "render.log")]
    assert main(args) == 0
    assert output.read_bytes().startswith(b"\xef\xbb\xbf")
    if mode == "lossless":
        assert output.read_bytes() == text
    assert source.read_bytes() == text
    args[args.index("--output") + 1] = str(source)
    assert main(args) == 1
    assert source.read_bytes() == text
    capsys.readouterr()


def test_renderer_cli_failed_atomic_write_preserves_output(tmp_path, monkeypatch, capsys):
    import render_specs as cli
    (tmp_path / "source.md").write_text("## Use cases\n### Read\nx --read--> y\n", encoding="utf-8")
    output = tmp_path / "out.md"
    output.write_bytes(b"existing output")
    def fail(*args):
        raise OSError("injected write failure")
    monkeypatch.setattr(cli.os, "replace", fail)
    assert cli.main(["source.md", "--workspace-root", str(tmp_path), "--output", str(output), "--log-file", str(tmp_path / "render.log")]) == 2
    assert output.read_bytes() == b"existing output"
    assert not list(tmp_path.glob(".planning-render-*"))
    capsys.readouterr()


def test_unrenderable_reference_context_blocks_only_dependent_comparison(tmp_path):
    source = inputs(tmp_path, "## Use cases\n### Read\nx --read--> y\n\nRealizes:\n- broken.md#UC4/R1\n")
    source.documents.append(DocumentSnapshot.from_text("broken.md", "## Use cases\n### 4. Broken\n\nRequirements:\nR1: Required.\n"))
    report = check_roundtrip(source)
    caller_checks = [c for c in report.checks if c.document_id == "spec.md"]
    assert [c.status for c in caller_checks] == ["passed", "blocked", "passed"]
    assert caller_checks[1].differences[0].path == "$.references"


def test_validation_cli_rejects_development_check_flag(tmp_path, capsys):
    import json
    from validate_specs import main
    (tmp_path / "spec.md").write_text("## Use cases\n### Read\nx --read--> y\n", encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main(["spec.md", "--workspace-root", str(tmp_path), "--check-roundtrip", "--format", "json"])
    assert error.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err
