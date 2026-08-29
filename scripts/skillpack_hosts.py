"""Host metadata for layered-spec skillpack installation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Scope = Literal["repo", "user"]

SKILL_NAMES = (
    "layered-workflow-planning",
    "spec-first-planning-loop",
    "connected-code-mapping",
    "code-logic-workflow-documentation",
    "user-story-workflow-documentation",
    "design-ux-guardrails",
)

PLANNING_CONTRACT = "planning_contract.md"

# Canonical source paths (posix-style strings used inside skill text).
CANONICAL_PLANNING_CONTRACT = f"planning/{PLANNING_CONTRACT}"
CANONICAL_SKILL_PATHS = tuple(f"skill/{name}/SKILL.md" for name in SKILL_NAMES)


@dataclass(frozen=True)
class HostPaths:
    skills_dir: Path
    planning_dir: Path
    manifest_dir: Path
    skills_ref: str
    planning_ref: str


@dataclass(frozen=True)
class HostConfig:
    name: str
    display_name: str
    keep_user_invocable: bool
    repo: HostPaths
    user: HostPaths


def _repo_paths(skills: str, planning: str, manifest: str) -> HostPaths:
    return HostPaths(
        skills_dir=Path(skills),
        planning_dir=Path(planning),
        manifest_dir=Path(manifest),
        skills_ref=skills,
        planning_ref=planning,
    )


def _user_ref(path: str) -> str:
    if path.startswith("~/"):
        return path
    return f"~/{path}"


def _user_paths(skills: str, planning: str, manifest: str) -> HostPaths:
    home = Path.home()
    return HostPaths(
        skills_dir=home / skills,
        planning_dir=home / planning,
        manifest_dir=home / manifest,
        skills_ref=_user_ref(skills),
        planning_ref=_user_ref(planning),
    )


HOSTS: dict[str, HostConfig] = {
    "vscode": HostConfig(
        name="vscode",
        display_name="VS Code / GitHub Copilot",
        keep_user_invocable=True,
        repo=_repo_paths(
            ".github/skills",
            ".github/planning",
            ".github",
        ),
        user=_user_paths(
            ".copilot/skills",
            ".copilot/planning",
            ".copilot",
        ),
    ),
    "cursor": HostConfig(
        name="cursor",
        display_name="Cursor",
        keep_user_invocable=True,
        repo=_repo_paths(
            ".cursor/skills",
            ".cursor/planning",
            ".cursor",
        ),
        user=_user_paths(
            ".cursor/skills",
            ".cursor/planning",
            ".cursor",
        ),
    ),
    "claude": HostConfig(
        name="claude",
        display_name="Claude Code",
        keep_user_invocable=True,
        repo=_repo_paths(
            ".claude/skills",
            ".claude/planning",
            ".claude",
        ),
        user=_user_paths(
            ".claude/skills",
            ".claude/planning",
            ".claude",
        ),
    ),
    "codex": HostConfig(
        name="codex",
        display_name="OpenAI Codex",
        keep_user_invocable=False,
        repo=_repo_paths(
            ".agents/skills",
            ".agents/planning",
            ".agents",
        ),
        user=_user_paths(
            ".agents/skills",
            ".agents/planning",
            ".agents",
        ),
    ),
    "antigravity": HostConfig(
        name="antigravity",
        display_name="Antigravity",
        keep_user_invocable=False,
        repo=_repo_paths(
            ".agents/skills",
            ".agents/planning",
            ".agents",
        ),
        user=_user_paths(
            ".gemini/config/skills",
            ".gemini/config/planning",
            ".gemini/config",
        ),
    ),
}

ALL_HOST_NAMES = tuple(HOSTS.keys())


def resolve_paths(host: str, scope: Scope, target_root: Path | None = None) -> HostPaths:
    config = HOSTS[host]
    paths = config.repo if scope == "repo" else config.user
    if scope == "repo" and target_root is not None:
        return HostPaths(
            skills_dir=target_root / paths.skills_dir,
            planning_dir=target_root / paths.planning_dir,
            manifest_dir=target_root / paths.manifest_dir,
            skills_ref=paths.skills_ref,
            planning_ref=paths.planning_ref,
        )
    return paths
