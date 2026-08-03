import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { HOSTS, SKILL_NAMES, resolveHostPaths } from "./hosts.mjs";

const MANIFEST_NAME = "layered-spec-skillpack.json";
const SOURCE_REPOSITORY = "https://github.com/vieteio/layered-spec";
const canonicalPathPatterns = [
  /(?<![\w/.-])planning\/planning_contract\.md/,
  /(?<![\w/.-])prompts\/plan implementation in a loop\.prompt\.md/,
  /(?<![\w/.-])skill\/[a-z0-9-]+\/SKILL\.md/
];

export async function installHosts({
  hostNames,
  scope,
  targetRoot,
  homeDir,
  packageRoot,
  packageVersion,
  dryRun,
  output = () => {}
}) {
  const sources = await loadCanonicalSources(packageRoot);
  const pathsByHost = hostNames.map((hostName) => ({
    hostName,
    paths: resolveHostPaths(hostName, scope, { targetRoot, homeDir })
  }));
  const installationGroups = groupCompatibleHosts(pathsByHost);

  for (const { hostNames: groupedHostNames, paths } of installationGroups) {
    await installHost({ hostNames: groupedHostNames, paths, scope, targetRoot, sources, packageVersion, dryRun, output });
  }
}

/** Implements Use case 1: install the selected host's skillpack into its target directory. */
async function installHost({ hostNames, paths, scope, targetRoot, sources, packageVersion, dryRun, output }) {
  const hostName = hostNames[0];
  const replacements = buildRewriteMap(paths);
  const writes = [
    [path.join(paths.planningDirectory, "planning_contract.md"), rewriteContent(sources.planning, replacements)],
    [path.join(paths.promptsDirectory, "plan implementation in a loop.prompt.md"), rewriteContent(sources.prompt, replacements)]
  ];

  for (const skillName of SKILL_NAMES) {
    for (const [relativePath, source] of sources.skills.get(skillName)) {
      const rewritten = rewriteContent(source, replacements);
      const output = relativePath === "SKILL.md"
        ? normalizeSkillFrontmatter(rewritten, hostName)
        : rewritten;
      if (relativePath === "SKILL.md") validateInstalledSkill(output, hostName);
      writes.push([path.join(paths.skillsDirectory, skillName, ...relativePath.split("/")), output]);
    }
  }

  const allFiles = writes.map(([file]) => file);
  const manifest = {
    source_repo: SOURCE_REPOSITORY,
    package_name: "@viete-io/layered-spec",
    package_version: packageVersion,
    installed_at: new Date().toISOString(),
    host: hostName,
    hosts: hostNames,
    scope,
    files: scope === "repo"
      ? allFiles.map((file) => toPosix(path.relative(targetRoot, file)))
      : allFiles.map(toPosix)
  };
  writes.push([path.join(paths.manifestDirectory, MANIFEST_NAME), `${JSON.stringify(manifest, null, 2)}\n`]);

  for (const [file, content] of writes) {
    if (dryRun) {
      output(`[dry-run] would write ${file}`);
    } else {
      await mkdir(path.dirname(file), { recursive: true });
      await writeFile(file, content, "utf8");
    }
  }

  const hostLabels = hostNames.map((name) => HOSTS[name].displayName).join(", ");
  output(`${dryRun ? "Dry run complete" : "Installed layered-spec skillpack"} for ${hostLabels} (${scope} scope)`);
}

async function loadCanonicalSources(packageRoot) {
  const sourcePath = (...parts) => path.join(packageRoot, ...parts);
  const planning = await readRequired(sourcePath("planning", "planning_contract.md"));
  const prompt = await readRequired(sourcePath("prompts", "plan implementation in a loop.prompt.md"));
  const skills = new Map();
  for (const skillName of SKILL_NAMES) {
    skills.set(skillName, await readSkillFiles(sourcePath("skill", skillName)));
  }
  return { planning, prompt, skills };
}

