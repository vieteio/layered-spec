---
name: layered-workflow-planning
description: "Use when: planning or refining a workflow-bearing feature slice, use-case set, or document section that genuinely needs layered workflow syntax, typed workflows, branch or parallel states, execution logic, types, tables, events, or logic details. Do not use for pure analysis or reference documents with no workflow-bearing section."
argument-hint: "Describe the workflow-bearing feature or document section, the use cases already written, the layers already filled, and what should be expanded next."
user-invocable: true
---

# Layered Workflow Planning

## When to Use
- Plan a new feature before implementation when the target artifact needs explicit workflows, state changes, or step-owned logic
- Expand user-provided workflow-bearing use cases into a complete set of workflows
- Fill missing layers for workflows the user has already started
- Refine one planning layer without regenerating the whole workflow-bearing part of the document
- Apply layered syntax to one workflow-bearing chapter inside a larger mixed document while leaving non-workflow chapters in plain structure
- Keep planning output concise, structured, and compatible across iterations
- Prepare planning artifacts that may later drive implementation, workflow tracing, or connected-code analysis

## Do Not Use This Skill When
- The task is only to document existing code after implementation; use code-logic-workflow-documentation instead
- The task is only to trace impacted existing code from one stale caller or identifier; use connected-code-mapping instead
- The user wants direct implementation with no planning artifact
- The requested artifact is primarily pure analysis or reference content with no workflow-bearing section
- Only the document as a whole is being described, but no chapter actually needs state, step, or transition logic

## Goal

Produce a planning artifact that is:

- iterative across multiple chat turns
- structured around use cases
- able to use hierarchical use-case numbering when parent and child cases need separate workflow treatment
- layered so different kinds of detail can be added independently
- concise enough for review, but explicit enough for implementation planning
- compatible with connected existing-code observations when a new workflow relies on old logic
- aligned with `planning/planning_contract.md`
- stored under `specs/` unless a narrower task-specific location is required

## Core Rule

Do not collapse all planning detail into one prose block.

Do not force the whole document into layered syntax when only one chapter needs workflow structure.

Follow the shared planning artifact contract in `planning/planning_contract.md`.

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

## Contract Ownership

The shared planning contract in `planning/planning_contract.md` is the single normative source for:

- required top-level sections
- use-case shape
- workflow operators and typed workflow syntax
- recommended optional use-case layers
- layer-specific syntax such as `Data`, `Types`, `Tables`, `Files And Functions`, `Tests`, and `Use Case Questions`
- question placement rules between local and top-level question sections

This skill should not redefine those rules. Use the contract directly for exact syntax and output shape.

Minimal reminder:

- each use case starts with one unlabeled workflow line directly under the use case name
- use-case numbering may be hierarchical when a parent use case is decomposed into narrower subcases
- optional named layers follow under the same numbered use case
- global structure and exact layer syntax come from `planning/planning_contract.md`
- generated plans and active specs belong in `specs/`

Apply that shape only to workflow-bearing artifacts or workflow-bearing sections of mixed documents.

## Hierarchical Use-Case Numbering Rule

Use hierarchical numbering when a use case needs child cases that refine the same parent workflow rather than introducing separate top-level concerns.

Typical examples:

- one parent use case splits into success, partial-success, and rejection subcases
- one workflow has multiple validation or compatibility paths that share the same entrypoint
- one broad use case needs narrower algorithmic or persistence subflows that should stay visibly grouped

Keep the hierarchy shallow and consistent unless deeper nesting materially improves readability.

## Language Rule

Keep plan wording close to the user's task language when that language is already precise.

Do not inflate direct task phrasing into abstract planning boilerplate.

Prefer direct wording that states the actual change, affected workflow, or intended behavior.

Do not replace concrete task phrases with newly invented shorthand if the shorthand drops distinctions that matter to the task.

Prefer meaning-bearing wording already present in the user request, nearby code, or the active spec when it remains precise.

Preserve words and short phrases that carry the user's distinctions about role, state, scope, timing, ownership, exceptions, or comparison, not just the headline domain terms.

When naming an intermediate step, helper, or structure, describe the concrete action or concrete contents first. Prefer names that say what is being collected, indexed, matched, grouped, filtered, skipped, or persisted, rather than names that only suggest a bigger architectural role.

If a broader helper label is still useful, define it immediately from the concrete inputs, outputs, or stored state so the reader never has to guess what data it actually contains or what distinction it is preserving.

If a shorter alias is genuinely needed for readability, define it immediately on first use and keep the original distinctions explicit. In particular, do not blur:

- persisted state versus derived runtime state
- canonical request state versus latest unsaved edits
- attached files versus files selected for context assembly versus persisted prepared context rows

For `Title and scope`, group wording by conceptual subchange rather than by the chronological order of edits.

Prefer one compact lead sentence that names the affected workflow, artifact, or behavior. Add a second sentence only when it improves clarity for grouped subcases or important edge rules.

Avoid changelist-style opening paragraphs that only enumerate implementation actions in sequence.

## Decomposition Rule

If a workflow step is too coarse to explain the intended implementation, decompose it in the plan before implementation.

If the algorithm requires intermediate structures or explicit data reshaping, surface that need in the plan instead of leaving the structure to be generated on the fly.

Typical signals:

