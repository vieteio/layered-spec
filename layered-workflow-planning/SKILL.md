---
name: layered-workflow-planning
description: "Use when: planning new features or refining use cases in an iterative loop with layered workflow syntax, typed workflows, branch or parallel states, refactoring workflows, type layers, table layers, execution logic, events and endpoints, or logic details."
argument-hint: "Describe the feature or planning task, the use cases already written, the layers already filled, and what should be expanded next."
user-invocable: true
---

# Layered Workflow Planning

## When to Use
- Plan a new feature before implementation
- Expand user-provided use cases into a complete set of workflows
- Fill missing layers for workflows the user has already started
- Refine one planning layer without regenerating the whole document
- Keep planning output concise, structured, and compatible across iterations
- Prepare planning artifacts that may later drive implementation, workflow tracing, or connected-code analysis

## Do Not Use This Skill When
- The task is only to document existing code after implementation; use code-logic-workflow-documentation instead
- The task is only to trace impacted existing code from one stale caller or identifier; use connected-code-mapping instead
- The user wants direct implementation with no planning artifact

## Goal

Produce a planning artifact that is:

- iterative across multiple chat turns
- structured around use cases
- layered so different kinds of detail can be added independently
- concise enough for review, but explicit enough for implementation planning
- compatible with connected existing-code observations when a new workflow relies on old logic

## Core Rule

Do not collapse all planning detail into one prose block.

Represent each use case as:

1. one workflow line or workflow block
2. zero or more named layers added underneath it
3. user-authored content preserved unless it is locally inconsistent

## Interaction Model

Work in an iterative planning loop.

1. Start from the user's current planning state.
2. Detect which use cases already exist and which layers are already filled.
3. Fill only the requested gaps, or the smallest obvious adjacent gaps needed for coherence.
4. Preserve the user's wording where practical.
5. If improving existing content, prefer delta edits over full rewrites.
6. Mark inferred content clearly when the source requirement is incomplete.

## Workflow Syntax

Use this syntax for high-level workflows:

`state 1 --step name--> state 2`

Conditional branches:

`[branch 1, branch 2, branch 3]`

Parallel branches:

`(branch 1, branch 2, branch 3)`

Workflow refactoring:

`{workflow 1} --refactoring step--> {workflow 2}`

Example:

`state 1 --step name 1--> state 2 --step name 2--> [conditional outcome state 1 --branch 1 step--> branch 1 state, conditional outcome state 2 --branch 2 step--> branch 2 state] --step name 3--> final state`

## Typed Workflow Syntax

Use this syntax when a workflow layer needs explicit state types:

`state 1: Type --step name--> state 2: Type`

The same branch, parallel, and refactoring operators are allowed inside typed workflows.

Example:

`state 1: Tuple[A, B] --step name 1--> state 2: List[X] --step name 2--> [conditional outcome state 1 --branch 1 step--> branch 1 state, conditional outcome state 2 --branch 2 step--> branch 2 state] --step name 3--> final state: Result`

## Use Case Shape

Write each use case in this structure:

```md
1. use_case_name
workflow
Layer_1_name: layer content
Layer_2_name:
multi line
layer content
Layer_3_name: multi line
layer
content
```

The workflow line comes first. Named layers come after it.

## Recommended Layers

Use these layer names unless the user already established a different naming convention:

- Workflow
- Execution Logic
- Events And Endpoints
- Types
- Tables
- Detailed Workflow
- Logic Details
- Observed Existing Logic
- Tests
- Validation
- Open Questions

### Layer Purposes

- Workflow: high-level state transition representation of the use case
- Execution Logic: implementation-oriented sequence that explains how the workflow executes
- Events And Endpoints: UI events, store events, backend endpoints, and externally visible transitions
- Types: runtime structures, DTOs, and nested payload shapes
- Tables: persisted schema, key columns, and relationships
- Detailed Workflow: typed or more granular workflow with important intermediate states
- Logic Details: important rules, missing logic, constraints, or non-obvious behavior not covered elsewhere
- Observed Existing Logic: existing code or flows that should be reused, constrained, or updated
- Tests: planned test coverage with optional test file grouping and optional workflow scenario fields
- Validation: planned checks, tests, or review points
- Open Questions: ambiguities or unresolved decisions

