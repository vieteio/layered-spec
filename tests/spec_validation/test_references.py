from pathlib import Path

import pytest

from spec_validation.api import validate_documents
from spec_validation.models import DocumentSet, DocumentSnapshot, ValidationOptions
from spec_validation.syntax import SyntaxFailure, reference


def validate(texts, tmp_path):
    return validate_documents(DocumentSet(documents=[DocumentSnapshot.from_text(name, text) for name, text in texts.items()], options=ValidationOptions(workspace_root=tmp_path)))


def contract(forward="UC7", reverse="UC4/R4.1", *, requirement="R4.1", owner="4. Render"):
    return f"""## Use cases
### {owner}
in --render--> out

Requirements:
Requirement: {requirement}
Required result.

Realized by:
- requirement {requirement} -> {forward}

### 7. Build
in --build--> out

Realizes:
- {reverse}
"""


@pytest.mark.parametrize("reverse", ["UC4/R4.1", "use-case 4/requirement R4.1", "use-case Render/R4.1", "use-case Render/requirement R4.1"])
def test_reference_aliases_satisfy_same_reciprocal_edge(reverse, tmp_path):
    report = validate({"s.md": contract(reverse=reverse)}, tmp_path)
    assert report.status == "passed", report.model_dump_json(indent=2)


def test_distinct_identifier_is_not_prefixed_automatically(tmp_path):
    report = validate({"s.md": contract(requirement="4.1", reverse="UC4/R4.1")}, tmp_path)
    assert "MISSING_MEMBER" in [d.code for d in report.diagnostics]
    assert "REALIZATION_FORWARD_MISSING" not in [d.code for d in report.diagnostics]


def test_both_missing_directions_are_reported(tmp_path):
    text = contract(forward="UC8") + "\n### 8. Other\nin --other--> out\n"
    report = validate({"s.md": text}, tmp_path)
    assert {"REALIZATION_FORWARD_MISSING", "REALIZATION_REVERSE_MISSING"} <= {d.code for d in report.diagnostics}


def test_target_requirement_refinements_share_one_reverse(tmp_path):
    text = contract(forward="UC7/R7.1, UC7/R7.2") + "\n\nRequirements:\nR7.1: First clause.\n\nR7.2: Second clause.\n"
    report = validate({"s.md": text}, tmp_path)
    assert report.status == "passed", report.model_dump_json(indent=2)


def test_duplicate_alias_edges_are_not_extra_graph_nodes(tmp_path):
    report = validate({"s.md": contract(forward="UC7, use-case Build")}, tmp_path)
    assert [d.code for d in report.diagnostics] == ["DUPLICATE_REALIZATION"]


def test_cross_file_reference_with_spaces_and_named_requirement(tmp_path):
    first = "## Use cases\n### Render\nin --render--> out\n\nRequirements:\nRequirement: Configuration requirement\nConfigured.\n\nRealized by:\n- requirement Configuration requirement -> sub/build%20spec.md#use-case Build\n"
    second = "## Use cases\n### Build\nin --build--> out\n\nRealizes:\n- ../render.md#use-case Render/requirement Configuration requirement\n"
    report = validate({"render.md": first, "sub/build spec.md": second}, tmp_path)
    assert report.status == "passed", report.model_dump_json(indent=2)


@pytest.mark.parametrize("ref", ["../escape.md#UC7", "https://example.com/x.md#UC7", "C:/x.md#UC7", "sub%ZZ.md#UC7", "bad path.md#UC7"])
def test_reference_paths_are_checked_without_fetching(ref, tmp_path):
    report = validate({"s.md": contract(forward=ref)}, tmp_path)
    assert any(d.code in ("INVALID_REFERENCE_PATH", "MALFORMED_MAPPING") for d in report.diagnostics)


def test_missing_document_does_not_become_missing_reverse(tmp_path):
    report = validate({"s.md": contract(forward="missing.md#UC7")}, tmp_path)
    assert "MISSING_DOCUMENT" in [d.code for d in report.diagnostics]
    assert "REALIZATION_REVERSE_MISSING" not in [d.code for d in report.diagnostics]
    assert not report.analysis_complete


def test_duplicate_titles_block_title_only(tmp_path):
    text = contract() + "\n### 8. Build\nin --build--> out\n"
    report = validate({"s.md": text}, tmp_path)
    assert [d.code for d in report.diagnostics] == ["DUPLICATE_USE_CASE_TITLE"]
    ambiguous = validate({"s.md": text.replace("-> UC7", "-> use-case Build")}, tmp_path)
    assert "AMBIGUOUS_REFERENCE" in [d.code for d in ambiguous.diagnostics]


def test_duplicate_numbers_can_resolve_by_title(tmp_path):
    text = contract(forward="use-case Build") + "\n### 7. Other\nin --other--> out\n"
    report = validate({"s.md": text}, tmp_path)
    assert [d.code for d in report.diagnostics] == ["DUPLICATE_USE_CASE_NUMBER"]


def test_quoted_titles_identifiers_and_numeric_title(tmp_path):
    text = contract(owner='"4"', requirement='"Input/output: configuration"', reverse='use-case "4"/requirement "Input/output: configuration"')
    assert validate({"s.md": text}, tmp_path).status == "passed"
    assert validate({"s.md": text.replace("S2.step3 -> UC4", "`S2.step3` -> `UC4`")}, tmp_path).status == "passed"


def test_cycle_scc_and_recursive_uses_are_separate(tmp_path):
    cases = []
    for number, target in ((1, 2), (2, 3), (3, 1)):
        previous = 3 if number == 1 else number - 1
        cases.append(f"### {number}. Case {number}\nin --process--> out\n\nRequirements:\nR{number}: Required.\n\nRealized by:\n- R{number} -> UC{target}\n\nRealizes:\n- UC{previous}/R{previous}\n\nUses:\n- \"recurse\" -> UC{number}\n")
    report = validate({"s.md": "## Use cases\n" + "\n".join(cases)}, tmp_path)
    assert [d.code for d in report.diagnostics] == ["REALIZATION_CYCLE"]
    cycle = report.diagnostics[0]
    assert len(cycle.related_locations) == 2


def test_bad_counterpart_suppresses_speculative_reverse(tmp_path):
    report = validate({"s.md": contract(reverse="malformed")}, tmp_path)
    assert "MALFORMED_MAPPING" in [d.code for d in report.diagnostics]
    assert "REALIZATION_REVERSE_MISSING" not in [d.code for d in report.diagnostics]


def test_story_state_and_declared_anchor_uses(tmp_path):
    text = """## States
### State ready — Ready

Description:
Ready to start.

Uses:
- State/ready -> UC4

## User stories
### S2 — Read a result
input --Application reads--> result

Workflow anchors:
- step3: Application reads

Uses:
- S2.step3 -> UC4

E2E tests:
- Read the result and observe the output.

## Use cases
### 4. Read
input --read--> result
"""
    assert validate({"s.md": text}, tmp_path).status == "passed"
    failed = validate({"s.md": text.replace("S2.step3 ->", "S2.step9 ->")}, tmp_path)
    assert "MISSING_MEMBER" in [d.code for d in failed.diagnostics]
