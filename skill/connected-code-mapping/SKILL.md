---
name: connected-code-mapping
description: "Use when: mapping a non-local code change from one anchor through connected backend, frontend, persistence, propagation, and test surfaces, especially when the result must support a workflow-bearing spec or workflow-bearing document section. Do not use this skill just to force layered output onto pure analysis or reference documents."
argument-hint: "Describe the concrete anchor, the changed assumption, and whether the result should stay as mapping output or also feed a workflow-bearing spec or section."
user-invocable: true
---

# Connected Code Mapping

Use this skill to plan non-local code changes that start from one concrete caller, endpoint, component, store event, or failing flow, then expand into all connected code that must move together.

## Use This Skill When

- one caller is broken because a helper or API changed
- one identifier changes scope, such as `project_id -> diagram_id`
- one route, loader, or store still assumes an old ownership model
- one behavior requires coordinated backend, frontend, persistence, notifications, and tests
- a migration or compatibility slice must be planned before editing

## Do Not Use This Skill When

- the change is isolated to one file and has no shared state implications
- the task is a simple bug fix with no identifier, ownership, or data-flow impact
- the user only wants implementation without planning or mapping work
- the requested artifact is pure analysis or reference content with no workflow-bearing section and no connected code-change mapping need

## Goal

Build a mapping-first plan that:

- finds connected parts of the codebase affected by one change
- finds relevant existing specs affected by the same change
- describes context for each connected group
- plans updates by responsibility instead of by file list
- prevents partial fixes where one caller changes but its loaders, persistence, propagation, or tests remain stale
- prevents code changes from silently leaving repository specs outdated
- can be summarized into layered workflow planning sections when the broader feature plan or one chapter of a mixed document genuinely needs workflow-bearing format
- can provide concise, evidence-backed context for a related user-story artifact without duplicating the connected code map in that story

## Core Rule

Do not plan from files. Plan from ownership and data flow.

Start from one concrete entry point and trace all code that reads, writes, transforms, transports, caches, notifies, or validates the same domain state.

When the user asks for compatibility with layered workflow planning, keep the mapping-first analysis but emit the result in named layers only for the workflow-bearing artifact or section instead of replacing all output with layered prose.

Do not wrap pure analysis or reference sections in use cases and layers when no workflow or state transition is being planned.

When the mapped workflow has meaningful parent and child cases, use hierarchical use-case numbering from the shared contract instead of flattening distinct subcases into one list.

When the anchor exposes weakly shaped input or a compatibility boundary, map the early validation point and the stronger post-validation contract that downstream steps may rely on.

If layered output remains too declarative to guide implementation, add `Implementation Logic` only where the algorithmic path must be made explicit. If the implementation approach is still not recoverable with confidence from the existing code and slice context, omit that layer or use `Implementation Logic Proposal` with a clear remark that fuller implementation reconstruction needs developer clarification.

## Inputs

At minimum, identify:

- one concrete anchor: failing caller, stale route, removed helper, broken UI flow, or test
- one changed assumption: identifier scope, ownership root, payload shape, compatibility rule, or persistence contract

Helpful optional inputs:

- related tables
- related stores or components
- existing plan documents
- existing specs in `specs/`
- candidate regression test location

## Workflow

### 1. Pin The Planning Anchor

Record:

- exact caller, symbol, route, event, or failing test
- exact old assumption underneath it
- why this is not a local fix

Result:
- one precise anchor defining the slice

### 2. Scan Spec Context

Before expanding the rest of the connected map, inspect `specs/` for relevant plans or specs.

For each relevant spec, record:

- file name
- why it is connected to the anchor
- current status: `active`, `updated by current plan`, `partially outdated`, `superseded`, or `archived`
- required action: `reuse`, `amend`, `mark outdated`, `replace`, or `archive`

If no relevant spec exists, record that explicitly.

When the mapping supports a user-story artifact, also inspect `specs/stories/`. Record each related story, its affected state or step, the relationship to the planning anchor, and whether the story should be reused, amended, or only cited as observed context.

### 3. Build A Connected-Part Map

Trace both upstream and downstream from the anchor.

Map connected parts into these responsibility groups:

1. Entry and orchestration
   - routes
   - chat tools
   - commands
   - store events/effects

2. Loaders and resolvers
   - helper functions
   - preload logic
   - query builders
   - compatibility resolution helpers

3. Persistence
   - write helpers
   - ORM models
   - tables
   - allocator logic

4. Response and propagation
   - API responses
   - notifications
   - websocket payloads
   - cached records

5. Frontend consumers
   - stores
   - components
   - routing state
   - editor state

6. Validation
   - unit tests
   - integration tests
   - static type or lint surfaces

7. Specs
   - plans or specs in `specs/`
   - spec status and required updates

8. Story context, when a user-visible workflow is affected
   - related story files and affected states or steps
   - technical use cases that create, restore, constrain, or publish those states
   - observed existing behavior and shared UI contracts that change visible expectations

### 4. Describe Context Per Group

For each connected group, capture:

- purpose
- current responsibility
- why it is connected to the anchor
- mapped functions and files
- database context
- frontend context
- invariants
- risk if skipped
- validation path

When a validation boundary is part of the slice, also capture:

- where weak input first enters the mapped workflow
- what validation or normalization occurs at that boundary
- what contract later groups may safely assume after that validation
- where re-validation is still required because a separate trust boundary exists

For the `Specs` group, also capture:

- whether the spec is still authoritative for the impacted workflow
- whether the new work is a refinement, compatibility slice, or refactoring of an existing implementation
- whether the existing spec must be amended, marked outdated, or superseded

For the `Story context` group, also capture:

