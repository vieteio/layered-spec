import { execFileSync } from "node:child_process";
import { mkdir, mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const workspace = await mkdtemp(path.join(os.tmpdir(), "layered-spec-packed-cli-"));
const prefix = path.join(workspace, "global");
const project = path.join(workspace, "project");
const npmCommand = process.platform === "win32" ? process.execPath : "npm";
const npmPrefixArguments = process.platform === "win32"
  ? [path.join(path.dirname(process.execPath), "node_modules", "npm", "bin", "npm-cli.js")]
  : [];
const runNpm = (arguments_, options) => execFileSync(npmCommand, [...npmPrefixArguments, ...arguments_], options);

try {
  const pack = JSON.parse(runNpm(["pack", "--json", "--pack-destination", workspace], { encoding: "utf8" }));
  const tarball = path.join(workspace, pack[0].filename);
  runNpm(["install", "--global", "--prefix", prefix, tarball], { stdio: "inherit" });
  await mkdir(project);
  const executable = process.platform === "win32"
    ? process.execPath
    : path.join(prefix, "bin", "layered-spec");
  const executableArguments = process.platform === "win32"
    ? [path.join(prefix, "node_modules", "@viete-io", "layered-spec", "scripts", "npm", "bin", "layered-spec.mjs")]
    : [];
  execFileSync(executable, [...executableArguments, "init", "--target-root", project, "--dry-run"], { stdio: "inherit" });
} finally {
  await rm(workspace, { recursive: true, force: true });
}