- the step requires a derived index or lookup structure
- the step builds or traverses trees, graphs, or other derived structures
- the step depends on ordering, aggregation, batching, or other structural preprocessing
- the developer already described intermediate states that should be preserved in the plan

When this happens, prefer adding the detail in `Detailed Workflow`, `Execution Logic`, `Types`, `Data`, `Files And Functions`, or `Logic Details` according to the shared contract.

When important constants, string templates, lists, matrices, tables, or other concrete structures drive the workflow, prefer a `Data` layer so those values stay explicit.

## Early Validation And Contract Rule

When a workflow accepts external, weakly shaped, or compatibility-sensitive input, plan early validation near the entrypoint when practical.

Then describe the post-validation contract that inner workflow steps may rely on. That contract can be expressed through types, nullable versus non-nullable fields, default values, comments, validation notes, and tests.

The planning goal is to simplify later workflow steps and remove redundant structure validation once the validated contract is established, unless a later trust boundary requires re-validation.

Capture this in `Input Validation And Contracts`, `Validation`, `Types`, `Data`, `Logic Details`, or `Tests` according to the shared contract and the level of detail already present in the artifact.

## Execution Logic Rule

When writing an `Execution Logic` or `Implementation Plan` layer, format it as ordered workflow steps.

For each step, include:

- Input: operational state or exact structures consumed
- Outcome: resulting state after the step
- Logic: actual processing performed
- External state: persisted or externally visible side effects
- Config parameters: settings or flags controlling the step
- Metrics: measurable signals, including execution time when relevant

## Scientific Formula Rule

When a scientific or mathematical expression materially clarifies the implementation, render it as KaTeX in `Execution Logic`, `Implementation Logic`, `Logic Details`, or `Data`. Use `$...$` for a short inline expression and `$$...$$` for a standalone equation or derivation.

Keep workflow lines, state names, transition labels, and branch labels as concise prose. Name the semantic transition there, then state the formula and its symbols, units, domains, and assumptions in the relevant logic layer. Do not introduce KaTeX merely for decoration.

## Implementation Logic Layer Rule

Use `Execution Logic` for operational step behavior when that is enough to explain how the workflow should proceed.

If the generated workflow and logic layers are still mostly declarative and do not explain the implementation path, add `Implementation Logic` with the algorithmic detail needed to support coding.

That layer may describe:

- indexes, lookup tables, caches, or grouping structures
- derived containers such as trees, graphs, or staged intermediate representations
- ordering rules, traversal strategy, batching, aggregation, or reconciliation steps
- invariants that let downstream code avoid repeated validation

If the implementation remains unclear and should stay developer-owned, either omit `Implementation Logic` or add `Implementation Logic Proposal` with high-level notes plus an explicit remark that the full implementation is not yet clear and should be completed by the developer.

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
- if the surrounding document also contains non-workflow analysis or reference sections, keep those sections outside the layered use-case format

### Stage 2: Fill Structural Layers

If the user started adding types, tables, or endpoints:

- propagate that level of detail across the remaining relevant use cases
- preserve naming consistency across layers

If concrete constants, templates, matrices, lists, or other structured values matter to the workflow, add a `Data` layer instead of burying those values in prose.

### Stage 3: Fill Logic Layers

If the user added execution logic, detailed workflow, or logic details for some use cases:

- extend the same layer family to the remaining use cases
- include important intermediate states and missing logic explicitly
- add `Implementation Logic` when the existing logic remains declarative and coding would otherwise require guesswork

### Stage 4: Refine Or Normalize

If the user asks for improvement instead of expansion:

- tighten syntax
- normalize layer names
- remove duplication
- preserve semantics

## Quality Checks

- Every use case starts with a workflow before deeper layers
- The workflow line has no label; it is the raw workflow text immediately under the use case name
- Exact syntax, section order, and layer rules come from `planning/planning_contract.md`
- Generated plans and active specs are placed in `specs/` unless the task explicitly narrows the location
- User-authored content is preserved unless it conflicts with nearby structure
- Pure analysis or reference documents without workflow-bearing sections are left in a lighter structure and do not trigger this skill
- Mixed documents use layered syntax only for the workflow-bearing section that needs it
- Title and scope wording stays close to the user's task language and avoids abstract boilerplate
- Title and scope wording groups related changes conceptually instead of mirroring raw edit chronology
- Workflow lines and deeper layers keep concrete task terms unless a new alias is defined immediately and remains semantically exact
- Helper and intermediate-structure names stay close to the concrete data they hold, the concrete action they perform, and the user-visible distinctions they preserve
- Existing-code observations are separated from planned new logic
- Hierarchical numbering is used when parent and child use cases need separate but related workflow treatment
- Early validation and post-validation contracts are captured when they simplify downstream logic or remove redundant validation
- Execution Logic and Implementation Plan steps include Input, Outcome, Logic, External state, Config parameters, and Metrics
- Scientific formulas use KaTeX in a technical Logic or Data layer when useful; workflow chains remain prose-only and scannable
- `Implementation Logic` is added only when declarative workflow layers are insufficient for implementation, and `Implementation Logic Proposal` or omission is used when the algorithm should remain developer-owned
- Complex algorithmic decompositions and intermediate structures are made explicit in the plan when they are needed for a correct or maintainable implementation
- Output examples should stay thin and must not drift from the contract

## One-Line Heuristic

Use the planning contract for exact shape, then expand one layer family at a time while preserving user-authored structure and separating planned behavior from observed existing logic.
