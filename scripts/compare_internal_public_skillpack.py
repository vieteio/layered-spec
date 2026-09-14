#!/usr/bin/env python3
"""Generate an exact unified diff between internal and public skill-pack files."""

from __future__ import annotations

import argparse
import difflib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FilePair:
    label: str
    internal_path: str
    public_path: str


FILE_PAIRS = (
    FilePair(
        "planning contract",
        ".agents/skills/layered-spec-core/references/planning_contract.md",
        "planning/planning_contract.md",
    ),
    FilePair(
        "requirements and realization",
        ".agents/skills/layered-spec-core/references/requirements-and-realization.md",
        "skill/layered-spec-core/references/requirements-and-realization.md",
    ),
    FilePair(
        "invariants",
        ".agents/skills/layered-spec-core/references/invariants.md",
        "skill/layered-spec-core/references/invariants.md",
    ),
    FilePair(
        "skill-pack versioning",
        ".agents/skills/layered-spec-core/references/skill-pack-versioning.md",
        "skill/layered-spec-core/references/skill-pack-versioning.md",
    ),
    FilePair(
        "layered workflow planning skill",
        ".agents/skills/layered-workflow-planning/SKILL.md",
        "skill/layered-workflow-planning/SKILL.md",
    ),
    FilePair(
        "code logic workflow documentation skill",
        ".agents/skills/code-logic-workflow-documentation/SKILL.md",
        "skill/code-logic-workflow-documentation/SKILL.md",
    ),
    FilePair(
        "connected code mapping skill",
        ".agents/skills/connected-code-mapping/SKILL.md",
        "skill/connected-code-mapping/SKILL.md",
    ),
    FilePair(
        "spec-first planning loop skill",
        ".agents/skills/spec-first-planning-loop/SKILL.md",
        "skill/spec-first-planning-loop/SKILL.md",
    ),
    FilePair(
        "default workflow",
        ".agents/skills/spec-first-planning-loop/assets/default_workflow.md",
        "skill/spec-first-planning-loop/assets/default_workflow.md",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("internal_root", type=Path)
    parser.add_argument("public_root", type=Path)
    parser.add_argument("output", type=Path)
    return parser.parse_args()


def read_lines(path: Path) -> list[str]:
    if not path.is_file():
        raise FileNotFoundError(f"Corresponding file does not exist: {path}")
    return path.read_text(encoding="utf-8").splitlines()


def create_report(internal_root: Path, public_root: Path) -> tuple[str, int]:
    report_lines = [
        "# Exact internal-to-public skill-pack diff",
        "# Line endings are normalized; wording and whitespace inside lines are unchanged.",
        f"# Internal root: {internal_root.resolve()}",
        f"# Public root: {public_root.resolve()}",
        "",
    ]
    changed_pairs = 0

    for pair in FILE_PAIRS:
        internal_file = internal_root / pair.internal_path
        public_file = public_root / pair.public_path
        pair_diff = list(
            difflib.unified_diff(
                read_lines(internal_file),
                read_lines(public_file),
                fromfile=f"internal/{pair.internal_path}",
                tofile=f"public/{pair.public_path}",
                lineterm="",
            )
        )

        report_lines.extend((f"# ===== {pair.label} =====", ""))
        if pair_diff:
            changed_pairs += 1
            report_lines.extend(pair_diff)
        else:
            report_lines.append("# No differences")
        report_lines.append("")

    return "\n".join(report_lines) + "\n", changed_pairs


def main() -> int:
    args = parse_args()
    report, changed_pairs = create_report(args.internal_root, args.public_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8", newline="\n")
    print(f"Compared {len(FILE_PAIRS)} file pairs; {changed_pairs} contain differences.")
    print(f"Wrote {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