- the relationship to each affected story state or step
- evidence from an existing story, use case, code path, or UI contract
- the planning implication: `reuse`, `amend`, `preserve`, or `validate`

Keep the result concise enough to place in a story's `## Connected Groups Or Observed Existing Logic` section. Do not replace the code map with story prose.

### 5. State The Compatibility Strategy

If the slice uses a temporary compatibility rule, state it once and reuse it consistently.

Examples:

- resolve the project's primary diagram
- keep project-scoped route but diagram-scoped persistence
- keep old response contract while migrating internal ownership

Never mix multiple compatibility strategies inside one slice.

### 6. Convert The Map Into Tasks

Decompose work in this order:

1. Documentation task
   - add or update plan entry with context, mappings, DB tables, frontend logic, required spec updates, planned test

2. Shared state task
   - update common resolver, typed identifier, context object, or helper

3. Runtime path task
   - update the concrete route, tool, command, or store effect

4. Propagation task
   - update notification payloads, responses, cache shape, or emitted identifiers

5. Validation task
   - add one focused regression proving the new ownership or mapping rule

6. Cleanup task
   - remove stale placeholders, trackers, compatibility shims, or superseded spec markers if safe

Spec update work is not optional cleanup. If the implementation changes behavior already described by a spec, include the spec maintenance step in the main task sequence.

### 7. Explicitly Mark Deferred Work

If a connected surface exists but is out of scope, document it clearly.

Examples:

- UI diagram selection deferred because the current slice only needs backend compatibility
- broader editor-state verification paused while a blocking backend migration is landed
- related spec rewrite deferred because the current slice only amends one compatibility rule and the remaining spec section is still accurate

### 8. Emit Layered Output When Relevant

If this mapping work supports a broader planning artifact for a new or changed feature, summarize the result in compatible layers such as:

- Planning anchor
- Connected groups or observed existing logic
- Story context, when the output supports a user-story artifact
- Use cases
- Input Validation And Contracts
- Implementation Logic
- Implementation checklist
- Open questions
- Decision log

Use workflow syntax only where it clarifies actual state transitions discovered from the mapping.

If the broader artifact is mixed, keep non-workflow chapters in plain structure and emit layered syntax only for the section that carries workflow or state-transition detail.

Follow the shared artifact contract in `planning/planning_contract.md`.

Do not restate workflow operators or layer syntax locally. Use the contract for exact operator and layer definitions.

When mapped scientific logic needs a formal expression, put KaTeX in the receiving technical `Execution Logic`, `Implementation Logic`, `Logic Details`, or `Data` layer. Keep workflow lines, state names, and transition labels as prose so the map stays scannable.

## Output Format

When using this skill, produce a plan or planning note with these sections.

### Title and scope

### Planning anchor

- exact entry point
- exact stale assumption
- impacted specs and their required action

### Connected groups or observed existing logic

For each group:

- purpose
- mapped symbols and files
- backend context
- data context
- frontend context
- risk if skipped
- validation

For the `Specs` group, include status and required action for each matched spec.

When the mapping feeds a user story, add a concise `### Story context` subsection that can be copied into the story's `## Connected Groups Or Observed Existing Logic` section. Each entry must identify the affected story state or step, relationship, evidence, and planning implication.

### Use cases

Represent impacted or planned workflows as numbered use cases. Use hierarchical numbering when a parent workflow is refined into narrower validation, compatibility, success, or rejection subcases. Keep workflow lines and optional layers under each use case according to `planning/planning_contract.md`.

### Implementation checklist

Use a numbered checklist that shows actual status, for example:

1. [ ] spec maintenance tasks
2. [ ] resolver changes
3. [ ] runtime path changes
4. [ ] propagation changes
5. [ ] validation tasks
6. [ ] deferred items only when intentionally left out of scope

### Open questions

- grouped blocking and non-blocking questions

### Decision log

- compatibility strategy
- spec supersession or outdated decisions

## Quality Checks

A good result from this skill must satisfy all of these:

- starts from one concrete caller or stale assumption
- scans `specs/` for connected specs before finalizing the plan
- maps connected code by responsibility, not just by file search results
- includes backend, frontend, data, and test context where relevant
- includes spec context where relevant
- names exact functions, routes, stores, tables, or tests
- states one compatibility strategy clearly
- includes at least one focused validation path
- records early validation boundaries and downstream contracts when the mapped slice depends on them
- leaves deferred work explicit
- if layered output is requested, preserves mapping-first reasoning while staying syntax-compatible with `planning/planning_contract.md`
- if layered output includes scientific formulas, places them in technical Logic or Data layers as KaTeX while keeping workflow chains prose-only
- if layered output is requested, uses `Implementation Logic` only when declarative workflow layers are insufficient and uses omission or `Implementation Logic Proposal` when the algorithm cannot be reconstructed confidently from existing code without developer clarification
- if a `Tests` layer is emitted, it is tied to the mapped impact slice and stays compatible with the contract
- records whether impacted specs remain authoritative, become outdated, or are superseded
- when a user story is affected, distinguishes story-level context from the detailed connected code map and identifies evidence for each story connection

## Common Failure Modes

- listing files without explaining why they are connected
- updating code without checking whether an existing spec now lies about the workflow
- fixing only the caller and skipping the shared resolver or write path
- changing persistence without changing emitted payloads
- saying "frontend affected" without naming the store or component path
- saying "add tests" without naming the regression target and behavioral assertion
- mentioning a related spec without deciding whether to reuse, amend, mark outdated, replace, or archive it
- emitting a high-level workflow without showing the connected readers, writers, or ownership boundaries behind it

## One-Line Heuristic

For any non-local change: map the ownership root, scan connected specs, trace every connected reader and writer, group them by responsibility, then plan spec maintenance, resolver, runtime, propagation, and regression together.
