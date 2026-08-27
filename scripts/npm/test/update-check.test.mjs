import assert from "node:assert/strict";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { defaultUpdateCheckCachePath, isVersionNewer, notifyOfAvailableUpdate, selectUpdateChannel } from "../src/update-check.mjs";

async function temporaryCachePath() {
  const directory = await mkdtemp(path.join(os.tmpdir(), "layered-spec-update-check-"));
  return path.join(directory, "update-check.json");
}

test("stable installation reports a newer latest release and caches it", async () => {
  const cachePath = await temporaryCachePath();
  const output = [];
  const requests = [];
  const result = await notifyOfAvailableUpdate({
    packageVersion: "0.2.0",
    cachePath,
    now: 1_000,
    output: (line) => output.push(line),
    fetchFunction: async (url) => {
      requests.push(url);
      return { ok: true, json: async () => ({ "dist-tags": { latest: "0.2.1", next: "0.3.0-alpha.1" } }) };
    }
  });

  assert.equal(result.channel, "latest");
  assert.equal(result.updateAvailable, true);
  assert.deepEqual(output, ["Update available: 0.2.1 (installed: 0.2.0)\nUpdate with: npm install -g @viete-io/layered-spec@latest"]);
  assert.equal(requests.length, 1);
  assert.deepEqual(JSON.parse(await readFile(cachePath, "utf8")), { checkedAt: 1_000, channel: "latest", availableVersion: "0.2.1" });
});

test("prerelease installation checks only next", async () => {
  const output = [];
  const result = await notifyOfAvailableUpdate({
    packageVersion: "0.3.0-alpha.1",
    cachePath: await temporaryCachePath(),
    output: (line) => output.push(line),
    fetchFunction: async () => ({ ok: true, json: async () => ({ "dist-tags": { latest: "0.3.0", next: "0.3.0-alpha.2" } }) })
  });

  assert.equal(result.channel, "next");
  assert.deepEqual(output, ["Update available: 0.3.0-alpha.2 (installed: 0.3.0-alpha.1)\nUpdate with: npm install -g @viete-io/layered-spec@next"]);
});

test("fresh cache is reused without a registry request", async () => {
  const cachePath = await temporaryCachePath();
  await writeFile(cachePath, JSON.stringify({ checkedAt: 1_000, channel: "latest", availableVersion: "0.2.1" }), "utf8");
  const output = [];
  const result = await notifyOfAvailableUpdate({
    packageVersion: "0.2.0",
    cachePath,
    now: 1_001,
    output: (line) => output.push(line),
    fetchFunction: async () => { throw new Error("registry should not be called"); }
  });

  assert.equal(result.updateAvailable, true);
  assert.equal(output.length, 1);
});

test("registry failures and malformed versions do not produce notices", async () => {
  const output = [];
  const result = await notifyOfAvailableUpdate({
    packageVersion: "0.2.0",
    cachePath: await temporaryCachePath(),
    output: (line) => output.push(line),
    fetchFunction: async () => { throw new Error("offline"); }
  });

  assert.equal(result.updateAvailable, false);
  assert.deepEqual(output, []);
  assert.equal(selectUpdateChannel("not-a-version"), null);
  assert.equal(isVersionNewer("0.3.0-alpha.10", "0.3.0-alpha.2"), true);
});

test("cache path follows the operating system cache directory", () => {
  assert.equal(
    defaultUpdateCheckCachePath({ homeDir: "/home/test", environment: { XDG_CACHE_HOME: "/cache" }, platform: "linux" }),
    path.join("/cache", "layered-spec", "update-check.json")
  );
  assert.equal(
    defaultUpdateCheckCachePath({ homeDir: "C:\\Users\\test", environment: { LOCALAPPDATA: "C:\\Cache" }, platform: "win32" }),
    path.join("C:\\Cache", "layered-spec", "update-check.json")
  );
});
