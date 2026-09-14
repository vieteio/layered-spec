"""Exercise the public distribution boundary through both real installers."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "skill/layered-spec-core"
HOST_PREFIXES = {
    "vscode": ".github", "cursor": ".cursor", "claude": ".claude",
    "codex": ".agents", "antigravity": ".agents",
}


@pytest.mark.parametrize("installer", ["python", "npm"])
@pytest.mark.parametrize("host,prefix", HOST_PREFIXES.items())
def test_installed_runtime_feedback_and_configuration_preservation(tmp_path, installer, host, prefix):
    project = tmp_path / "project with spaces"
    lifecycle = project / "specs/spec-lifecycle"
    lifecycle.mkdir(parents=True)
    settings = '{"validation":{"enabled":false},"future":{"custom":true}}\n'
    (lifecycle / "workflow.json").write_text(settings, encoding="utf-8")
    (lifecycle / "workflow.md").write_text("Custom lifecycle\n", encoding="utf-8")
    (project / ".gitignore").write_text("user-owned-entry\n", encoding="utf-8")

    match installer:
        case "python":
            command = [sys.executable, str(ROOT / "scripts/install_skillpack.py"),
                       "--host", host, "--scope", "repo", "--target-root", str(project)]
        case "npm":
            node = shutil.which("node")
            assert node, "Node is required to verify the public npm installer"
            command = [node, str(ROOT / "scripts/npm/bin/layered-spec.mjs"), "init",
                       "--host", host, "--target-root", str(project), "--no-update-check"]
    installed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
    assert installed.returncode == 0, installed.stderr
    copied = project / prefix / "skills/layered-spec-core"
    manifest = json.loads((project / prefix / "layered-spec-skillpack.json").read_text())
    template_relative = "skills/spec-first-planning-loop/assets/default_workflow.json"
    installed_template = project / prefix / template_relative
    source_template = ROOT / "skill/spec-first-planning-loop/assets/default_workflow.json"
    assert installed_template.read_bytes() == source_template.read_bytes()
    assert f"{prefix}/{template_relative}" in manifest["files"]
    assert json.loads(installed_template.read_text())["validation"]["installation"]["decision"] == "ask"
    expected_runtime = [CORE / "requirements.txt", *CORE.glob("scripts/*.py"),
                        *CORE.glob("scripts/spec_validation/*.py")]
    for source in expected_runtime:
        target = copied / source.relative_to(CORE)
        assert target.read_bytes() == source.read_bytes()
        assert target.relative_to(project).as_posix() in manifest["files"]
    assert not any("tests/" in file or "__pycache__" in file for file in manifest["files"])
    for relative in ("scripts/render_specs.py", "scripts/spec_validation/rendering.py", "scripts/spec_validation/roundtrip.py"):
        assert not (copied / relative).exists()
    instructions = (copied / "references/validation.md").read_text(encoding="utf-8")
    assert f"{prefix}/skills/layered-spec-core/scripts/validate_specs.py" in instructions
    assert f"{prefix}/skills/layered-spec-core/requirements.txt" in instructions
    assert (copied / "references/../../spec-first-planning-loop/assets/default_workflow.json").resolve() == installed_template.resolve()
    assert (lifecycle / "workflow.json").read_text() == settings
    assert (lifecycle / "workflow.md").read_text() == "Custom lifecycle\n"
    assert (project / ".gitignore").read_text() == "user-owned-entry\n"

    # Installation leaves policy untouched; an explicit CLI call validates supplied files.
    (project / "parent.md").write_text(
        "## Use cases\n\n### 1. Parent\nx --read--> y\n\nRequirements:\nR1: Read.\n"
        "\nRealized by:\n- R1 -> child.md#UC2\n", encoding="utf-8",
    )
    child = project / "child.md"
    child.write_text("## Use cases\n\n### 2. Child\nx --implement--> y\n", encoding="utf-8")
    validate = [sys.executable, str(copied / "scripts/validate_specs.py"),
                "--workspace-root", str(project), "--format", "json",
                "parent.md", "child.md"]
    environment = {key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "LOGFIRE_TOKEN"}}
    failed = subprocess.run(validate, cwd=tmp_path, env=environment, capture_output=True, text=True, check=False)
    assert failed.returncode == 1, failed.stderr
    old_report = json.loads(failed.stdout)
    assert old_report["diagnostics"]
    child.write_text(child.read_text() + "\nRealizes:\n- parent.md#UC1/R1\n", encoding="utf-8")
    passed = subprocess.run(validate, cwd=tmp_path, env=environment, capture_output=True, text=True, check=False)
    assert passed.returncode == 0, passed.stderr + passed.stdout
    assert json.loads(passed.stdout)["input_set_fingerprint"] != old_report["input_set_fingerprint"]


def test_python_installer_dry_run_leaves_target_absent(tmp_path):
    target = tmp_path / "untouched"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/install_skillpack.py"), "--host", "all",
         "--scope", "repo", "--target-root", str(target), "--dry-run"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert not target.exists()
