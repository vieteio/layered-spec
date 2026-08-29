# Planning Contract

This document defines the canonical shape for planning artifacts in this repository.

Implemented plans become specs. Later implementation updates, refactorings, or compatibility slices may leave older specs partially outdated or fully superseded. Planning must therefore create new specs and keep affected existing specs synchronized.

## Primary Location


Store generated plans and active specs in this folder:

- `specs/`

Use this folder as the default planning and spec registry unless a narrower location is explicitly required by the task.

`specs/spec-lifecycle/` contains specification-lifecycle policy rather than generated solution specifications. Do not classify files in that folder with solution-spec lifecycle states such as `active`, `partially outdated`, `superseded`, or `archived`.

## Planning Levels

Use the smallest level that preserves the requested behavior:

- user stories under `specs/stories/` describe user goals, user/application actions, visible states, waits that affect the journey, UI states, and E2E acceptance;
- technical use-case specs under `specs/` describe application-owned transitions, validation, persistence, APIs, events, and implementation logic;
- shared UI contracts under `specs/ui/` describe reusable spatial and visual rules across stories.

For mixed work, maintain both a story and one or more technical use cases. A material application action or state in the story maps to the use case or use cases that implement it. Do not duplicate internal contracts, durable-state representations, or implementation algorithms in the story merely because the same feature has a technical spec.

Create or update a story when the change affects a meaningful user journey. Do not require one for an internal-only refactor, local algorithm change, or maintenance task with no user-visible workflow.


## Artifact Lifecycle

Planning artifacts move through these states:

- `active`: current plan or current authoritative spec
- `updated by current plan`: existing spec updated in the same change
- `partially outdated`: still useful but no longer fully describes current implementation
- `superseded`: replaced by a newer spec or implementation contract
- `archived`: retained only for history

Allowed maintenance actions:

- `reuse`
- `amend`
- `mark outdated`
- `replace`
- `archive`

## Required Top-Level Sections

Every non-trivial technical use-case planning artifact should use these top-level sections in this order. User-story artifacts use the shape in `User-Story Mapping` instead.

1. `Title and scope`
2. `Planning anchor`
3. `Connected groups or observed existing logic`
4. `Use cases`
5. `Implementation checklist`
6. `Open questions`
7. `Decision log`

Do not add `Validation` or `Tests` as fixed top-level sections. Those belong under the relevant use case when needed.

### Title And Scope Wording

The `Title and scope` section should use direct task language rather than boilerplate meta-summary language.

Prefer wording that names the concrete behavior, bug, workflow, or change being planned in terms close to the user's task description.

Avoid generic openers that restate that the document is a spec without adding concrete meaning.

When practical, preserve the user's own domain wording and task framing instead of replacing it with more abstract planning vocabulary.

Prefer grouping the title and scope around the developer's conceptual change groups rather than the chronological order of edits.

Start from the affected workflow, artifact, or user-visible behavior, then name one or two grouped subchanges when that makes the scope easier to scan.

Prefer one compact lead sentence. Add a second sentence only when needed to capture important grouped edge cases or normalization rules.

Avoid changelist phrasing that simply chains implementation actions with repeated `and` clauses.

## Planning Anchor

The `Planning anchor` section should record:

- the concrete caller, route, symbol, event, failing test, or workflow entrypoint
- the changed assumption or compatibility rule behind the change
- why the work is non-local when applicable
- impacted specs already present in `specs/`
- preliminary spec action per impacted spec: `reuse`, `amend`, `mark outdated`, `replace`, or `archive`

## Connected Groups Or Observed Existing Logic

Use this section to collect existing behavior before planning updates.

When connected-code mapping is needed, group existing context by responsibility. Example groups:

1. Entry and orchestration
2. Loaders and resolvers
3. Persistence
4. Response and propagation
5. Frontend consumers
6. Validation
7. Specs

The `Specs` group should list:

- relevant files under `specs/`
- why each spec is connected to the planning anchor
- whether it remains authoritative or must be updated, marked outdated, or superseded

When the task is local and full connected mapping is unnecessary, this section may instead contain `Observed Existing Logic` with focused notes only.

## Use Cases

Represent planning detail under numbered use cases. Use-case numbering may be hierarchical when a parent use case is refined into narrower subcases. Each use case begins with the use case name, then the workflow line, then optional layers.

Use this shape:

```md
### 1. Use case name
initial state --step name--> next state
Layer_1_name:
layer content
Layer_2_name:
layer content

### 1.1 Child use case name
child state --step name--> child next state
Layer_name:
layer content
```

Rules:

