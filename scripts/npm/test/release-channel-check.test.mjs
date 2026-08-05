import assert from "node:assert/strict";
import test from "node:test";
import { main, validateReleaseChannel } from "../release-channel-check.mjs";

test("accepts a stable release only for latest", () => {
  assert.deepEqual(validateReleaseChannel({ version: "0.2.0", tag: "latest" }), {
    version: "0.2.0",
    tag: "latest",
    prerelease: false
  });
  assert.throws(
    () => validateReleaseChannel({ version: "0.2.0", tag: "next" }),
    /must be published with --tag latest/
  );
});

test("accepts a prerelease only for next", () => {
  assert.deepEqual(validateReleaseChannel({ version: "0.2.0-alpha.0", tag: "next" }), {
    version: "0.2.0-alpha.0",
    tag: "next",
    prerelease: true
  });
  assert.throws(
    () => validateReleaseChannel({ version: "0.2.0-alpha.0", tag: "latest" }),
    /must be published with --tag next/
  );
});

test("auto selects the channel that matches the package version", async () => {
  const output = [];
  const release = await main(["--tag", "auto"], {
    version: "0.2.0-alpha.0",
    output: (line) => output.push(line)
  });

  assert.equal(release.tag, "next");
  assert.deepEqual(output, ["Release channel valid: 0.2.0-alpha.0 -> next"]);
});

test("rejects malformed versions and unsupported tags", () => {
  assert.throws(
    () => validateReleaseChannel({ version: "0.2-alpha", tag: "next" }),
    /complete SemVer/
  );
  assert.throws(
    () => validateReleaseChannel({ version: "0.2.0", tag: "beta" }),
    /release tag must be latest, next, or auto/
  );
});
