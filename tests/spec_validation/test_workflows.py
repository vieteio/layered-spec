from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from spec_validation.api import validate_documents
from spec_validation.models import (
    DetailedWorkflowLayer, DocumentSet, DocumentSnapshot, InvalidWorkflowChain,
    ValidationOptions, ValidationResult, ValidWorkflowChain, WorkflowChain,
    WorkflowConditional, WorkflowExpression, WorkflowLoop, WorkflowParallel, WorkflowProse,
    WorkflowScope, WorkflowSequence, WorkflowState,
)
from spec_validation.workflow_expressions import WorkflowSyntaxFailure, parse_expression


def inspect(text, tmp_path, **options):
    return validate_documents(DocumentSet(documents=[DocumentSnapshot.from_text("s.md", text)], options=ValidationOptions(workspace_root=tmp_path, **options)), include_documents=True)


def expression(text, max_depth=128):
    snapshot = DocumentSnapshot.from_text("s.md", text)
    return parse_expression(snapshot, snapshot.span(0, len(text)), max_depth)


def semantic(node):
    if isinstance(node, dict):
        return {key: semantic(value) for key, value in node.items() if key != "source"}
    if isinstance(node, list):
        return [semantic(value) for value in node]
    return node


@pytest.mark.parametrize("text,kind", [
    ("a --read--> b --write--> c", "sequence"),
    ("a: Input --parse--> b: list[Output]", "sequence"),
    ("[a --first--> x, b --second--> y]", "conditional"),
    ("(a --first--> x, b --second--> y)", "parallel"),
    ("| for each file: file --read--> text |", "loop"),
    ("{a --old--> b} --refactor--> {a --new--> b}", "sequence"),
    ("branch(left, right) --split--> (left --call--> x, right --call--> y) --combine--> result", "sequence"),
    ('"input, [raw]" --read "-->" literally--> `output: [text]`', "sequence"),
    ("a --dispatch--> [base --return--> result, nested --recurse--> result]", "sequence"),
    ("| for each child: child --dispatch--> [a --use step-a--> result, b --use step-b--> result] --append--> results |", "loop"),
])
def test_expression_forms_and_json_roundtrip(text, kind):
    parsed = expression(text)
    assert parsed.kind == kind
    adapter = TypeAdapter(WorkflowExpression)
    assert adapter.validate_json(adapter.dump_json(parsed)) == parsed


def test_states_types_and_transition_locations():
    text = "branch(left, right): Node[Tuple[A, B]] --process--> result: Result"
    parsed = expression(text)
    assert parsed.operands[0].name == "branch(left, right)"
    assert parsed.operands[0].type_annotation == "Node[Tuple[A, B]]"
    assert text[parsed.transitions[0].source.start_offset:parsed.transitions[0].source.end_offset] == "--process-->"
    assert parsed.operands[1].type_annotation == "Result"


@pytest.mark.parametrize("text", [
    "a --read-->", "--read--> b", "a ----> b", "a --read-> b",
    "a --dispatch--> [x --read--> y,]", "a --dispatch--> [x --read--> y",
    "a --dispatch--> (x --read--> y]", "| : a --read--> b |",
    "| condition a --read--> b |", "a: --read--> b", "just prose",
    "a --read--> b)", "branch(a --read--> b", "[a --read--> b] trailing text",
    'a --read--> "unclosed', 'a --read--> `unclosed', 'a --read--> "escaped\\"',
])
def test_malformed_expression_is_located(text):
    with pytest.raises(WorkflowSyntaxFailure) as failure:
        expression(text)
    assert 0 <= failure.value.source.start_offset <= len(text)


