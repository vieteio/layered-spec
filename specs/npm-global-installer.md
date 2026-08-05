# Title and scope

Distribute layered-spec as `@viete-io/layered-spec` so a user can install the CLI with `npm install -g @viete-io/layered-spec@latest`, enter a project, and run `layered-spec init` without cloning this repository. `init` defaults to all supported hosts in the current project, while `--host <host>` remains available for a one-host installation.

Package selection happens at npm installation time: an unqualified install and `@latest` select the newest stable release, `@next` selects the newest prerelease, and an exact SemVer version selects a pinned release. The CLI installs only the canonical assets embedded in its resolved package version; it must not download and execute a different version at `init` time.

## Planning anchor

- Anchor: `scripts/install_skillpack.py#main` is the only current installation entry point. It depends on a checked-out repository for the canonical `skill/`, `planning/`, and `prompts/` source files and requires a Python runtime.
- Changed assumption: distribution is no longer a cloned Python repository; the published npm tarball is the immutable source bundle and the Node CLI is the supported public entry point.
- Version-selection anchor: `package.json#version` is being prepared as `0.2.0-alpha.1` from the six-skill `user-stories` branch. npm currently maps `latest` to `0.1.1`; the prior four-skill `0.2.0-alpha.0` package was unpublished and must not be reused.
- Changed release rule: stable and prerelease packages are separately published and selected through npm dist-tags. A prerelease must never move `latest`.
- Why this is non-local: the change affects source layout, install runtime, CLI compatibility, package contents, documentation, release credentials, CI, and end-to-end tests on every supported host/path combination.
- Impacted specs already present in `specs/`:
  - `specs/construction-drawing-pdf-estimation-service.md` — unrelated demo-project plan. Status: `active`. Action: `reuse` unchanged.
  - `specs/task_draft_verification_assembled_vietejson_policy_files.md` — unrelated workspace plan. Status: `active`. Action: `reuse` unchanged.
  - No existing spec describes skillpack package distribution. This file is the authoritative plan for the npm installer.

## Connected groups or observed existing logic

### 1. Entry and orchestration

- `scripts/install_skillpack.py#parse_args` owns the public options: required `--host`, required `--scope`, optional `--target-root`, and `--dry-run`.
- `scripts/install_skillpack.py#main` validates the canonical source, expands `--host all`, resolves the target root, and calls the host installer once per selected host.
- `scripts/skillpack_hosts.py#HOSTS` is the single registry of five supported hosts and their repository/user paths.

### 2. Canonical source and transformation

- Canonical artifacts are `skill/*/SKILL.md`, `planning/planning_contract.md`, and `prompts/plan implementation in a loop.prompt.md`.
- `validate_canonical_source`, `build_rewrite_map`, `rewrite_content`, `normalize_frontmatter`, and `validate_installed_skill` enforce source existence, rewrite host-local references, preserve allowed frontmatter, and reject stale paths.
- The package must include exactly these canonical assets; the npm `files` allowlist must exclude examples, generated installations, local agent state, and repository-only documents by default.

### 3. Filesystem output and compatibility

- `install_host` writes planning guidance, loop prompt, one `SKILL.md` per skill, and `layered-spec-skillpack.json` into host-specific directories.
- The manifest records `source_repo`, `git_revision`, timestamp, host, scope, and installed files. Under npm distribution, `source_repo` should become the public repository URL and the manifest needs a `package_name` and `package_version` to identify the installed release.
- Repo scope is intentionally caller-selected through `--target-root`; user scope resolves from the current user's home directory.

### 4. Documentation and publishing

