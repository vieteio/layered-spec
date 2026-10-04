# Task Context

A task-context file is reusable shared context for one logical task. It reduces repeated investigation across user stories, architecture decisions, basis evaluations, and specs. It is not a completeness boundary, an exclusive source, or the canonical owner of requirements, decisions, or behavior.

## Location And Identity

Store supporting artifacts for a logical task in one flat task folder:

```text
specs/task-contexts/<task-name>/
  task_context.md
  candidates/          # only when basis evaluation is needed
    <basis-name>.md
    comparison.md
```

Use a descriptive lowercase hyphenated task name. Resume a folder only when its recorded scope matches the same logical task; a matching name alone is insufficient. For an unrelated task whose name collides on the filesystem, append the next available numeric suffix, such as `task-name-2`, without overwriting or merging the existing folder. Keep task workspaces directly under `specs/task-contexts/`; component hierarchy is outside this version.

The folder is a task workspace, not a solution spec. `task_context.md` contains reusable context; `candidates/` contains task-owned basis evaluations. Create only artifacts that are needed. Standalone basis evaluation may create the workspace and candidates without requiring or creating a context file. This does not require a lifecycle workflow or a context-assembly skill.

Keep the stable `CTX-NNNN` identity in the context document's title, independently of the folder name. Allocate the next globally unique sequential identifier by inspecting context titles in task folders. Use the highest allocated number plus one; do not fill gaps or reuse known historical identifiers. Do not assign a context ID to a candidates-only workspace until its context file is created. Renaming a task folder does not change its context identity; update incoming path references if a rename is explicitly requested.

A logical task includes its initial request and later clarifications that continue the same requested outcome. Resume its existing workspace and context for those continuations. Create a new workspace when a later request materially replaces that outcome.

Task names and spec names are independent. One task may create or update several business, framework, story, ADR, or other artifacts; several tasks may contribute to the same spec. Record explicit relative links in `Affected artifacts`, and let consuming artifacts link relevant contexts and comparisons where useful. Do not infer a relationship only from matching names.

Use `active` while the task continues and `closed` when the task has ended. Status does not certify that every possible source or artifact has been exhaustively investigated. Increment the revision when shared directives, evidence, findings, affected-artifact mappings, or gaps change materially.

## File Shape

Use ordinary Markdown rather than layered use-case syntax:

```md
# CTX-NNNN: <task title>

- Last edited with skill pack: `<skill-pack version>`
- Status: `<active | closed>`
- Revision: `<revision>`

## Task outcome and scope

## Task directives

## Evidence

## Findings and concerns

## Affected artifacts

## Evidence gaps and conflicts
```

### Task Directives

Give each relevant user statement or other authoritative input a stable `T-NN` identifier and record:

- source;
- classification, such as `user-visible`, `architectural`, `implementation`, `validation`, or `unresolved`;
- authority, such as `required`, `preferred`, `candidate`, `observed`, `inferred`, or `unresolved`;
- the directive itself.

### Evidence

Give each observed fact a stable `E-NN` identifier and record:

- source and precise provenance;
- evidence kind, such as code, test, configuration, existing artifact, operational observation, or external authority;
- the observation;
- relevant concerns.

Observed implementation is evidence, not an automatic requirement or decision.

### Findings And Concerns

Give each artifact-neutral synthesis a stable `F-NN` identifier and record:

- the finding;
- the directive, evidence, or earlier finding identifiers from which it is derived;
- relevant concerns;
- potential reach without prematurely fixing `solution-local` or `architectural` ownership;
- stories, ADRs, comparisons, or specs to which it may be relevant.

Findings bridge evidence and artifact authoring, but remain task-scoped analysis. The consuming artifact owns its requirements, decisions, evaluation, or technical behavior.

### Affected Artifacts, Gaps, And Resolutions

For each affected artifact, record the expected action such as `reuse`, `amend`, `create`, `supersede`, or `investigate`, plus relevant task-context identifiers. When an artifact resolves a finding, gap, or conflict, add its link beside that item rather than materializing a separate context-view artifact.

Give material unresolved concerns stable `C-NN` identifiers. Record the missing evidence, potential consumers, and whether the gap blocks shared investigation or should be resolved only by a particular artifact owner.

## Reuse By Artifact Skills

An artifact skill may reuse relevant directives, findings, and evidence from task context, then inspect original or additional sources whenever its output needs information that is absent, incomplete, ambiguous, stale, or artifact-specific. The artifact skill remains responsible for the sufficiency and correctness of its own output.

Keep newly discovered information local to an artifact when it has no expected cross-artifact consumer. When information is useful to several artifacts or corrects shared understanding, update the task context first and synchronize affected artifacts. Do not block an artifact merely because the task context lacks a local detail.

Reference the task-context path and stable identifiers when provenance is useful. Do not copy the complete context into every consumer.

The spec's `Connected groups or observed existing logic` section may combine reused task-context material with additional investigation performed for that spec. It is written directly into the spec and is not a separately materialized view.

Durable reverse documentation remains a separate reusable artifact when valuable beyond the current task. Link it from task context and extract only the evidence and findings likely to be shared by the task's artifacts. A consumer may inspect the full documentation when it needs more detail.

## Content Boundary

Do not store raw conversation transcripts, secrets, irrelevant repository dumps, complete candidate evaluations, ADR rationale, user-story requirements, or technical-use-case implementations merely for completeness. Link canonical artifacts and original sources instead.
