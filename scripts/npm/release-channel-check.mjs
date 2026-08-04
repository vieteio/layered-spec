import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const SEMVER_PATTERN = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$/;
const CHANNELS = new Set(["latest", "next", "auto"]);

export function validateReleaseChannel({ version, tag }) {
  const match = SEMVER_PATTERN.exec(version);
  if (!match) {
    throw new Error(`package version must be complete SemVer (for example 0.2.0 or 0.2.0-alpha.0): ${version}`);
  }
  if (!CHANNELS.has(tag)) {
    throw new Error(`release tag must be latest, next, or auto: ${tag}`);
  }

  const prerelease = match[4] !== undefined;
  const resolvedTag = tag === "auto" ? (prerelease ? "next" : "latest") : tag;
  if (prerelease && resolvedTag !== "next") {
    throw new Error(`prerelease ${version} must be published with --tag next, not --tag ${resolvedTag}`);
  }
  if (!prerelease && resolvedTag !== "latest") {
    throw new Error(`stable release ${version} must be published with --tag latest, not --tag ${resolvedTag}`);
  }
  return { version, tag: resolvedTag, prerelease };
}

export async function main(argv, environment = {}) {
  const version = environment.version ?? await readPackageVersion(environment.packageRoot ?? packageRoot);
  const tag = parseTag(argv, environment.npmConfigTag ?? process.env.npm_config_tag);
  const release = validateReleaseChannel({ version, tag });
  (environment.output ?? ((line) => process.stdout.write(`${line}\n`)))(`Release channel valid: ${release.version} -> ${release.tag}`);
  return release;
}

function parseTag(argv, npmConfigTag) {
  if (argv.length > 2 || (argv.length === 2 && argv[0] !== "--tag")) {
    throw new Error("Usage: node scripts/npm/release-channel-check.mjs [--tag latest|next|auto]");
  }
  return argv[0] === "--tag" ? argv[1] : (npmConfigTag ?? "latest");
}

async function readPackageVersion(root) {
  const packageJson = JSON.parse(await readFile(path.join(root, "package.json"), "utf8"));
  return packageJson.version;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2)).catch((error) => {
    process.stderr.write(`layered-spec release check: ${error.message}\n`);
    process.exitCode = 1;
  });
}
