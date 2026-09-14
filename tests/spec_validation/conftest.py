from pathlib import Path
import sys

import pytest

SCRIPTS_ROOT = Path(__file__).resolve().parents[2] / "skill/layered-spec-core/scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))


@pytest.fixture(autouse=True)
def no_external_telemetry(monkeypatch):
    # Tests are isolated from telemetry; the CLI accepts an explicitly selected .env.
    monkeypatch.setenv("LOGFIRE_TOKEN", "")