## Type And Table Layer Syntax

Use this exact shape for type or table layers:

```md
Type_name
 - field_name1: optional_type # optional comment
 - field_name2: optional_type
   - nested_field_name: optional_type
```

For tables, field names are columns. Nested fields are generally not relevant for table layers.

## Tests Layer Syntax

Use one shared syntax for the `Tests` layer.

```md
Tests:
optional test file name
 - description: test 1 description
   input: input description
   workflow: state 1 with given input --one or several steps--> final state 1
   expected outcome: expected output or exception description
 - description: test 2 description
   input: input description
   workflow: state 2 with given input --one or several steps--> final state 2
   expected outcome: expected output or exception description
```

Rules:

- The optional test file name line may be omitted when the target file is unknown or not relevant at planning time.
- For each test entry, `description`, `input`, `workflow`, and `expected outcome` are optional fields.
- At least one of `description` or `workflow` must be present for each test entry.
- If `workflow` is present, `input` and `expected outcome` should normally be present as well unless the scenario is genuinely incomplete.
- Use concise checklist-style entries by filling only `description` when deep scenario detail is unnecessary.
- Use the full scenario shape when the test is meant to validate a precise workflow path, exception, or branch outcome.

## Execution Logic Rule

When writing an `Execution Logic` or `Implementation Plan` layer, format it as ordered workflow steps.

For each step, include:

- Input: operational state or exact structures consumed
- Outcome: resulting state after the step
- Logic: actual processing performed
- External state: persisted or externally visible side effects
- Config parameters: settings or flags controlling the step
- Metrics: measurable signals, including execution time when relevant

## Existing-Code Integration Rule

When a new use case depends on existing code:

- observe the existing code path first
- record reused or constrained behavior in `Observed Existing Logic`
- add `Events And Endpoints`, `Types`, `Tables`, or `Logic Details` entries only where that dependency matters
- add `Tests` entries where reused behavior or compatibility constraints need explicit regression coverage
- if the change is non-local, connected-code-mapping can be used to derive the connected surfaces and then summarized back into this layered format

## Output Strategy By Planning Stage

### Stage 1: Expand Use Cases

If the user only provided a few use cases or workflows:

- keep output at workflow level
- add missing use cases
- do not invent deep layers unless requested

### Stage 2: Fill Structural Layers

If the user started adding types, tables, or endpoints:

- propagate that level of detail across the remaining relevant use cases
- preserve naming consistency across layers

### Stage 3: Fill Logic Layers

If the user added execution logic, detailed workflow, or logic details for some use cases:

- extend the same layer family to the remaining use cases
- include important intermediate states and missing logic explicitly

### Stage 4: Refine Or Normalize

If the user asks for improvement instead of expansion:

- tighten syntax
- normalize layer names
- remove duplication
- preserve semantics

## Output Shape

```md
# <Feature Name>

Brief scope.

## Use Cases

1. use_case_name
Workflow: initial state --step--> next state
Execution Logic:
1. Step name
Input: ...
Outcome: ...
Logic: ...
External state: ...
Config parameters: ...
Metrics: ...
Events And Endpoints:
- UI event: ...
- Store event: ...
- Backend endpoint: ...
Types:
RequestType
 - field: type
Tables:
task_table
 - id: uuid
Detailed Workflow:
initial state: RequestType --step--> persisted state: TaskRow
Logic Details:
- ...
Observed Existing Logic:
- ...
Tests:
 - description: persists valid request
 - description: rejects invalid request with expected exception
Validation:
- ...
Open Questions:
- ...
```

## Quality Checks

- Every use case starts with a workflow before deeper layers
- Layer names are explicit and stable across use cases unless the user asked for variation
- Typed workflow syntax is used only where it adds clarity
- Branches, parallel work, and refactoring steps use the shared operators consistently
- User-authored content is preserved unless it conflicts with nearby structure
- Existing-code observations are separated from planned new logic
- Execution Logic and Implementation Plan steps include Input, Outcome, Logic, External state, Config parameters, and Metrics
- If a `Tests` layer is present, each test entry includes at least `description` or `workflow`

## One-Line Heuristic

Start with workflows, add one layer family at a time, preserve user-authored structure, and separate planned new behavior from observed existing logic.