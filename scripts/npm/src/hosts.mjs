import path from "node:path";

// The Node CLI keeps its host mapping beside the npm entrypoint.

export const SKILL_NAMES = [
  "layered-workflow-planning",
  "spec-first-planning-loop",
  "connected-code-mapping",
  "code-logic-workflow-documentation"
];

export const CORE_REFERENCE_NAMES = [
  "requirements-and-realization.md",
  "invariants.md",
  "skill-pack-versioning.md"
];

const host = (displayName, repo, user) => ({ displayName, repo, user });

export const HOSTS = {
  vscode: host("VS Code / GitHub Copilot", [".github", "skills"], [".copilot", "skills"]),
  cursor: host("Cursor", [".cursor", "skills"], [".cursor", "skills"]),
  claude: host("Claude Code", [".claude", "skills"], [".claude", "skills"]),
  codex: host("OpenAI Codex", [".agents", "skills"], [".agents", "skills"]),
  antigravity: host("Antigravity", [".agents", "skills"], [".gemini", "config", "skills"])
};

export const HOST_NAMES = Object.keys(HOSTS);

export function resolveHostPaths(hostName, scope, { targetRoot, homeDir }) {
  const config = HOSTS[hostName];
  if (!config) throw new Error(`Unknown host: ${hostName}`);

  const skillDirectory = scope === "repo"
    ? path.join(targetRoot, ...config.repo)
    : path.join(homeDir, ...config.user);
  const base = path.dirname(skillDirectory);

  return {
    skillsDirectory: skillDirectory,
    planningDirectory: path.join(base, "planning"),
    manifestDirectory: base,
    skillsReference: toReference(scope, config.repo, config.user),
    planningReference: toReference(scope, replaceLast(config.repo, "planning"), replaceLast(config.user, "planning"))
  };
}

function replaceLast(parts, value) {
  return [...parts.slice(0, -1), value];
}

function toReference(scope, repoParts, userParts) {
  const parts = scope === "repo" ? repoParts : userParts;
  return scope === "repo" ? parts.join("/") : `~/${parts.join("/")}`;
}