- The workflow line appears immediately under the use case name.
- The workflow line does not use a `Workflow:` label.
- Layers are grouped directly under their use case.
- Individual layers are not rendered as markdown headers.
- Use hierarchical numbering such as `1`, `1.1`, `1.2`, `2` when a child use case refines the parent scope instead of introducing an unrelated top-level concern.
- Keep hierarchical numbering shallow and consistent unless deeper nesting materially improves clarity.
- Use-case-specific questions may be recorded in a use-case layer.
- `Open questions` remains a top-level section for general, cross-use-case, or escalated question batches.

## User-Story Mapping

User stories are the parent product-workflow level, not a second prose rendering of technical use cases. A story may contain several user actions and application actions; each application action may decompose into one or more technical use cases with additional internal states.

Use stable mapping labels where the relationship matters, for example `S2.step3 -> UC5.2`.

Story artifacts should normally contain:

- `Terms` for non-trivial actor, artifact, and state vocabulary;
- `Connected Groups Or Observed Existing Logic` when related stories, use cases, observed behavior, or shared UI contracts materially reach, resume, constrain, or otherwise operate on a story state or transition;
- `States` with user expectations, an optional story-specific `UI` wireframe, and technical mapping;
- `User stories` with a compact workflow and `User expectations`, `Technical mapping`, and `E2E tests` layers;
- `Implementation checklist`, `Open questions`, and `Decision log` when the story is actively driving implementation.

Use actor names in story workflow lines. Waiting is an actor action on a transition, not a state. Record it in the transition label only when it changes ownership, visible status, interruption behavior, retry/cancel options, or another user expectation. Model an intermediate condition as a state only when that condition or its available actions are meaningful to the story; do not create a state solely to say that an actor waits.

When present, `Connected Groups Or Observed Existing Logic` appears after `Terms` and before `States`. Each entry identifies the affected story state or step, relationship, evidence, and planning implication. Keep detailed code ownership and data flow in the connected-code map or technical use case.

### Common Use-Case Layers

Use these layer names when they help:

- `Execution Logic`
- `Implementation Logic`
- `Implementation Logic Proposal`
- `Events And Endpoints`
- `Files And Functions`
- `Types`
- `Tables`
- `Data`
- `Detailed Workflow`
- `Logic Details`
- `Observed Existing Logic`
- `Input Validation And Contracts`
- `Tests`
- `Validation`
- `Use Case Questions`

Use additional layer names only when they communicate a distinct responsibility clearly.

### Early Validation And Contract Rule

When a workflow accepts external or weakly shaped input, plan early validation near the workflow entry when practical.

After that validation, describe the contract that downstream workflow steps may rely on so inner logic does not keep re-validating the same structure.

Contracts may be expressed through one or more of these layers when useful:

- `Types` using nullable versus non-nullable fields, discriminated states, or defaulted fields
- `Validation` or `Input Validation And Contracts` for the validation boundary and accepted shapes
- `Tests` for accepted and rejected boundary cases
- `Logic Details` or `Detailed Workflow` for assumptions that remain important to the implementation

When the contract is meant to simplify later steps, say that explicitly and avoid planning redundant structural validation in inner workflow stages unless a separate trust boundary requires it.

### Workflow Syntax

Use this syntax for the workflow line or detailed workflow layers:

`state 1 --step name--> state 2`

Conditional branches:

`[branch 1, branch 2, branch 3]`

Parallel branches:

`(branch 1, branch 2, branch 3)`

Refactoring transitions:

`{workflow 1} --refactoring step--> {workflow 2}`

Typed workflow syntax:

`state 1: Type --step name--> state 2: Type`

Loop workflows:

```text
| loop condition: input --step 1--> state --step 2--> outcome |
```

The text before the first `:` is the natural-language loop condition. The workflow after `:` repeats while that condition applies. If the loop condition does not apply before the first iteration, the loop performs no steps and its input state continues unchanged. Iterations are sequential unless the loop body explicitly uses parallel workflow syntax. The condition is descriptive text and does not require further formalization.

Examples:

```text
| process each file: file --perform analysis--> report |
```

```text
| while unfinished work items remain:
  current work state --select next item--> selected item
  --process item--> updated work state |
```

Place loop workflows in fenced text blocks or inline code so the enclosing `|` characters are not interpreted as a Markdown table.

Refactoring syntax exists because implemented specs can become outdated after an implementation update. Use it when the plan changes an existing workflow rather than adding a net-new one.

### Scientific Formula Syntax

Use KaTeX only when a scientific or mathematical expression materially clarifies a technical rule, algorithm, invariant, transformation, or data definition. Keep ordinary implementation prose in plain language.

