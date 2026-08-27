import { mkdir, readFile, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const PACKAGE_NAME = "@viete-io/layered-spec";
const REGISTRY_URL = `https://registry.npmjs.org/${encodeURIComponent(PACKAGE_NAME)}`;
const UPDATE_CHECK_INTERVAL_MS = 24 * 60 * 60 * 1000;
const UPDATE_CHECK_TIMEOUT_MS = 1_000;
const SEMVER_PATTERN = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$/;

/** Implements Use case 4: tell an init user about a newer matching package channel. */
export async function notifyOfAvailableUpdate({
  packageVersion,
  output = () => {},
  homeDir,
  cachePath,
  fetchFunction = globalThis.fetch,
  now = Date.now()
}) {
  try {
    const resolvedCachePath = cachePath ?? defaultUpdateCheckCachePath({ homeDir });
    const channel = selectUpdateChannel(packageVersion);
    if (!channel) return { channel: null, availableVersion: null, updateAvailable: false };

    const cached = await readCache(resolvedCachePath);
    const availableVersion = isFreshCacheEntry(cached, channel, now)
      ? cached.availableVersion
      : await fetchAndCacheAvailableVersion({ channel, cachePath: resolvedCachePath, fetchFunction, now });
    const updateAvailable = typeof availableVersion === "string" && isVersionNewer(availableVersion, packageVersion);

    if (updateAvailable) {
      output(`Update available: ${availableVersion} (installed: ${packageVersion})\nUpdate with: npm install -g ${PACKAGE_NAME}@${channel}`);
    }
    return { channel, availableVersion: availableVersion ?? null, updateAvailable };
  } catch {
    return { channel: null, availableVersion: null, updateAvailable: false };
  }
}

export function defaultUpdateCheckCachePath({ homeDir = os.homedir(), environment = process.env, platform = process.platform } = {}) {
  const cacheRoot = platform === "win32"
    ? environment.LOCALAPPDATA ?? path.join(homeDir, "AppData", "Local")
    : environment.XDG_CACHE_HOME ?? path.join(homeDir, ".cache");
  return path.join(cacheRoot, "layered-spec", "update-check.json");
}

export function selectUpdateChannel(version) {
  const parsed = parseVersion(version);
  if (!parsed) return null;
  return parsed.prerelease.length === 0 ? "latest" : "next";
}

export function isVersionNewer(availableVersion, installedVersion) {
  const available = parseVersion(availableVersion);
  const installed = parseVersion(installedVersion);
  if (!available || !installed) return false;
  return compareVersions(available, installed) > 0;
}

async function fetchAndCacheAvailableVersion({ channel, cachePath, fetchFunction, now }) {
  if (typeof fetchFunction !== "function") return null;
  const response = await fetchFunction(REGISTRY_URL, { signal: AbortSignal.timeout(UPDATE_CHECK_TIMEOUT_MS) });
  if (!response.ok) return null;

  const metadata = await response.json();
  const availableVersion = metadata?.["dist-tags"]?.[channel];
  if (typeof availableVersion !== "string") return null;

  await writeCache(cachePath, { checkedAt: now, channel, availableVersion });
  return availableVersion;
}

async function readCache(cachePath) {
  try {
    return JSON.parse(await readFile(cachePath, "utf8"));
  } catch {
    return null;
  }
}

async function writeCache(cachePath, cacheEntry) {
  try {
    await mkdir(path.dirname(cachePath), { recursive: true });
    await writeFile(cachePath, `${JSON.stringify(cacheEntry)}\n`, "utf8");
  } catch {
    // An unavailable cache must not affect the completed installation.
  }
}

function isFreshCacheEntry(cacheEntry, channel, now) {
  return cacheEntry?.channel === channel
    && typeof cacheEntry.checkedAt === "number"
    && cacheEntry.checkedAt <= now
    && now - cacheEntry.checkedAt < UPDATE_CHECK_INTERVAL_MS
    && typeof cacheEntry.availableVersion === "string";
}

function parseVersion(version) {
  const match = SEMVER_PATTERN.exec(version);
  if (!match) return null;
  return {
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3]),
    prerelease: match[4]?.split(".") ?? []
  };
}

function compareVersions(left, right) {
  for (const field of ["major", "minor", "patch"]) {
    if (left[field] !== right[field]) return left[field] - right[field];
  }
  if (left.prerelease.length === 0 || right.prerelease.length === 0) {
    if (left.prerelease.length === right.prerelease.length) return 0;
    return left.prerelease.length === 0 ? 1 : -1;
  }

  const identifierCount = Math.max(left.prerelease.length, right.prerelease.length);
  for (let index = 0; index < identifierCount; index += 1) {
    const leftIdentifier = left.prerelease[index];
    const rightIdentifier = right.prerelease[index];
    if (leftIdentifier === undefined) return -1;
    if (rightIdentifier === undefined) return 1;
    if (leftIdentifier === rightIdentifier) continue;

    const leftNumeric = /^\d+$/.test(leftIdentifier);
    const rightNumeric = /^\d+$/.test(rightIdentifier);
    if (leftNumeric && rightNumeric) return Number(leftIdentifier) - Number(rightIdentifier);
    if (leftNumeric) return -1;
    if (rightNumeric) return 1;
    return leftIdentifier < rightIdentifier ? -1 : 1;
  }
  return 0;
}
