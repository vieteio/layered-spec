# Validate prepared stories and specifications

Read the `validation` section of `workflow.json` beside the active lifecycle `workflow.md`, including during standalone authoring. Without an active lifecycle, use `<workspace-root>/specs/spec-lifecycle/workflow.json`.

Defaults come from [default_workflow.json](../../spec-first-planning-loop/assets/default_workflow.json). If `workflow.json` is missing, create its parent directory as needed and copy the template. If only `validation` is absent, initialize that section from the template and preserve other sections. Never replace existing settings during skill updates or workflow restoration. Preserve the configuration if the lifecycle moves. Unreadable/invalid configuration, a missing/invalid required template or failed initialization is an explicit setup error, never permission to invent defaults or reset preferences.

The fields below belong to `validation`:

1. If disabled or `rejected`, skip without interpreter discovery or validation/installation prompts, even in later tasks/sessions. Only an explicit user request may re-enable validation; then reset installation to `ask` with a null hash.
2. Otherwise check the saved executable (`python`: absolute or workspace-relative path). If none was selected, find available Python 3.10+, including host-provided runtimes. No suitable interpreter permits a skip for this run. Never persist availability, disable validation for temporary failures or silently switch a saved target.
3. Ready dependencies require no installation prompt. Otherwise show the manifest, exact target and command; request approval, another environment or rejection. Include environment creation when needed. Selecting a target alone is not consent. Reuse approval only for the same environment and SHA-256 of the exact requirements file; changed requirements or a new/recreated environment need approval before installation.
4. Before installing, save `approved`, the selected executable path and manifest hash. Rejection saves `enabled: false`, `rejected` and a null hash, then skips validation. Read back saved JSON; report failed persistence without claiming the decision will survive future sessions. Pending approval permits no installation.

For either permitted skip, continue semantic review and report **validation not run**, with the reason; preparation may continue, but no structural pass is claimed. Actual validation errors still require correction. These are agent instructions; the CLI does not read this policy or install dependencies.

Only after approval, install using the selected interpreter in place of `python`:

```text
python -m pip install -r skill/layered-spec-core/requirements.txt
```

After creating or updating structured stories/use cases, run this command from the workspace root with the changed files and related specs needed to check references:

```text
python skill/layered-spec-core/scripts/validate_specs.py --workspace-root . --format json specs/feature.md specs/related.md
```

1. Read the full JSON report and fix all actionable errors, including both ends of `Realizes`/`Realized by`. Preserve the intended requirements and update affected incoming references when renaming declarations.
2. Revalidate the full file set after each correction batch. For tool errors (exit 2), fix the tooling or environment instead of changing the specs.
3. Stop after three unsuccessful repair attempts or two consecutive attempts with identical inputs and diagnostics; report unresolved errors without marking preparation complete.
4. Unless validation was skipped under the policy above, require a fresh passing report (exit 0) for the final files. Continue semantic review; structural validation does not establish requirement satisfaction or authorize implementation.

Use the validation command's `--help` for optional arguments.

Markdown generation and source/structure round-trip checks are development tools. Do not run them during spec preparation or validation.
