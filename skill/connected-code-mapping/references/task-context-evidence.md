# Connected-Code Contributions To Task Context

Use this reference when connected-code mapping receives `specs/task-contexts/<task-name>/task_context.md`.

Read the shared file contract in `skill/layered-spec-core/references/task-context.md`. Preserve existing identifiers and revision history.

Follow explicit links between the task context, its task-owned candidates, and affected specs. One task can support several specs, including reusable-framework specs; do not infer consumers from matching names.

## What To Add

Add connected information that is likely to be reused by an ADR, basis comparison, spec, or verification pass:

- evidence entries for observed behavior, code symbols, configuration, tests, platform contracts, and existing artifacts;
- artifact-neutral findings derived from that evidence;
- concern relationships;
- affected-artifact actions;
- material gaps or conflicts.

Use stable task-context identifiers. Each finding cites the directives, evidence, or earlier findings from which it is derived. Record observed constraints and consequences without selecting a basis or promoting current implementation into a requirement.

## What Stays Local

Keep detailed file inventories, implementation tasks, artifact-local planning implications, and mapping detail needed by only one output in the requested mapping or consuming artifact. Task context is reusable shared context rather than a complete copy of the connected map.

## Standalone Use

When no task-context path is supplied, produce the requested connected map normally. Do not create task context implicitly.