async function readSkillFiles(directory, relativeDirectory = "") {
  let entries;
  try {
    entries = await readdir(directory, { withFileTypes: true });
  } catch (error) {
    if (error.code === "ENOENT") throw new Error(`Missing canonical skill directory: ${directory}`);
    throw error;
  }

  const files = new Map();
  for (const entry of entries) {
    const relativePath = relativeDirectory ? `${relativeDirectory}/${entry.name}` : entry.name;
    const absolutePath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      const nestedFiles = await readSkillFiles(absolutePath, relativePath);
      for (const [nestedPath, content] of nestedFiles) files.set(nestedPath, content);
    } else if (entry.isFile()) {
      files.set(relativePath, await readRequired(absolutePath));
    }
  }
  if (!relativeDirectory && !files.has("SKILL.md")) {
    throw new Error(`Missing canonical skill file: ${path.join(directory, "SKILL.md")}`);
  }
  return files;
}

async function readRequired(file) {
  try {
    return await readFile(file, "utf8");
  } catch (error) {
    if (error.code === "ENOENT") throw new Error(`Missing canonical source file: ${file}`);
    throw error;
  }
}

function buildRewriteMap(paths) {
  const replacements = [
    ["planning/planning_contract.md", `${paths.planningReference}/planning_contract.md`],
    ["prompts/plan implementation in a loop.prompt.md", `${paths.promptsReference}/plan implementation in a loop.prompt.md`],
    ...SKILL_NAMES.map((name) => [`skill/${name}/SKILL.md`, `${paths.skillsReference}/${name}/SKILL.md`])
  ];
  return replacements.sort(([left], [right]) => right.length - left.length);
}

function rewriteContent(content, replacements) {
  return replacements.reduce((result, [source, target]) => result.split(source).join(target), content);
}

function normalizeSkillFrontmatter(content, hostName) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (!match) throw new Error(`Skill source has no valid frontmatter for ${hostName}`);

  const fields = new Map();
  for (const line of match[1].split(/\r?\n/)) {
    const field = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (field) fields.set(field[1], field[2]);
  }
  for (const required of ["name", "description"]) {
    if (!fields.has(required)) throw new Error(`Skill frontmatter is missing ${required}`);
  }

  const keepUserInvocable = hostName === "vscode" || hostName === "cursor" || hostName === "claude";
  const keys = keepUserInvocable
    ? ["name", "description", "user-invocable", "argument-hint"]
    : ["name", "description"];
  const frontmatter = ["---", ...keys.filter((key) => fields.has(key)).map((key) => `${key}: ${fields.get(key)}`), "---"].join("\n");
  return `${frontmatter}\n${content.slice(match[0].length).replace(/^\n+/, "")}`;
}

function validateInstalledSkill(content, hostName) {
  const errors = canonicalPathPatterns.filter((pattern) => pattern.test(content)).map((pattern) => `still contains canonical path: ${pattern}`);
  if (hostName !== "vscode" && /(?<![\w/.-])\.github\/(planning|prompts|skills)\//.test(content)) {
    errors.push("still contains VS Code-only .github reference");
  }
  if (!/^---\nname: .+\ndescription: .+/m.test(content)) errors.push("missing required frontmatter");
  if (errors.length) throw new Error(`Installed skill validation failed:\n${errors.map((error) => `  - ${error}`).join("\n")}`);
}

function groupCompatibleHosts(pathsByHost) {
  const groups = new Map();
  for (const { hostName, paths } of pathsByHost) {
    const key = [paths.skillsDirectory, paths.planningDirectory, paths.promptsDirectory, paths.manifestDirectory].join("\0");
    const group = groups.get(key);
    if (group) {
      group.hostNames.push(hostName);
    } else {
      groups.set(key, { hostNames: [hostName], paths });
    }
  }
  return [...groups.values()];
}

function toPosix(value) {
  return value.split(path.sep).join("/");
}
