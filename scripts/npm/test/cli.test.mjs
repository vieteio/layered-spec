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
  await main(["init", "--host", "codex"], { cwd: project, homeDir: project, packageVersion: "9.9.9", output: () => {}, updateChecker: () => {} });

  const skill = await readFile(path.join(project, ".agents", "skills", "layered-workflow-planning", "SKILL.md"), "utf8");
  assert.match(skill, /\.agents\/planning\/planning_contract\.md/);
  assert.match(skill, /metadata:\n  version: "0\.2\.2"/);
  assert.match(skill, /Requirements And Realization Rule/);
  assert.match(skill, /Invariants Layer Rule/);
  assert.match(skill, /\.agents\/skills\/layered-spec-core\/references\/skill-pack-versioning\.md/);
  assert.doesNotMatch(skill, /`planning\/planning_contract\.md`/);

  const planningContract = await readFile(path.join(project, ".agents", "planning", "planning_contract.md"), "utf8");
  assert.match(planningContract, /Requirements And Implementation Structure/);
  assert.match(planningContract, /Invariants Layer Syntax/);
  assert.match(planningContract, /\.agents\/skills\/layered-spec-core\/references\/requirements-and-realization\.md/);
  assert.doesNotMatch(planningContract, /skill\/layered-spec-core\/references/);
  assert.doesNotMatch(planningContract, /user stor|solution basis|basis selection|UX layer/i);

  const requirementsReference = await readFile(path.join(project, ".agents", "skills", "layered-spec-core", "references", "requirements-and-realization.md"), "utf8");
  const invariantsReference = await readFile(path.join(project, ".agents", "skills", "layered-spec-core", "references", "invariants.md"), "utf8");
  const versioningReference = await readFile(path.join(project, ".agents", "skills", "layered-spec-core", "references", "skill-pack-versioning.md"), "utf8");
  assert.match(requirementsReference, /Declarative And Implementation Use Cases/);
  assert.match(invariantsReference, /Invariants:\n- Outline:/);
  assert.match(versioningReference, /Last edited with skill pack/);
  assert.doesNotMatch(`${requirementsReference}\n${invariantsReference}`, /user stor|solution basis|basis selection|UX layer/i);

  const lifecycleSkill = await readFile(path.join(project, ".agents", "skills", "spec-first-planning-loop", "SKILL.md"), "utf8");
  assert.match(lifecycleSkill, /specs\/spec-lifecycle\/workflow\.md/);
  assert.doesNotMatch(lifecycleSkill, /user stor|solution basis|basis selection/i);

  const workflowTemplate = await readFile(path.join(project, ".agents", "skills", "spec-first-planning-loop", "assets", "default_workflow.md"), "utf8");
  assert.match(workflowTemplate, /Default workflow version: `0\.2\.2`/);
  assert.match(workflowTemplate, /Check specification completeness/);
  assert.match(workflowTemplate, /Check specification consistency/);
  assert.doesNotMatch(workflowTemplate, /user stor|solution basis|basis selection/i);

  const manifest = JSON.parse(await readFile(path.join(project, ".agents", "layered-spec-skillpack.json"), "utf8"));
  assert.equal(manifest.package_name, "@viete-io/layered-spec");
  assert.equal(manifest.package_version, "9.9.9");
  assert.equal(manifest.scope, "repo");
  assert.equal(manifest.files.length, 9);
});

test("init defaults to all hosts in repo scope and combines shared configuration paths", async () => {
  const project = await temporaryDirectory("layered-spec-default-");
  await main(["init"], { cwd: project, homeDir: project, packageVersion: "9.9.9", output: () => {}, updateChecker: () => {} });

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
  await main(["init", "--host", "all", "--scope", "user"], { cwd: home, homeDir: home, packageVersion: "9.9.9", output: () => {}, updateChecker: () => {} });

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
  await main(["init", "--host", "cursor", "--dry-run"], { cwd: project, homeDir: project, output: (line) => output.push(line), updateChecker: () => { throw new Error("dry runs must skip update checks"); } });

  await assert.rejects(stat(path.join(project, ".cursor")));
  assert.ok(output.some((line) => line.includes("would write")));
});

test("rejects unsafe or incomplete input before writes", async () => {
  const project = await temporaryDirectory("layered-spec-invalid-");
  await assert.rejects(main(["init", "--host", "unknown"], { cwd: project, homeDir: project, output: () => {}, updateChecker: () => {} }), /Unknown host/);
  await assert.rejects(main(["init", "--host", "cursor", "--scope", "user", "--target-root", project], { cwd: project, homeDir: project, output: () => {}, updateChecker: () => {} }), /only be used/);
});

test("checks for updates after installation unless explicitly disabled", async () => {
  const project = await temporaryDirectory("layered-spec-update-check-");
  const checks = [];
  const updateChecker = async (options) => checks.push(options);

  await main(["init", "--host", "codex"], { cwd: project, homeDir: project, packageVersion: "9.9.9", output: () => {}, updateChecker });
  assert.equal(checks.length, 1);
  assert.equal(checks[0].packageVersion, "9.9.9");
  assert.equal(checks[0].homeDir, project);

  await main(["init", "--host", "codex", "--no-update-check"], { cwd: project, homeDir: project, packageVersion: "9.9.9", output: () => {}, updateChecker });
  assert.equal(checks.length, 1);
});