- `README.md` currently advertises Python commands only.
- The repository has no root `package.json`, lockfile, test runner, npm publishing configuration, or GitHub Actions workflow.
- The comparable OpenSpec quick start separates global package installation from project initialization; it documents Node 20.19+ as a runtime requirement and calls a CLI command after `npm install -g`. [OpenSpec quick start](https://github.com/Fission-AI/OpenSpec#quick-start)

### 5. Validation

- There are no automated tests for the installer today.
- The Python installer has a side-effect-free `--dry-run` path that can become a fixture-based contract test baseline before it is retired.

### 6. Release channel and package selection

- `package.json` currently exposes one package version; `scripts/npm/src/cli.mjs#readPackageVersion` writes that resolved version into the installation manifest.
- npm already resolves package versions before the CLI executes. Adding a version prompt to `init` would require downloading, unpacking, and trusting a second package version at runtime, while the installed executable and manifest could then disagree about their source version.
- The supported selection surface should therefore be npm's native specifier syntax:
  - `npm install -g @viete-io/layered-spec` or `@latest` for the newest stable release.
  - `npm install -g @viete-io/layered-spec@next` for the newest prerelease.
  - `npm install -g @viete-io/layered-spec@<exact-version>` for a reproducible pinned release.
- The existing `v0.2-alpha` Git tag is a repository milestone. The corrected npm prerelease uses the complete SemVer version `0.2.0-alpha.1` and receives the matching Git tag `v0.2.0-alpha.1`.

## Use cases

### 1. Install layered-spec skills into the user configuration

project working directory --`layered-spec init --host <host|all>`--> host-specific skills, planning contract, prompt, and versioned manifest in that project

Input Validation And Contracts:

- Validate `host` against the central host registry before any write.
- `init` defaults to `--scope repo` and `--target-root .`; accept `--scope user` for a user-wide install and retain explicit `--target-root` for scripts.
- After validation, each install operation receives a normalized host name, scope, absolute target root where applicable, and package metadata; individual write steps do not re-parse CLI input.

Execution Logic:

1. Resolve package-root canonical assets rather than a cloned repository root.
2. Load host path metadata, rewrite internal links for that host, validate the rewritten skill content, and create target parent directories.
3. Write all artifacts with UTF-8 and normalized LF line endings, then write a manifest containing package provenance.
4. Print the selected host, scope, and concrete output paths.

Files And Functions:

- planned: `package.json` — scoped package metadata, `bin` mapping, Node engine, `files` allowlist, scripts, and publish configuration.
- implemented: `scripts/npm/bin/layered-spec.mjs` — public executable that dispatches `init` and `--help`.
- implemented: `scripts/npm/src/cli.mjs#main` — parse and validate command input.
- implemented: `scripts/npm/src/installer.mjs#installHost` — implement the workflow above; its docstring links it to Use case 1.
- implemented: `scripts/npm/src/hosts.mjs#HOSTS` — canonical host metadata ported from `scripts/skillpack_hosts.py`.
- existing: `skill/`, `planning/`, `prompts/` — package-owned canonical source assets.

Tests:

`scripts/npm/test/cli.test.mjs`
 - description: installs one host in user scope into a temporary home directory
   input: `layered-spec init --host cursor --scope user` with a temporary home override
   workflow: valid command --write rewritten artifacts and manifest--> expected host-local output tree
   expected outcome: every canonical asset is installed, references are host-local, and the manifest contains package name and package version.
 - description: expands `--host all`
   input: all hosts in a temporary home directory
   workflow: all-host request --install each configured host--> five independent output trees
   expected outcome: every registry host receives only its declared paths.

### 1.1 Preview or reject unsafe installation input

CLI options --validate or dry-run--> no writes for invalid input; exact planned writes for `--dry-run`

Execution Logic:

1. Reject unknown hosts, missing scope, a repo scope lacking a valid target root, and attempts to install into a path that cannot be resolved.
2. For `--dry-run`, run the same source validation and target-path calculation as a real installation but perform no filesystem mutation.
3. Preserve non-zero exit codes and useful errors so shell scripts and CI can depend on the result.

Tests:

`scripts/npm/test/cli.test.mjs`
 - description: rejects invalid command input before files are created
   input: unknown host or invalid repo target
   workflow: invalid CLI input --validate--> failed command
   expected outcome: non-zero exit and no temporary output files.
 - description: previews a valid install without writes
   input: `--dry-run` for each distinct path policy
   workflow: valid dry run --calculate output paths--> printed plan
   expected outcome: no installed paths exist and output names every planned artifact.

### 2. Preserve existing repository consumers during the migration

existing Python command --six-month migration window--> documented npm CLI, with no silent divergent installer behavior

Implementation Logic:

- Port the Python behavior into Node modules with only Node built-ins (`node:fs`, `node:path`, `node:os`, `node:process`, `node:child_process`) so global install has no production dependency tree.
- Build table-driven tests from the `HOSTS` registry and fixtures that assert the same target paths, rewritten references, frontmatter policy, manifest file list, and dry-run output semantics as the Python installer.
- Do not make `postinstall` mutate a user's host configuration: global package installation should provide the `layered-spec` command, and explicit `init` performs the user-visible write in the current project. This follows the install-then-initialize experience used by OpenSpec while avoiding surprise writes.

Files And Functions:

- existing: `scripts/install_skillpack.py` — behavioral reference during parity testing; remove only after the npm CLI is released and the deprecation window is complete.
- existing: `scripts/skillpack_hosts.py` — source of truth to port initially; consolidate/remove once Node becomes authoritative.
- planned: `test/fixtures/` — minimal canonical assets and expected rewritten outputs.
- planned: `test/installer-parity.test.mjs` — compares Node output against approved fixture expectations for each host/scope mode.

Use Case Questions:

- Retain the Python command for six months after the first stable npm release. Its README section will call it legacy, link to `layered-spec init`, and state the removal date; remove it in the first compatible release after that date.

### 3. Publish and upgrade a trustworthy scoped package

merged versioned release --CI validation and npm publish--> `@viete-io/layered-spec@latest` and reproducible global installation

Execution Logic:

1. Add package scripts for lint/type check as applicable, tests, `npm pack --dry-run`, and a clean temporary-directory CLI smoke test.
2. Add a pull-request workflow that runs the scripts on supported Node versions and fails when `npm pack --dry-run` omits a required canonical asset or includes excluded content.
3. Add a pull-request/release-validation workflow that verifies the same package tarball but does not publish. Publish the first stable releases manually from a maintainer terminal using npm login plus 2FA.
4. If automated publishing is needed later, create a narrowly scoped npm granular access token manually in npm, store it only as a protected GitHub Actions secret, and use a protected release workflow. No token may be committed, placed in a repository file, read through browser automation, or printed to logs.
5. Version with SemVer, publish under the `viete-io` npm organization, and update README quick-start, upgrade, and uninstall/troubleshooting guidance.

Data:

package metadata invariants:

| Field | Required value |
| --- | --- |
| name | `@viete-io/layered-spec` |
| bin command | `layered-spec` |
| default registry tag | `latest` |
| publish access | public |
| engine | chosen supported Node LTS range |
| package assets | `scripts/npm/bin/`, `scripts/npm/src/`, `skill/`, `planning/`, `prompts/`, `README.md`, `LICENSE` |

Tests:

`.github/workflows/ci.yml`
 - description: verifies the packed artifact on a clean Node environment
   input: `npm pack` tarball
   workflow: tarball --global install and CLI dry run--> no checkout required
   expected outcome: package exposes `layered-spec`, contains its canonical sources, and performs a host dry run.

`.github/workflows/publish.yml`
 - description: optional future token-authenticated publishing after protected-release validation
   input: protected tag matching package version
   workflow: release trigger --test and publish--> npm `latest` release
   expected outcome: the published package version equals the release tag, while the npm token remains available only to the protected workflow.

### 4. Select a stable, prerelease, or pinned installer version

user chooses package selector --npm resolves and globally installs one immutable package--> `layered-spec init` writes skills and a manifest from the selected release

Input Validation And Contracts:

- Treat an omitted selector as `latest`; `latest` must point only to a non-prerelease SemVer version.
- Treat `next` as the documented prerelease channel; it may point only to a SemVer prerelease version.
- Accept exact versions only as npm package selectors. The shell/npm client validates selector syntax and resolves the package before the CLI runs.
- After npm resolves a selector, `package.json#version`, the executable, canonical assets, and `layered-spec-skillpack.json#package_version` must all describe the same package tarball.

Execution Logic:

1. Publish `0.2.0-alpha.1` from the merged six-skill `user-stories` release state with `npm publish --tag next`; verify `latest` remains `0.1.1`.
2. Document the three native npm selectors in README quick start and upgrade guidance, with `@latest` as the displayed default.
3. Add release validation that rejects a prerelease publish targeting `latest` and a stable publish targeting `next`.
4. Promote a tested prerelease by publishing its final stable SemVer version from the merged `main` release state with `npm publish --tag latest`; only this step advances the default installer.

Files And Functions:

- existing: `package.json#version` - package version installed and recorded by the CLI.
- existing: `scripts/npm/src/cli.mjs#readPackageVersion` - preserves package-to-manifest provenance; do not add remote version loading.
- planned: `scripts/npm/release-channel-check.mjs` - validates the package version and intended npm dist-tag before a publish command runs.
- planned: `.github/workflows/release-validation.yml` - validates the selected release channel, tests, and packed tarball without publishing.
- existing: `README.md` - document stable, prerelease, pinned, upgrade, and rollback commands.

Tests:

`scripts/npm/test/release-channel-check.test.mjs`
 - description: accepts a stable package version only for `latest`
   input: `0.2.0` with `latest`
   workflow: stable package metadata --validate release channel--> publishable stable release
   expected outcome: validation succeeds.
 - description: accepts a prerelease package version only for `next`
   input: `0.2.0-alpha.0` with `next`
   workflow: prerelease package metadata --validate release channel--> publishable prerelease
   expected outcome: validation succeeds and `latest` is not selected.
 - description: rejects channel/version mismatches
   input: prerelease with `latest`, stable with `next`, or malformed package version
   workflow: invalid release metadata --validate--> failed release validation
   expected outcome: non-zero exit before npm publish can run.
 - description: records the package selected by npm
   input: each packed stable/prerelease fixture
   workflow: resolved package --`layered-spec init`--> installation manifest
   expected outcome: manifest `package_version` equals the fixture's `package.json#version`.

## Implementation checklist

1. [x] Create this npm-installer plan and record the current Python installer, canonical assets, documentation, and absent release automation.
2. [x] Decide Node 20.19+ support, the `layered-spec init` CLI with all hosts as the default, default repo scope/current directory, and a six-month Python deprecation period.
3. [x] Add root package metadata, the explicit `layered-spec init` command, and a Node implementation of host registry, source validation, rewriting, and manifest generation.
4. [x] Add table-driven unit tests plus a clean-tarball global-install smoke test, including all-host user scope, invalid input, and `--dry-run`.
5. [x] Update README quick start to show `npm install -g @viete-io/layered-spec@latest`, `cd your-project`, and `layered-spec init --host <host>`; retain Python migration notes for the six-month overlap.
6. [x] Add CI packaging checks and release validation. The maintainer npm account is authenticated; the initial release will be manually published with public access and npm 2FA.
7. [x] Publish `0.1.0`, install it from npm in a clean prefix, and start the six-month legacy Python migration window.
8. [-] Publish `0.1.1` so `layered-spec init` installs all supported hosts by default and records shared Codex/Antigravity output in one manifest.
9. [x] Amend this spec and README with npm-native stable, prerelease, and exact-version selection. Keep `@latest` as the default command and do not add an `init`-time package downloader.
10. [x] Add a release-channel validator and its unit tests; wire it before packed-tarball checks in release validation. The packed CLI smoke test now verifies that the manifest version equals the installed tarball version.
11. [-] Prepare the merged six-skill `user-stories` branch state as `0.2.0-alpha.1` for `npm publish --tag next`; verify after publication that registry tags are `latest=0.1.1` and `next=0.2.0-alpha.1`.
12. [ ] On merge to `main`, publish the corresponding final stable SemVer package with `latest`, then verify a no-selector global install resolves that version.

## Open questions

- Resolved: `npm install -g` installs the CLI; `cd your-project && layered-spec init --host <host>` performs project-local setup. `init --host all` is supported, and `--scope user` remains available when explicitly requested.
- Resolved: Node 20.19+ is the supported runtime floor.
- Resolved: no GitHub OIDC. First releases are manually published by an authorized `viete-io` npm user with 2FA; later GitHub automation, if wanted, uses a manually created granular access token in a protected secret.
- Resolved: retain the Python installer for six months after the first stable npm release.
- Resolved: use npm dist-tags rather than an interactive CLI downloader for version selection. npm selects the immutable package before the CLI runs, which keeps the executable, canonical assets, and installed manifest aligned.
- Resolved: stable releases use `latest`, prereleases use `next`, and reproducible installations use exact complete SemVer versions. `v0.2-alpha` remains a Git milestone; the npm prerelease is tagged and published as a complete SemVer version.

## Decision log

- 2026-07-14: Use an npm package with a Node CLI rather than an npm wrapper around Python. This removes both the repository clone and Python-runtime requirements from the normal installation path.
- 2026-07-14: Treat `skill/`, `planning/`, and `prompts/` as package-owned canonical content and protect this with an npm `files` allowlist and packed-tarball tests.
- 2026-07-14: Keep installation as an explicit CLI action rather than an npm lifecycle side effect; global package installation alone must not write into agent configuration directories.
- 2026-07-14: Name the explicit project-local command `init`, default it to repo scope at the current directory, require `--host <host|all>`, and document the OpenSpec-style quick start.
- 2026-07-14: Support Node 20.19+ and retain the legacy Python installer for six months after the first stable npm release.
- 2026-07-14: Do not use GitHub OIDC. Use manual npm publication with the maintainer's organization permissions and 2FA for initial releases; any future CI publisher uses a granular token stored only in a protected GitHub secret.
- 2026-07-14: `init` defaults to all hosts in both scopes. Codex and Antigravity share compatible repo-scoped `.agents/` output, so their identical generated artifacts are installed once and the manifest records both hosts.
- 2026-07-14: `npm publish --access public` passed package assembly and registry validation but npm required an authenticator one-time password. The release must be completed by the authenticated maintainer without exposing that code to the agent.
- 2026-07-14: Published `@viete-io/layered-spec@0.1.0` with the `latest` dist-tag. A clean registry installation ran `layered-spec init --host codex` successfully and produced the expected versioned manifest.
- 2026-07-14: Existing unrelated specs remain active and unchanged; this new spec is the only authoritative plan for npm distribution.
- 2026-08-04: npm registry inspection shows `latest` points to `0.1.1` and no prerelease is published. Keep this stable default while publishing the `user-stories` branch as a separately selectable `next` prerelease.
- 2026-08-06: Merge the npm release support from `main` into the six-skill `user-stories` branch. The four-skill `0.2.0-alpha.0` package was unpublished; publish the corrected immutable replacement as `0.2.0-alpha.1` under `next`.