Put formulas primarily in `Execution Logic`, `Implementation Logic`, `Logic Details`, or `Data`. Use inline KaTeX (`$...$`) for a short expression within a sentence and display KaTeX (`$$...$$`) for a standalone equation, derivation, or multi-line aligned expression.

Do not put KaTeX in workflow lines, transition labels, branch labels, or workflow-state names. Those chains must remain scannable state-to-state prose. Give the chain a concise semantic state or step name, then place the formula in the relevant Logic layer and refer to the named state or quantity there.

For example:

```md
raw measurements --estimate model parameters--> fitted model

Logic Details:
Least-squares estimator:
$$
\hat{\theta} = \underset{\theta}{\operatorname{arg\,min}}\; \lVert X\theta - y \rVert_2^2
$$
```

Preserve notation definitions, units, domains, and assumptions next to a formula when they are needed to interpret it. Do not add formulas decoratively when a named rule or short prose is clearer.

### Decomposition And Intermediate Structures

The workflow line and deeper workflow layers may rely on intermediate steps or states already described by the developer in the task description.

The plan may also introduce a new decomposition for a workflow step when that decomposition is needed to explain the implementation clearly.

When an algorithm is non-trivial and requires dedicated intermediate structures or explicit data conversion, describe that in the plan before implementation rather than leaving the structure to be invented during code generation.

Examples include:

- indexes
- sorted arrays
- trees, graphs, and other derived structures
- task-specific derived representations

When such decomposition or structure planning is needed, record:

- why the decomposition or intermediate structure is necessary
- the source state or source data it is derived from
- the transformation step that builds it
- the workflow step or algorithm stage that consumes it
- important invariants, ordering assumptions, or performance intent when relevant

Prefer capturing this detail in one or more of these layers when useful:

- `Detailed Workflow`
- `Execution Logic`
- `Implementation Logic`
- `Types`
- `Data`
- `Files And Functions`
- `Logic Details`

### Implementation Logic Layer Rule

Use `Execution Logic` for workflow-oriented behavior when that is enough to explain what each step must do.

When the use case and logic layers remain mostly declarative and do not explain how the behavior should be implemented, add `Implementation Logic` to describe the algorithmic path.

That layer may include:

- intermediate indexes or lookup tables
- sorted or grouped derived collections
- trees, graphs, and other dedicated containers
- staged transformations and the structures passed between stages
- important invariants, ordering guarantees, and performance-sensitive choices

If the implementation is still unclear or the algorithm design should remain developer-owned, either omit `Implementation Logic` entirely or add `Implementation Logic Proposal` with high-level notes and an explicit statement that the full implementation approach is not yet clear and should be finalized by the developer.

### Type And Table Layer Syntax

Use this exact shape:

```md
Type_name
 - field_name1: optional_type # optional comment
 - field_name2: optional_type
   - nested_field_name: optional_type
```

For table layers, field names are columns.

### Data Layer Syntax

Use `Data:` when a use case depends on important constants, templates, lists, matrices, tables, or other concrete data structures that should stay explicit in the spec.

State the data item name first, then provide the concrete data using the markdown syntax that best fits the shape.

Use this shape:

```md
Data:
data_name:
<data payload rendered in the most readable markdown form>
```

Rules:

- Use `Data:` for concrete runtime or spec-owned values and structures that materially constrain, drive, or explain the use case.
- Write the data item name on its own line followed by the data body.
- The data body may use any markdown form that best communicates the structure, including plain text, bullet lists, tables, fenced code blocks with a relevant language, or KaTeX.
- Preserve exact values, templates, ordering, dimensions, and structural shape when those properties matter to the workflow.
- Use `Types` for schema or field contracts, `Tables` for persisted database tables, and `Data` for concrete non-table values or structures.
- When several related constants or structured fixtures belong together, group them in one `Data:` layer instead of scattering them through prose.

### Files And Functions Layer Syntax

Use this shape for the `Files And Functions` layer:

```md
Files And Functions:
 - existing: path/to/file.ts#functionOrSymbol - reuse or extension purpose
 - existing: path/to/file.ts - related file with no exact symbol yet
 - planned: path/to/new_file.ts#plannedSymbol - new file or function to implement
```

Rules:

- Use `existing` for files or symbols that should be reused, extended, or inspected.
- Use `planned` for files or symbols expected to be created or newly implemented.
- If the exact symbol is not known yet, the file path alone is acceptable.
- Keep the entry focused on implementation relevance rather than full file inventory.

### Code-To-Spec Traceability Rule

When spec implementation creates or substantially reshapes a function or method that directly realizes a use-case workflow step, reflect that relationship in the function or method docstring.

