import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

import pytest

from spec_validation.api import validate_documents
from spec_validation.feedback import FeedbackState, record_repair_attempt, report_is_current
from spec_validation.loading import load_document_set
from spec_validation.models import ValidationOptions
import validate_specs as cli


VALID = "## Use cases\r\n\r\n### Read 😀\r\nin --read--> out\r\n"


def inputs(tmp_path, text=VALID):
    path = tmp_path / "spec.md"
    path.write_bytes(text.encode("utf-8"))
    options = ValidationOptions(workspace_root=tmp_path)
    return path, load_document_set([path], options)


def arguments(tmp_path, *extra):
    return ["--workspace-root", str(tmp_path), "--format", "json", "--log-file", str(tmp_path / "validator.log"), *extra, "spec.md"]


def test_load_bom_crlf_unicode_and_independent_failures(tmp_path):
    contents = b"\xef\xbb\xbf" + VALID.encode("utf-8")
    (tmp_path / "spec.md").write_bytes(contents)
    (tmp_path / "bad.md").write_bytes(b"\xff")
    options = ValidationOptions(workspace_root=tmp_path)
    loaded = load_document_set(["spec.md", "bad.md", "missing.md"], options)
    assert len(loaded.documents) == 1
    snapshot = loaded.documents[0]
    assert snapshot.source_text == VALID
    assert snapshot.content_sha256 == sha256(contents).hexdigest()
    assert snapshot.byte_count == len(contents)
    report = validate_documents(loaded)
    assert {d.code for d in report.diagnostics} == {"INVALID_ENCODING", "INPUT_UNREADABLE"}
    assert report.status == "failed" and not report.analysis_complete


def test_input_aliases_and_workspace_escape(tmp_path):
    path, loaded = inputs(tmp_path)
    loaded = load_document_set([path, "./spec.md", "../outside.md"], loaded.options)
    assert {d.code for d in loaded.failed_inputs} == {"DUPLICATE_DOCUMENT", "INVALID_REFERENCE_PATH"}
    assert len(loaded.documents) == 1


@pytest.mark.parametrize("limits", [{"max_file_bytes": 5}, {"max_total_bytes": 5}])
def test_bounded_read(tmp_path, limits):
    path, loaded = inputs(tmp_path)
    loaded = load_document_set([path], loaded.options.model_copy(update=limits))
    assert not loaded.documents
    assert [d.code for d in loaded.failed_inputs] == ["INPUT_LIMIT_EXCEEDED"]


def test_freshness_and_deterministic_semantic_report(tmp_path):
    path, loaded = inputs(tmp_path)
    first = validate_documents(loaded)
    second = validate_documents(loaded)
    assert first.model_dump(exclude={"metrics"}) == second.model_dump(exclude={"metrics"})
    assert report_is_current(first, loaded)
    changed_options = loaded.model_copy(update={"options": loaded.options.model_copy(update={"max_nesting_depth": 64})})
    assert not report_is_current(first, changed_options)
    path.write_bytes((VALID + "\n").encode())
    assert not report_is_current(first, load_document_set([path], loaded.options))


def test_feedback_stops_unchanged_attempts_and_passes(tmp_path):
    _, loaded = inputs(tmp_path, "## Use cases\n### Invalid\n")
    report = validate_documents(loaded)
    state = FeedbackState()
    assert record_repair_attempt(state, report) == "retry"
    assert record_repair_attempt(state, report) == "unresolved"
    _, valid = inputs(tmp_path)
    assert record_repair_attempt(FeedbackState(), validate_documents(valid)) == "passed"


def test_cli_json_saved_report_and_log(tmp_path, capsys):
    path, _ = inputs(tmp_path)
    before = path.read_bytes()
    destination = tmp_path / "report.json"
    assert cli.main(arguments(tmp_path, "--report-json", str(destination))) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == json.loads(destination.read_text(encoding="utf-8"))
    assert not captured.err
    assert "status=passed" in (tmp_path / "validator.log").read_text()
    assert path.read_bytes() == before


def test_cli_text_and_multiple_diagnostics(tmp_path, capsys):
    inputs(tmp_path, "## Use cases\n### First\n\n### Second\n")
    assert cli.main(arguments(tmp_path, "--format", "text")) == 1
    output = capsys.readouterr().out
    assert output.count("MISSING_WORKFLOW") == 2
    assert "Not checked:" in output


@pytest.mark.parametrize("target", ["spec.md", "missing/report.json"])
def test_cli_report_failure_preserves_input(tmp_path, capsys, target):
    path, _ = inputs(tmp_path)
    before = path.read_bytes()
    assert cli.main(arguments(tmp_path, "--report-json", str(tmp_path / target))) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "tool_error"
    assert report["diagnostics"][-1]["code"] == "REPORT_WRITE_FAILED"
    assert path.read_bytes() == before


@pytest.mark.parametrize("error", [RuntimeError("injected"), ValueError("injected")])
def test_cli_unexpected_failure_is_machine_readable(tmp_path, capsys, monkeypatch, error):
    inputs(tmp_path)
    def fail(_):
        raise error
    monkeypatch.setattr(cli, "validate_documents", fail)
    assert cli.main(arguments(tmp_path)) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "tool_error"
    assert [d["code"] for d in report["diagnostics"]] == ["TOOL_FAILURE"]
    assert "Traceback" in (tmp_path / "validator.log").read_text()


def test_cli_refuses_input_as_log(tmp_path, capsys):
    path, _ = inputs(tmp_path)
    before = path.read_bytes()
    assert cli.main(arguments(tmp_path, "--log-file", str(path))) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "tool_error"
    assert path.read_bytes() == before


def test_module_entrypoint_and_no_database_imports(tmp_path):
    inputs(tmp_path, "# Notes\nNo planning region.\n")
    script = Path(__file__).resolve().parents[2] / "skill/layered-spec-core/scripts/validate_specs.py"
    process = subprocess.run([sys.executable, str(script), *arguments(tmp_path)], cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", check=False)
    assert process.returncode == 1, process.stderr
    assert json.loads(process.stdout)["status"] == "failed"
    assert not any(name.startswith("viete.database") for name in sys.modules)