def test_main_and_detail_share_ast_and_preserve_blank_branches(tmp_path):
    chain = "input\n--dispatch-->\n[\n  base --return--> result,\n\n  nested\n  --invoke recursive-step recursively-->\n  result\n]"
    text = "## Use cases\n### 4. Process\n" + chain + "\n\nDetailed Workflow:\nSome explanation.\n\n#### recursive-step\n" + chain + "\n"
    result = inspect(text, tmp_path)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    owner = result.documents[0].entities[0]
    layer = owner.layers[0]
    assert isinstance(owner.workflow, WorkflowChain)
    assert isinstance(layer, DetailedWorkflowLayer)
    assert len(layer.chains) == 1
    assert result.report.metrics.workflow_chains == 2
    assert result.report.metrics.invalid_workflow_chains == 0
    assert result.report.tool_version == "0.2.3"
    assert semantic(owner.workflow.expression.model_dump()) == semantic(layer.chains[0].value.expression.model_dump())
    assert "\n\n  nested" in owner.workflow.body.markdown
    assert layer.chains[0].value.label == "recursive-step"
    assert ValidationResult.model_validate_json(result.model_dump_json()).documents[0].entities[0].workflow == owner.workflow


def test_compact_mutual_recursion_mixed_bullets_and_prose(tmp_path):
    text = (Path(__file__).parent / "fixtures" / "mixed_recursive_workflows.md").read_text(encoding="utf-8")
    result = inspect(text, tmp_path)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    layer = result.documents[0].entities[0].layers[0]
    assert [item.value.label for item in layer.chains] == ["recursive-step-a", "recursive-step-b", None, "fenced-step"]
    assert all(isinstance(item.value.expression, WorkflowSequence) for item in layer.chains)
    assert len([item for item in layer.content if isinstance(item, WorkflowProse)]) >= 3
    reconstructed = "".join(
        text[item.value.source.start_offset:item.value.source.end_offset] if isinstance(item, ValidWorkflowChain)
        else item.body.markdown for item in layer.content
    )
    assert reconstructed == layer.body.markdown


@pytest.mark.parametrize("opening,closing,label", [
    ("- `worker`:\n  ", "", "worker"),
    ("- worker:\n  ", "", "worker"),
    ("  worker:\n", "", "worker"),
    ("- **worker**: ", "", "worker"),
    ("#### worker\n", "", "worker"),
    ("- ", "", None),
    ("`", "`", None),
    ("```text\n", "\n```", None),
    ("```workflow\n", "\n```", None),
])
def test_embedded_chain_wrappers(opening, closing, label, tmp_path):
    text = "## Use cases\n### Main\na --read--> b\n\nDetailed Workflow:\n\n" + opening + "a --read--> b" + closing + "\n"
    result = inspect(text, tmp_path)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    chains = result.documents[0].entities[0].layers[0].chains
    assert len(chains) == 1
    assert chains[0].value.label == label


def test_mixed_literals_remain_prose(tmp_path):
    body = """Use `a --read--> b` as an example in prose.

- A plain explanatory bullet.
- Another note with `x --call--> y`.

> quoted --example--> text

```python
"a --looks-like--> workflow"
```

```md
a --example--> b
```

<!-- a --hidden--> b -->

    indented --code--> block

"""
    result = inspect("## Use cases\n### Main\na --read--> b\n\nDetailed Workflow:\n" + body, tmp_path)
    assert result.report.status == "passed"
    layer = result.documents[0].entities[0].layers[0]
    assert layer.chains == []
    assert layer.content[0].body.markdown == body


def test_sibling_chain_recovery_and_duplicate_labels(tmp_path):
    text = """## Use cases
### Main
a --read-->

Detailed Workflow:
- `bad`:
  a --choose--> [
    b --read--> c,

- `good`:
  x --read--> y

- `broken`:
  x --bad-> y

- `good`:
  z --read--> r

Requirements:
R1: Still recovered.

### Later
a --read--> b
"""
    result = inspect(text, tmp_path)
    issues = result.report.diagnostics
    assert len([item for item in issues if item.code == "INVALID_WORKFLOW"]) == 3
    assert result.report.metrics.invalid_workflow_chains == 3
    assert "DUPLICATE_WORKFLOW_LABEL" in [item.code for item in issues]
    owner = result.documents[0].entities[0]
    assert isinstance(owner.workflow_result, InvalidWorkflowChain)
    assert [isinstance(item, ValidWorkflowChain) for item in owner.layers[0].chains] == [False, True, False, True]
    assert owner.layers[1].entries[0].value.requirement_id == "R1"
    assert result.documents[0].entities[1].workflow.expression.kind == "sequence"


