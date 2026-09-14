# Skill Pack Versioning

All skills in this pack use one version. Read the current version from the invoking skill's `metadata.version` field.

When a skill creates or edits a specification or ADR, place or update this line directly below the artifact title:

```md
- Last edited with skill pack: `<current skill-pack version>`
```

This value records the skill-pack version used for the most recent skill-guided edit. Do not add a separate specification-conformance version.

`spec-first-planning-loop/assets/default_workflow.md` carries the version of the skill pack containing that default workflow. An active `specs/spec-lifecycle/workflow.md` carries the default-workflow version from which it was created or with which it was most recently synchronized. Ordinary customization of the active workflow does not change that source version. Initialization or explicit synchronization/restoration from the bundled default copies its current version into the active workflow.

`architecture-decision-recording/assets/default_adr_template.md` carries its source version as `Default ADR template version`. The active repository template is `specs/architecture/template.md`. Initialize the active template from the bundled default only when it is missing. Never overwrite, merge, reconcile, or update an existing active template automatically when the bundled default changes. A user-provided active template remains authoritative even when it omits the bundled source-version marker.

Task-context files under `specs/task-contexts/` also use the `Last edited with skill pack` line. Their `active` or `closed` status describes the logical task lifecycle and is not a completeness certification.
