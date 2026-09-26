"""Run the copied skill runtime without application paths or implicit configuration."""

import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

import render_specs
import validate_specs


CORE = Path(__file__).resolve().parents[2] / "skill/layered-spec-core"
VALID = "## Use cases\n\n### 1. Read\ninput --read--> result\n"


def run_script(script, workspace, cwd, *arguments):
    environment = {key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "LOGFIRE_TOKEN"}}
    return subprocess.run(
        [sys.executable, str(script), "--workspace-root", str(workspace), *arguments],
        cwd=cwd, env=environment, capture_output=True, text=True, encoding="utf-8", check=False,
    )


def test_copied_core_validation_feedback_without_development_tools(tmp_path):
    copied = tmp_path / "portable core"
    shutil.copytree(CORE, copied, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    workspace, unrelated = tmp_path / "documents", tmp_path / "unrelated cwd"
    workspace.mkdir()
    unrelated.mkdir()
    # Unselected dotenv files must not activate telemetry or introduce a backend dependency.
    for location in (workspace, unrelated):
        (location / ".env").write_text("LOGFIRE_TOKEN=unused-test-token\n", encoding="utf-8")
    parent = workspace / "parent.md"
    child = workspace / "child.md"
    parent.write_text(VALID + "\nRequirements:\nR1: Read.\n\nRealized by:\n- R1 -> child.md#UC2\n", encoding="utf-8")
    child.write_text("## Use cases\n\n### 2. Implement\nx --read--> y\n", encoding="utf-8")
    validator = copied / "scripts/validate_specs.py"
    arguments = ("--format", "json", "parent.md", "child.md")
    failed = run_script(validator, workspace, unrelated, *arguments)
    assert failed.returncode == 1, failed.stderr
    report = json.loads(failed.stdout)
    assert report["status"] == "failed"
    assert report["diagnostics"]
    assert all("primary_location" in item for item in report["diagnostics"])
    # A preparing agent's reciprocal correction is accepted only by a fresh validation.
    child.write_text(child.read_text() + "\nRealizes:\n- parent.md#UC1/R1\n", encoding="utf-8")
    passed = run_script(validator, workspace, unrelated, *arguments)
    assert passed.returncode == 0, passed.stderr + passed.stdout
    fresh = json.loads(passed.stdout)
    assert fresh["input_set_fingerprint"] != report["input_set_fingerprint"]
    assert not {"preservation", "structural_roundtrip", "canonical_stability"} & {c["check"] for c in fresh["checks"]}
    for relative in ("scripts/render_specs.py", "scripts/spec_validation/rendering.py", "scripts/spec_validation/roundtrip.py"):
        assert not (copied / relative).exists()
    assert (workspace / ".agents/logs/spec_validation.log").is_file()
    assert not (unrelated / ".agents").exists()
    assert not (copied / "bundled").exists()
    output = workspace / "rendered.md"
    rendered = run_script(Path(__file__).with_name("render_specs.py"), workspace, unrelated, "parent.md", "--output", str(output), "--mode", "lossless")
    assert rendered.returncode == 0, rendered.stderr
    assert output.read_bytes() == parent.read_bytes()
    assert (workspace / ".agents/logs/spec_rendering.log").is_file()


@pytest.mark.parametrize("cli", [validate_specs, render_specs])
def test_explicit_missing_environment_file_is_a_tool_error(tmp_path, capsys, cli):
    (tmp_path / "spec.md").write_text(VALID, encoding="utf-8")
    arguments = ["--workspace-root", str(tmp_path), "spec.md", "--env-file", str(tmp_path / "missing.env")]
    if cli is render_specs:
        arguments += ["--output", str(tmp_path / "out.md")]
    else:
        arguments += ["--format", "json"]
    assert cli.main(arguments) == 2
    captured = capsys.readouterr()
    if cli is validate_specs:
        assert json.loads(captured.out)["status"] == "tool_error"
    else:
        assert "Environment file does not exist" in captured.err


@pytest.mark.parametrize("cli", [validate_specs, render_specs])
def test_explicit_environment_configures_optional_telemetry(tmp_path, monkeypatch, capsys, cli):
    monkeypatch.delenv("LOGFIRE_TOKEN", raising=False)
    calls = []
    monkeypatch.setitem(sys.modules, "logfire", SimpleNamespace(
        configure=lambda **options: calls.append(options), LogfireLoggingHandler=logging.NullHandler,
    ))
    (tmp_path / "spec.md").write_text(VALID, encoding="utf-8")
    environment = tmp_path / "selected.env"
    environment.write_text("LOGFIRE_TOKEN=local-test-token\n", encoding="utf-8")
    arguments = ["--workspace-root", str(tmp_path), "spec.md", "--env-file", str(environment)]
    if cli is render_specs:
        arguments += ["--output", str(tmp_path / "out.md")]
    assert cli.main(arguments) == 0
    assert calls == [{"console": False}]
    capsys.readouterr()