def test_inline_example_on_later_physical_line_stays_prose(tmp_path):
    text = "## Use cases\n### Main\na --read--> b\n\nDetailed Workflow:\nWe explain the notation using\n`input --read--> output`\ninside this prose paragraph.\n"
    result = inspect(text, tmp_path)
    assert result.report.status == "passed"
    assert result.documents[0].entities[0].layers[0].chains == []


def test_anonymous_chain_recovers_after_unclosed_sibling(tmp_path):
    text = "## Use cases\n### Main\na --read--> b\n\nDetailed Workflow:\na --choose--> [\n  b --read--> c,\n\nx --independent--> y\n"
    result = inspect(text, tmp_path)
    chains = result.documents[0].entities[0].layers[0].chains
    assert len(chains) == 2
    assert isinstance(chains[0], InvalidWorkflowChain)
    assert isinstance(chains[1], ValidWorkflowChain)


def test_nested_chain_depth_limit_and_next_sibling(tmp_path):
    text = "## Use cases\n### Main\na --read--> b\n\nDetailed Workflow:\n```workflow\n" + "{" * 8 + "a --read--> b" + "}" * 8 + "\n```\n\n- `later`: a --read--> b\n"
    result = inspect(text, tmp_path, max_nesting_depth=3)
    assert "WORKFLOW_NESTING_LIMIT_EXCEEDED" in [item.code for item in result.report.diagnostics]
    assert isinstance(result.documents[0].entities[0].layers[0].chains[-1], ValidWorkflowChain)


def test_exact_unicode_crlf_sources_inside_list_and_fence(tmp_path):
    text = "## Use cases\r\n### Main\r\na --read--> b\r\n\r\nDetailed Workflow:\r\n- `unicode`:\r\n  ```text\r\n  вход 😀: Input\r\n  --read-->\r\n  result\r\n  ```\r\n"
    result = inspect(text, tmp_path)
    assert result.report.status == "passed", result.report.model_dump_json(indent=2)
    chain = result.documents[0].entities[0].layers[0].chains[0].value
    assert chain.body.markdown == text[chain.body.source.start_offset:chain.body.source.end_offset]
    first = chain.expression.operands[0]
    assert first.text == "вход 😀: Input"
    assert (first.source.start_line, first.source.start_column) == (8, 3)
    assert text[first.source.start_offset:first.source.end_offset] == first.text


def test_sequence_model_rejects_disconnected_operands():
    parsed = expression("a --read--> b")
    with pytest.raises(ValidationError):
        WorkflowSequence(operands=parsed.operands + parsed.operands, transitions=parsed.transitions, source=parsed.source)


def test_schema_contains_shared_workflow_types():
    schema = ValidationResult.model_json_schema()
    assert {"WorkflowChain", "WorkflowSequence", "WorkflowParallel", "WorkflowConditional", "DetailedWorkflowLayer", "InvalidWorkflowChain"} <= set(schema["$defs"])
    assert schema["$defs"]["WorkflowParallel"]["properties"]["kind"]["const"] == "parallel"
    assert schema["$defs"]["WorkflowConditional"]["properties"]["kind"]["const"] == "conditional"
    assert schema["$defs"]["UseCase"]["properties"]["workflow"]["$ref"] == "#/$defs/WorkflowChain"
    assert schema["$defs"]["ValidationReport"]["properties"]["tool_version"]["default"] == "0.2.3"
