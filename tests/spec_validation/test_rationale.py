"""T-19: independent rationale expectations, recovery and three-check evidence."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from spec_validation.api import validate_documents
from spec_validation.models import (
    DocumentSet, DocumentSnapshot, InvariantDerivation, ParsedDocument, RationaleNote,
    ValidEntry, ValidationOptions,
)
from spec_validation.parser import parse_document
from spec_markdown.rendering import reconstruct_markdown, render_markdown
from spec_markdown.roundtrip import check_roundtrip, compare_documents


PREFIX = "## Use cases\n\n### 1. Construct\nx --build--> y\n\nInvariants:\n"
NOTE = "  - `N1`:\n    - note: An idea.\n    - assessment: supported\n"
FIXTURE = Path(__file__).parent / "fixtures" / "rationale.md"


def inputs(tmp_path, text, **peers):
    return DocumentSet(
        documents=[DocumentSnapshot.from_text("spec.md", text), *[
            DocumentSnapshot.from_text(name, body) for name, body in peers.items()
        ]], options=ValidationOptions(workspace_root=tmp_path),
    )


def notes(document):
    return [entry.value for owner in document.entities for layer in owner.layers
            for entry in layer.all_entries if isinstance(entry, ValidEntry) and isinstance(entry.value, RationaleNote)]


def diagnostics(tmp_path, body):
    result = validate_documents(inputs(tmp_path, PREFIX + body), include_documents=True)
    return result, [item.code for item in result.report.diagnostics]


def test_independent_fixture_objects_and_json(tmp_path):
    source = inputs(tmp_path, FIXTURE.read_text(encoding="utf-8"))
    result = validate_documents(source, include_documents=True)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    parsed = result.documents[0]
    values = notes(parsed)
    assert [(note.rationale_id, note.assessment) for note in values] == [
        ("N1", "supported"), ("N2", "qualified"), ("N3", "rejected"), (None, "unsupported"),
    ]
    assert values[0].note.markdown == " Canonicalization preserves the accepted meaning."
    assert values[1].qualification.markdown == " Construction must cover every required element."
    assert values[2].replacement.markdown == " Construction establishes completeness."
    assert [ref.member_selector.value for ref in values[0].used_by] == ["D1"]
    assert values[0].used_by[0].owner_local
    assert ParsedDocument.model_validate_json(parsed.model_dump_json()) == parsed
    assert check_roundtrip(source).status == "passed"


def test_published_authoring_example(tmp_path):
    reference = Path(__file__).resolve().parents[2] / "skill/layered-spec-core/references/invariants.md"
    text = reference.read_text(encoding="utf-8").split("````md\n", 1)[1].split("\n````", 1)[0]
    source = inputs(tmp_path, PREFIX.removesuffix("Invariants:\n") + text)
    result = validate_documents(source, include_documents=True)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    assert [note.rationale_id for note in notes(result.documents[0])] == ["N1", "N2", "N3"]
    assert check_roundtrip(source).status == "passed"


@pytest.mark.parametrize("ending", ["", "\n", "\r\n"])
def test_standalone_rationale_expected_canonical(tmp_path, ending):
    source = inputs(tmp_path, PREFIX + "- Rationale:\n" + NOTE.rstrip("\n") + ending)
    parsed = parse_document(source.documents[0], source.options)
    expected = (
        "## Use cases\n\n### UC1 — Construct ###\n```workflow\nx --build--> y\n```\n\n"
        "Invariants:\n- Rationale:\n" + NOTE + "\n"
    )
    assert render_markdown(parsed) == expected
    assert len(notes(parsed)) == 1
    assert check_roundtrip(source).status == "passed"


@pytest.mark.parametrize("position", ["before", "after"])
def test_subsection_order_and_body_ownership(tmp_path, position):
    fixture = FIXTURE.read_text(encoding="utf-8")
    start = fixture.index("- Rationale:")
    stop = fixture.index("- State invariants:")
    rationale = fixture[start:stop]
    body = fixture[:start] + fixture[stop:]
    text = fixture if position == "before" else body + "\n\n" + rationale + "\nLogic:\nDone.\n"
    source = inputs(tmp_path, text)
    parsed = parse_document(source.documents[0], source.options)
    assert not parsed.diagnostics
    assert len(notes(parsed)) == 4
    for layer in parsed.entities[0].layers:
        for entry in layer.all_entries:
            if isinstance(entry, ValidEntry) and isinstance(entry.value, InvariantDerivation):
                assert "Rationale" not in entry.value.justification.markdown
    assert check_roundtrip(source).status == "passed"


@pytest.mark.parametrize("assessment,extra,expected", [
    ("supported", "", []),
    ("qualified", "", ["RATIONALE_FIELD_REQUIRED"]),
    ("qualified", "    - qualification: Only this part.\n", []),
    ("unsupported", "", ["RATIONALE_FIELD_REQUIRED"]),
    ("rejected", "", ["RATIONALE_FIELD_REQUIRED"]),
    ("rejected", "    - reason: Incorrect.\n", []),
    ("nonsense", "", ["INVALID_RATIONALE_STRUCTURE"]),
])
def test_assessment_contract(tmp_path, assessment, extra, expected):
    _, codes = diagnostics(tmp_path, "- Rationale:\n" + NOTE.replace("supported", assessment) + extra)
    for code in expected:
        assert code in codes
    if not expected:
        assert not codes


def test_independent_usage_errors_and_missing_targets(tmp_path):
    body = "- Rationale:\n  - note: Unsupported idea.\n    - assessment: rejected\n    - used by: D404, D405\n"
    _, codes = diagnostics(tmp_path, body)
    assert "RATIONALE_FIELD_REQUIRED" in codes
    assert "RATIONALE_ID_REQUIRED" in codes
    assert "RATIONALE_USAGE_NOT_ALLOWED" in codes
    assert codes.count("MISSING_MEMBER") == 2


def test_duplicate_notes_and_subsections(tmp_path):
    _, codes = diagnostics(tmp_path, "- Rationale:\n" + NOTE + NOTE)
    assert "DUPLICATE_RATIONALE" in codes
    _, codes = diagnostics(tmp_path, "- Rationale:\n" + NOTE + "- Rationale:\n" + NOTE.replace("N1", "N2"))
    assert "DUPLICATE_INVARIANT_SECTION" in codes


@pytest.mark.parametrize("broken", [
    "    - assessment: supported\n",
    "    - mystery: value\n",
    "    - reason:\n",
    "    - used by: I1, UC1, invalid\n",
    "    - used by:\n",
    "    - assessment: supported\n      continuation\n",
    "   - reason: wrong indentation\n",
    "    - reason: valid\nwrong continuation\n",
])
def test_field_errors_recover_at_next_note(tmp_path, broken):
    body = "- Rationale:\n" + NOTE + broken + NOTE.replace("N1", "N2")
    result, codes = diagnostics(tmp_path, body)
    assert "INVALID_RATIONALE_STRUCTURE" in codes
    assert [note.rationale_id for note in notes(result.documents[0])] == ["N2"]
    checks = check_roundtrip(inputs(tmp_path, PREFIX + body))
    assert [check.status for check in checks.checks] == ["passed", "blocked", "blocked"]


def test_multiple_field_errors_and_malformed_header_recovery(tmp_path):
    body = "- Rationale:\n  - `N0`:\n    - note: Bad identifier.\n" + NOTE.replace("N1", "N2")
    result, codes = diagnostics(tmp_path, body)
    assert "INVALID_RATIONALE_STRUCTURE" in codes
    assert [note.rationale_id for note in notes(result.documents[0])] == ["N2"]
    body = "- Rationale:\n  - `N1`:\n    - unknown: text\n    - reason:\n    - used by: I1, UC1\n"
    result, _ = diagnostics(tmp_path, body)
    errors = [d for d in result.report.diagnostics if d.code == "INVALID_RATIONALE_STRUCTURE"]
    assert len(errors) >= 6


@pytest.mark.parametrize("subsection", [" - Rationale:", "  - Rationale:", "Rationale:"])
def test_misplaced_subsection(tmp_path, subsection):
    _, codes = diagnostics(tmp_path, "\n" + subsection + "\n" + NOTE)
    assert "INVALID_INVARIANT_NESTING" in codes


def test_markdown_bodies_literals_whitespace_and_spans(tmp_path):
    body = (
        "- Rationale:\n  - `N1`:\n    - assessment: supported\n    - note:\n"
        "      First paragraph.  \n\n      - nested item\n      - `N9`: an example\n      - Rationale:\n"
        "      ```md\n      - Rationale:\n        - assessment: invalid\n      ```\n"
        "      Last\tparagraph.\n"
    ).replace("\n", "\r\n")
    source = inputs(tmp_path, PREFIX + body)
    parsed = parse_document(source.documents[0], source.options)
    assert not parsed.diagnostics
    note = notes(parsed)[0]
    assert "\r\n\r\n      - nested item" in note.note.markdown
    assert "        - assessment: invalid" in note.note.markdown
    span = note.note.source
    assert source.documents[0].source_text[span.start_offset:span.end_offset] == note.note.markdown
    assert reconstruct_markdown(parsed) == source.documents[0].source_text
    assert check_roundtrip(source).status == "passed"


def test_requirement_after_rationale_has_independent_source_ownership(tmp_path):
    text = PREFIX + "- Rationale:\n" + NOTE + "\nR1.1: A requirement.\n"
    source = inputs(tmp_path, text)
    parsed = parse_document(source.documents[0], source.options)
    assert not parsed.diagnostics
    assert "R1.1" not in notes(parsed)[0].note.markdown
    assert check_roundtrip(source).status == "passed"


def test_rationale_preamble_does_not_hide_unowned_text(tmp_path):
    result, codes = diagnostics(tmp_path, "- Rationale:\n  Free text without note marker.\n" + NOTE)
    assert "INVALID_RATIONALE_STRUCTURE" in codes
    assert len(notes(result.documents[0])) == 1


def test_cross_file_used_by_and_rationale_reference(tmp_path):
    local = PREFIX + "- Rationale:\n" + NOTE + "    - used by: peer.md#use-case Build/D1\n"
    peer = (
        "## Use cases\n### Build\nx --build--> y\n\nInvariants:\n"
        "- State invariants:\n  - `I1` at `x`: Valid.\n  - `I2` at `y`: Complete.\n"
        "- Derivations:\n  - `D1: I1 -> I2`\n    - workflow transition: build\n    - justification: Constructed.\n"
        "\nTests:\n - description: Rationale reference.\n   requirements: spec.md#UC1/N1\n"
    )
    source = inputs(tmp_path, local, **{"peer.md": peer})
    result = validate_documents(source)
    assert result.status == "passed", result.model_dump_json(indent=2)
    assert check_roundtrip(source).status == "passed"


def test_typed_mutation_changes_rendering_and_semantic_comparison(tmp_path):
    source = inputs(tmp_path, PREFIX + "- Rationale:\n" + NOTE)
    parsed = parse_document(source.documents[0], source.options)
    changed = parsed.model_copy(deep=True)
    note = notes(changed)[0]
    note.rationale_id = "N2"
    note.assessment = "qualified"
    note.note.markdown = " Changed meaning."
    note.qualification = note.note.model_copy(update={"markdown": " Only for valid inputs."})
    output = render_markdown(changed)
    assert "`N2`" in output and "assessment: qualified" in output
    assert "qualification: Only for valid inputs." in output
    after = parse_document(DocumentSnapshot.from_text("spec.md", output), source.options)
    changes = compare_documents([parsed], [after], source)["spec.md"]
    assert any("rationale_id" in change.path for change in changes)
    assert any("assessment" in change.path for change in changes)
    assert any("qualification" in change.path for change in changes)


def test_pydantic_rejects_empty_body_and_invalid_assessment(tmp_path):
    source = inputs(tmp_path, PREFIX + "- Rationale:\n" + NOTE)
    note = notes(parse_document(source.documents[0], source.options))[0]
    fields = note.model_dump()
    fields["note"]["markdown"] = "  "
    fields["assessment"] = "incorrect"
    with pytest.raises(ValidationError) as failure:
        RationaleNote.model_validate(fields)
    assert len(failure.value.errors()) == 2