The docstring should make the implemented workflow step discoverable from the code without requiring the reader to reconstruct the mapping manually.

When practical, reuse the step wording or a close paraphrase from the relevant use case so the connection between spec and code remains easy to trace.

Apply this only when the function or method is a meaningful implementation boundary for that workflow step. Do not add forced traceability text to tiny helpers whose names and scope do not correspond to a spec step.

### Tests Layer Syntax

Use this shape for the `Tests` layer:

```md
Tests:
optional test file name
 - description: test 1 description
   input: input description
   workflow: state 1 with given input --one or several steps--> final state 1
   expected outcome: expected output or exception description
```

Rules:

- The optional test file name line may be omitted.
- At least one of `description` or `workflow` must be present for each test entry.
- If `workflow` is present, `input` and `expected outcome` should usually be present as well.

## Implementation Checklist

The `Implementation checklist` section is a numbered checklist of implementation tasks that shows current execution status.

Use this shape:

```md
1. [ ] not started task
2. [x] finished task
3. [-] in progress task
```

Rules:

- Use a numbered list for implementation tasks.
- Use `[ ]` for not started tasks.
- Use `[x]` for finished tasks.
- Use any visible non-space marker for in-progress work when needed, for example `[-]`.
- Keep the checklist updated so it reflects the actual implementation status.

When more execution detail is needed, each step should include:

- `Input`
- `Outcome`
- `Logic`
- `External state`
- `Config parameters`
- `Metrics`

Spec maintenance tasks belong here. If a plan updates behavior already described in an existing spec, include the spec update or supersession step in the implementation checklist rather than leaving it as optional cleanup.

If implementation is expected to create a function or method that matches a use-case workflow step, note in that implementation step that the docstring should name the workflow link.

## Open Questions

The `Open questions` section stays at the end of the plan before the decision log.

Questions should be grouped and batched rather than emitted one-by-one during implementation discovery.

Use-case-specific ambiguities may stay under the relevant use case in a `Use Case Questions` layer.

The top-level `Open questions` section is reserved for:

- general questions affecting multiple use cases
- blocking questions that stop further progress
- promoted local questions that became cross-cutting or need user escalation as part of the current batch

Question handling follows this rule set:

1. Continue autonomous planning and implementation until a coherent question batch is ready.
2. Do not stop after every new ambiguity.
3. If a few new tasks should be added to the plan, collect them into one batch and ask about the batch.
4. Stop when the grouped question batch is ready or when a truly blocking ambiguity prevents correct progress.

Use this status distinction:

- `blocking`: implementation or planning must stop until answered
- `non-blocking`: the system may proceed under an explicit assumption if the user accepts that mode

## Decision Log

Use the `Decision log` section to record:

- chosen compatibility strategies
- accepted assumptions
- spec status changes
- supersession decisions
- why a spec was updated instead of replaced, or replaced instead of updated

## Quality Checks

A valid planning artifact should satisfy all of these:

- uses the required top-level sections in order
- keeps layers grouped under each use case
- keeps `Open questions` as a top-level section
- uses `Use Case Questions` only for local questions tied to one use case
- uses the top-level `Open questions` section for general or escalated question batches
- treats implemented plans as specs that may need later maintenance
- scans existing specs when the task changes existing behavior or refactors a workflow
- records which specs stay authoritative and which become outdated or superseded
- includes spec maintenance in the implementation checklist when relevant
- distinguishes story-level workflows from technical use cases and maps material application transitions between them when both levels apply
- keeps story-specific UI states in `specs/stories/` and reusable UI rules in `specs/ui/`
- records code-to-spec traceability when implementation boundaries map cleanly to use-case workflow steps
- uses workflow operators consistently, including refactoring syntax when updating an existing implementation path
- uses KaTeX for scientific formulas only where it clarifies technical logic or data, while keeping workflow chains as readable prose
- uses hierarchical use-case numbering when parent and child use cases need distinct workflow treatment
- plans early validation and the post-validation contract when later workflow steps depend on stronger assumptions
- uses `Implementation Logic` only when algorithmic detail is needed beyond declarative workflow behavior, and uses `Implementation Logic Proposal` or omission when the implementation should stay developer-owned
- introduces non-trivial decompositions and intermediate algorithmic structures in the plan when implementation quality depends on them
- uses direct task-native wording in `Title and scope` and avoids abstract boilerplate
- groups `Title and scope` by conceptual subchange rather than raw edit order when multiple related changes are involved
- keeps `Title and scope` readable by using one compact lead sentence + an optional second sentence when detail is needed
