import assert from "node:assert/strict";
import { mkdtemp, readFile, stat } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { main } from "../src/cli.mjs";

async function temporaryDirectory(prefix) {
  return mkdtemp(path.join(os.tmpdir(), prefix));
}

test("init writes a Codex project install and versioned manifest", async () => {
  const project = await temporaryDirectory("layered-spec-project-");
  await main(["init", "--host", "codex"], { cwd: project, homeDir: project, packageVersion: "9.9.9", output: () => {} });

  const skill = await readFile(path.join(project, ".agents", "skills", "layered-workflow-planning", "SKILL.md"), "utf8");
  assert.match(skill, /\.agents\/planning\/planning_contract\.md/);
  assert.doesNotMatch(skill, /`planning\/planning_contract\.md`/);

  const manifest = JSON.parse(await readFile(path.join(project, ".agents", "layered-spec-skillpack.json"), "utf8"));
  assert.equal(manifest.package_name, "@viete-io/layered-spec");
  assert.equal(manifest.package_version, "9.9.9");
  assert.equal(manifest.scope, "repo");
  assert.equal(manifest.files.length, 9);
  await stat(path.join(project, ".agents", "skills", "spec-first-planning-loop", "assets", "default_workflow.md"));
  await assert.rejects(stat(path.join(project, ".agents", "prompts")), { code: "ENOENT" });
  await stat(path.join(project, ".agents", "skills", "user-story-workflow-documentation", "SKILL.md"));
  await stat(path.join(project, ".agents", "skills", "design-ux-guardrails", "references", "design-system-sync.md"));
});

test("init defaults to all hosts in repo scope and combines shared configuration paths", async () => {
  const project = await temporaryDirectory("layered-spec-default-");
  await main(["init"], { cwd: project, homeDir: project, packageVersion: "9.9.9", output: () => {} });

  await Promise.all([
    stat(path.join(project, ".github", "skills", "layered-workflow-planning", "SKILL.md")),
    stat(path.join(project, ".cursor", "skills", "layered-workflow-planning", "SKILL.md")),
    stat(path.join(project, ".claude", "skills", "layered-workflow-planning", "SKILL.md")),
    stat(path.join(project, ".agents", "skills", "layered-workflow-planning", "SKILL.md"))
  ]);
  const agentsManifest = JSON.parse(await readFile(path.join(project, ".agents", "layered-spec-skillpack.json"), "utf8"));
  assert.deepEqual(agentsManifest.hosts, ["codex", "antigravity"]);
});

test("init supports all hosts in user scope", async () => {
  const home = await temporaryDirectory("layered-spec-home-");
  await main(["init", "--host", "all", "--scope", "user"], { cwd: home, homeDir: home, packageVersion: "9.9.9", output: () => {} });

  await Promise.all([
    stat(path.join(home, ".copilot", "skills", "layered-workflow-planning", "SKILL.md")),
    stat(path.join(home, ".cursor", "skills", "layered-workflow-planning", "SKILL.md")),
    stat(path.join(home, ".claude", "skills", "layered-workflow-planning", "SKILL.md")),
    stat(path.join(home, ".agents", "skills", "layered-workflow-planning", "SKILL.md")),
    stat(path.join(home, ".gemini", "config", "skills", "layered-workflow-planning", "SKILL.md"))
  ]);
});

test("dry run creates no project files", async () => {
  const project = await temporaryDirectory("layered-spec-dry-run-");
  const output = [];
  await main(["init", "--host", "cursor", "--dry-run"], { cwd: project, homeDir: project, output: (line) => output.push(line) });

  await assert.rejects(stat(path.join(project, ".cursor")));
  assert.ok(output.some((line) => line.includes("would write")));
});

test("rejects unsafe or incomplete input before writes", async () => {
  const project = await temporaryDirectory("layered-spec-invalid-");
  await assert.rejects(main(["init", "--host", "unknown"], { cwd: project, homeDir: project, output: () => {} }), /Unknown host/);
  await assert.rejects(main(["init", "--host", "cursor", "--scope", "user", "--target-root", project], { cwd: project, homeDir: project, output: () => {} }), /only be used/);
});
