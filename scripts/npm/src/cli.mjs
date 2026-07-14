import { access, readFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { HOST_NAMES } from "./hosts.mjs";
import { installHosts } from "./installer.mjs";

const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");

export async function main(argv, environment = {}) {
  const cwd = environment.cwd ?? process.cwd();
  const homeDir = environment.homeDir ?? os.homedir();
  const output = environment.output ?? ((line) => process.stdout.write(`${line}\n`));
  const parsed = parseArguments(argv);
  if (parsed.help) {
    output(helpText());
    return;
  }

  const targetRoot = path.resolve(cwd, parsed.targetRoot ?? ".");
  if (parsed.scope === "repo") await assertDirectory(targetRoot);
  const packageVersion = environment.packageVersion ?? await readPackageVersion();
  const hostNames = parsed.host === "all" ? HOST_NAMES : [parsed.host];
  await installHosts({ ...parsed, hostNames, targetRoot, homeDir, packageRoot, packageVersion, output });
}

function parseArguments(argv) {
  if (argv.length === 0 || argv[0] === "--help" || argv[0] === "-h") return { help: true };
  if (argv[0] !== "init") throw new Error(`Unknown command: ${argv[0]}. Run 'layered-spec --help' for usage.`);

  const result = { command: "init", host: "all", scope: "repo", dryRun: false };
  for (let index = 1; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--help" || argument === "-h") return { help: true };
    if (argument === "--dry-run") {
      result.dryRun = true;
      continue;
    }
    const [option, inlineValue] = argument.split("=", 2);
    if (!["--host", "--scope", "--target-root"].includes(option)) throw new Error(`Unknown option: ${argument}`);
    const value = inlineValue ?? argv[++index];
    if (!value || value.startsWith("--")) throw new Error(`${option} requires a value`);
    if (option === "--host") result.host = value;
    if (option === "--scope") result.scope = value;
    if (option === "--target-root") result.targetRoot = value;
  }
  if (result.host !== "all" && !HOST_NAMES.includes(result.host)) throw new Error(`Unknown host: ${result.host}`);
  if (!["repo", "user"].includes(result.scope)) throw new Error("--scope must be repo or user");
  if (result.scope === "user" && result.targetRoot) throw new Error("--target-root can only be used with --scope repo");
  return result;
}

async function assertDirectory(directory) {
  try {
    await access(directory);
  } catch {
    throw new Error(`Project directory does not exist: ${directory}`);
  }
}

async function readPackageVersion() {
  const packageJson = JSON.parse(await readFile(path.join(packageRoot, "package.json"), "utf8"));
  return packageJson.version;
}

function helpText() {
  return `Usage:\n  layered-spec init [--host <host|all>] [--scope repo|user] [--target-root <path>] [--dry-run]\n\nExamples:\n  layered-spec init\n  layered-spec init --host codex\n  layered-spec init --host all --scope user\n  layered-spec init --host cursor --target-root ../my-project\n\nThe default host is all, the default scope is repo, and the default target is the current directory.`;
}
