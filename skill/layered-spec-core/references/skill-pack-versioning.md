# Skill Pack Versioning

All skills in this pack use one version. Read the current version from the invoking skill's `metadata.version` field.

When a skill creates or edits a specification, place or update this line directly below the specification title:

```md
- Last edited with skill pack: `<current skill-pack version>`
```

This value records the skill-pack version used for the most recent skill-guided edit. Do not add a separate specification-conformance version.

`spec-first-planning-loop/assets/default_workflow.md` carries the version of the skill pack containing that default workflow. An active `specs/spec-lifecycle/workflow.md` carries the default-workflow version from which it was created or with which it was most recently synchronized. Ordinary customization of the active workflow does not change that source version. Initialization or explicit synchronization/restoration from the bundled default copies its current version into the active workflow.
