#!/usr/bin/env python3
"""Install layered-spec skills into IDE/agent-specific directories."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from skillpack_hosts import (
    ALL_HOST_NAMES,
    CANONICAL_PLANNING_CONTRACT,
    CANONICAL_SKILL_PATHS,
    DEFAULT_WORKFLOW,
    HOSTS,
    PLANNING_CONTRACT,
    SKILL_NAMES,
    Scope,
    resolve_paths,
)

MANIFEST_NAME = "layered-spec-skillpack.json"
REQUIRED_FRONTMATTER_KEYS = ("name", "description")
OPTIONAL_FRONTMATTER_KEYS = ("user-invocable", "argument-hint")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def posix_path(path: Path) -> str:
    return path.as_posix()


def git_revision(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def validate_canonical_source(root: Path) -> list[Path]:
    required = [
        root / "planning" / PLANNING_CONTRACT,
        root / "skill" / "spec-first-planning-loop" / "assets" / DEFAULT_WORKFLOW,
    ]
    required.extend(root / "skill" / name / "SKILL.md" for name in SKILL_NAMES)
    missing = [path for path in required if not path.is_file()]
    if missing:
        lines = "\n".join(f"  - {path}" for path in missing)
        raise SystemExit(f"Missing canonical source files:\n{lines}")
    return required


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    if not content.startswith("---"):
        return {}, content

    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", content, re.DOTALL)
    if not match:
        return {}, content

    frontmatter: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        key_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not key_match:
            continue
        key, value = key_match.group(1), key_match.group(2).strip()
        frontmatter[key] = value

    body = content[match.end() :]
    return frontmatter, body


def normalize_frontmatter(frontmatter: dict[str, str], keep_user_invocable: bool) -> dict[str, str]:
    allowed = set(REQUIRED_FRONTMATTER_KEYS)
    if keep_user_invocable:
        allowed.update(OPTIONAL_FRONTMATTER_KEYS)

    normalized: dict[str, str] = {}
    for key in REQUIRED_FRONTMATTER_KEYS:
        if key not in frontmatter:
            raise ValueError(f"Missing required frontmatter field: {key}")
        normalized[key] = frontmatter[key]

    if keep_user_invocable:
        for key in OPTIONAL_FRONTMATTER_KEYS:
            if key in frontmatter:
                normalized[key] = frontmatter[key]

    return normalized


def render_frontmatter(frontmatter: dict[str, str]) -> str:
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def build_rewrite_map(paths) -> list[tuple[str, str]]:
    replacements = [
        (CANONICAL_PLANNING_CONTRACT, f"{paths.planning_ref}/{PLANNING_CONTRACT}"),
    ]
    for skill_path in CANONICAL_SKILL_PATHS:
        skill_name = skill_path.split("/")[1]
        target = f"{paths.skills_ref}/{skill_name}/SKILL.md"
        replacements.append((skill_path, target))
    replacements.sort(key=lambda item: len(item[0]), reverse=True)
    return replacements


def rewrite_content(content: str, replacements: list[tuple[str, str]]) -> str:
    result = content
    for source, target in replacements:
        result = result.replace(source, target)
    return result


CANONICAL_PATH_PATTERNS = [
    re.compile(r"(?<![\w/.-])planning/planning_contract\.md"),
    re.compile(r"(?<![\w/.-])skill/[a-z0-9-]+/SKILL\.md"),
]

NON_VSCODE_PATH_PATTERNS = [
    re.compile(r"(?<![\w/.-])\.github/planning/"),
    re.compile(r"(?<![\w/.-])\.github/skills/"),
]


def validate_installed_skill(content: str, host: str) -> list[str]:
    errors: list[str] = []

    for pattern in CANONICAL_PATH_PATTERNS:
        if pattern.search(content):
            errors.append(f"still contains canonical or stale path: {pattern.pattern}")

    if host != "vscode":
        for pattern in NON_VSCODE_PATH_PATTERNS:
            if pattern.search(content):
                errors.append(f"still contains VS Code-only path: {pattern.pattern}")

    frontmatter, _ = parse_frontmatter(content)
    for key in REQUIRED_FRONTMATTER_KEYS:
        if key not in frontmatter:
            errors.append(f"missing frontmatter field: {key}")

    return errors


def install_host(
    root: Path,
    host: str,
    scope: Scope,
    target_root: Path | None,
    dry_run: bool,
) -> list[Path]:
    config = HOSTS[host]
    paths = resolve_paths(host, scope, target_root)
    replacements = build_rewrite_map(paths)
    written: list[Path] = []

    planning_source = root / "planning" / PLANNING_CONTRACT
    planning_target = paths.planning_dir / PLANNING_CONTRACT

    if not dry_run:
        paths.planning_dir.mkdir(parents=True, exist_ok=True)
        paths.skills_dir.mkdir(parents=True, exist_ok=True)

    planning_text = rewrite_content(planning_source.read_text(encoding="utf-8"), replacements)

    if dry_run:
        print(f"[dry-run] would write {planning_target}")
    else:
        planning_target.parent.mkdir(parents=True, exist_ok=True)
        planning_target.write_text(planning_text, encoding="utf-8", newline="\n")
    written.append(planning_target)

    for skill_name in SKILL_NAMES:
        source = root / "skill" / skill_name / "SKILL.md"
        target = paths.skills_dir / skill_name / "SKILL.md"
        raw = source.read_text(encoding="utf-8")
        rewritten = rewrite_content(raw, replacements)
        frontmatter, body = parse_frontmatter(rewritten)
        normalized = normalize_frontmatter(frontmatter, config.keep_user_invocable)
        output = render_frontmatter(normalized) + "\n" + body.lstrip("\n")

        validation_errors = validate_installed_skill(output, host)
        if validation_errors:
            details = "\n".join(f"  - {error}" for error in validation_errors)
            raise SystemExit(f"Validation failed for {target}:\n{details}")

        if dry_run:
            print(f"[dry-run] would write {target}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(output, encoding="utf-8", newline="\n")
        written.append(target)

    workflow_source = root / "skill" / "spec-first-planning-loop" / "assets" / DEFAULT_WORKFLOW
    workflow_target = paths.skills_dir / "spec-first-planning-loop" / "assets" / DEFAULT_WORKFLOW
    workflow_text = rewrite_content(workflow_source.read_text(encoding="utf-8"), replacements)
    if dry_run:
        print(f"[dry-run] would write {workflow_target}")
    else:
        workflow_target.parent.mkdir(parents=True, exist_ok=True)
        workflow_target.write_text(workflow_text, encoding="utf-8", newline="\n")
    written.append(workflow_target)

    install_root = target_root or root
    if scope == "repo":
        manifest_files = [posix_path(path.relative_to(install_root)) for path in written]
    else:
        manifest_files = [posix_path(path) for path in written]

    manifest = {
        "source_repo": str(root),
        "git_revision": git_revision(root),
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "host": host,
        "scope": scope,
        "files": manifest_files,
    }

    manifest_path = paths.manifest_dir / MANIFEST_NAME
    if dry_run:
        print(f"[dry-run] would write {manifest_path}")
    else:
        paths.manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    written.append(manifest_path)

    label = "Dry run complete" if dry_run else "Installed layered-spec skillpack"
    print(f"{label} for {config.display_name} ({scope} scope)")
    for path in written:
        print(f"  - {path}")

    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install layered-spec skills for an AI host.")
    parser.add_argument(
        "--host",
        required=True,
        choices=[*ALL_HOST_NAMES, "all"],
        help="Target host or 'all'.",
    )
    parser.add_argument(
        "--scope",
        required=True,
        choices=["repo", "user"],
        help="Install into the current repository or the user home directory.",
    )
    parser.add_argument(
        "--target-root",
        type=Path,
        default=None,
        help="Repository root for repo-scoped installs (defaults to layered-spec repo).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be written without creating files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    validate_canonical_source(root)

    hosts = ALL_HOST_NAMES if args.host == "all" else (args.host,)
    target_root = args.target_root.resolve() if args.target_root else (root if args.scope == "repo" else None)

    for host in hosts:
        install_host(root, host, args.scope, target_root, args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
