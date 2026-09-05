---
name: layered-workflow-planning
description: "Use when: planning or refining a workflow-bearing solution slice, use-case set, or document section that genuinely needs layered workflow syntax, typed workflows, branch or parallel states, execution logic, types, tables, events, or logic details. Do not use for pure analysis or reference documents with no workflow-bearing section."
metadata:
  version: "0.2.2"
argument-hint: "Describe the workflow-bearing solution or document section, the use cases already written, the layers already filled, and what should be expanded next."
user-invocable: true
---

# Layered Workflow Planning

When this skill creates or edits a specification, follow `skill/layered-spec-core/references/skill-pack-versioning.md`.

## When to Use
- Plan a new solution before implementation when the target artifact needs explicit workflows, state changes, or step-owned logic
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
- able to choose between a direct implementation use case, an implementation use case with requirements, and a declarative use case with separate realizations
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
- layer-specific syntax such as `Data`, `Types`, `Tables`, `Files And Functions`, `Tests`, `Invariants`, and `Use Case Questions`
- question placement rules between local and top-level question sections

When a specification needs a `Requirements` layer or implementation realization mappings, also read `skill/layered-spec-core/references/requirements-and-realization.md`. Keep detailed requirement and representation syntax there instead of duplicating it in this skill.

When a use case needs meaningful state invariants or derivations between them, also read `skill/layered-spec-core/references/invariants.md`. Keep the detailed layer syntax and proof terminology there instead of duplicating them in this skill.

When a workflow directly or mutually invokes itself, dispatches over recursive data variants, or needs explicit base-case, progress, cycle, or depth-limit treatment, read `skill/layered-spec-core/references/recursive-workflows.md` and apply its recursive-family rules and templates.

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

## Recursive Workflow Rule

Treat recursion as explicit invocation between workflow chains, not as a loop operator.

Generate one workflow chain for each distinct recursive step body and show every recursive call with its target chain label or use-case id. Keep compact related chains in one use case under `Detailed Workflow`; use hierarchical child use cases when recursive variants have substantial independent logic, contracts, errors, or tests.

An individual step may delegate without a local exit, but every recursive family must identify a reachable base or exit case and a progress measure. Specify cycle or depth-limit behavior when finite descent is not guaranteed by the input contract. Use self-referential or mutually referential `Uses` mappings for recursive use-case invocation without treating those mappings as realization.

## Requirements And Realization Rule

Choose the smallest structure that keeps required behavior and implementation logic clear.

1. Start with one implementation use case. Keep only its workflow and logic layers when they completely describe the behavior.
2. Add `Requirements` directly to that implementation use case when non-trivial conditions, invariant obligations, rejection rules, or required outcomes need explicit normative definitions but the implementation remains one coherent workflow.
3. Introduce a separate declarative use case when its requirements and the implementation decomposition each need an independently understandable structure, normally because several use cases jointly realize the behavior.
4. In either requirements-bearing form, use identified workflow chains when explicit inputs and outcomes improve clarity, EARS for natural-language behavioral requirements, a hierarchical contract when one umbrella obligation benefits from detailed clauses, and identified invariants, types, formulas, tables, or compatibility rules for non-transition constraints.
5. Select composition, product, coproduct, loop, recursive calls, or separate chains from the actual relationship between requirements.
6. When requirement ownership and realization are separate, add realization mappings by mapping requirements through `Realized by` and adding the symmetric `Realizes` mapping to every realizing use case. A realizing use case may itself be declarative and may contain `Realizes`, its own `Requirements`, and a further `Realized by` layer. Do not add self-referential mappings when one implementation use case owns its requirements.
7. Use `Uses` on an implementation use case when one of its states or steps references another declarative or implementation use case.
8. Keep reusable framework use cases separate when several callers use them. Use a declarative framework use case with separate realizations when the framework contract needs its own decomposition; otherwise an implementation framework use case may own its `Requirements` directly.
9. When requirement representations are present, retain their source requirement IDs, declare their semantic relation, and preserve the meaning of the definition written directly under each requirement ID.

Do not infer a normative requirement merely from current implementation behavior. Use the user request, product contract, authoritative specification, or an explicit planning decision as the requirement source.

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

When this happens, prefer adding the detail in `Detailed Workflow`, `Execution Logic`, `Types`, `Data`, `Files And Functions`, `Logic Details`, or `Invariants` according to the shared contract.

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

When a scientific or mathematical expression materially clarifies the implementation, render it as KaTeX in `Execution Logic`, `Implementation Logic`, `Logic Details`, `Data`, or `Invariants`. Use `$...$` for a short inline expression and `$$...$$` for a standalone equation or derivation.

Keep workflow lines, state names, transition labels, and branch labels as concise prose. Name the semantic transition there, then state the formula and its symbols, units, domains, and assumptions in the relevant logic layer. Do not introduce KaTeX merely for decoration.

## Invariants Layer Rule

Add `Invariants` only when selected workflow states have meaningful invariants whose preservation, assembly, or derivation materially clarifies the plan. Do not generate invariants for every state.

Treat the layer as a selective parallel chain over the main workflow. Keep its outline concise, map each invariant to a meaningful workflow state, and map each derivation from its source invariant or invariants through the relevant workflow transition or transition span to its target invariant or invariants. Put long natural-language reasoning, formulas, pseudocode, or formal text in detailed entries below the outline.

An invariant is not automatically a requirement. A requirement may reference an invariant owned by the same use case. When the invariant belongs to a realizing use case, keep the owning requirement self-contained, preserve the realization mappings, and let the invariant derivation identify the requirement it justifies. Natural-language reasoning may be a proof; use **verifiable proof** only for a formalism successfully checked by its verifier.

Follow `skill/layered-spec-core/references/invariants.md` for exact syntax and boundaries.

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
- start with implementation use cases and introduce declarative parents only when requirements and implementation decomposition both need separate workflow structures

### Stage 2: Fill Requirements And Structural Layers

If the user started adding types, tables, or endpoints:

- propagate that level of detail across the remaining relevant use cases
- preserve naming consistency across layers

If meaningful state invariants and their derivation are part of the solution, add an `Invariants` layer only to the affected use cases. Do not propagate it to unrelated states or use cases for structural uniformity.

If concrete constants, templates, matrices, lists, or other structured values matter to the workflow, add a `Data` layer instead of burying those values in prose.

When explicit requirements are needed:

- add identified workflow chains, EARS requirements, hierarchical contracts, or non-transition constraints to the owning implementation use case when it remains coherent
- keep static or quantitative requirements in the structure that expresses them most precisely
- move requirements to a separate declarative use case only when a distinct realization decomposition is also needed
- add `Realized by` only after the intended separate realizing use cases are identified

### Stage 3: Add Realizations And Logic Layers

If the user added execution logic, detailed workflow, or logic details for some use cases:

- extend the same layer family to the remaining use cases
- include important intermediate states and missing logic explicitly
- add `Implementation Logic` when the existing logic remains declarative and coding would otherwise require guesswork
- keep requirements and logic together when one implementation use case remains sufficient
- add realizing use cases and symmetric `Realized by` / `Realizes` mappings when declarative requirements need several distinct realization workflows
- add `Uses` when an implementation-use-case step references another use case, including a reusable framework use case

### Stage 4: Refine Or Normalize

If the user asks for improvement instead of expansion:

- tighten syntax
- normalize layer names
- remove duplication
- preserve semantics
- when requirement representations are present, verify their requirement coverage and source mappings

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
- Recursive workflows give every distinct recursive step body its own chain, name each call target, and record family-level exit and progress behavior
- The specification uses the smallest sufficient structure: implementation workflow and logic alone, implementation with owned requirements, or a declarative use case with separate realization mappings
- A `Requirements` layer stays on its implementation use case unless required behavior and implementation decomposition both benefit from separate structures
- Declarative use cases use identified `Requirements` entries and explicit `Realized by` mappings when separate realizing use cases are present
- Every realizing use case uses a symmetric `Realizes` mapping, regardless of whether it is declarative or implementation-oriented
- A declarative realizing use case may contain `Realizes`, its own `Requirements`, and `Realized by`
- `Uses` maps an implementation-use-case step to a referenced declarative or implementation use case without replacing realization mappings
- Reusable framework use cases use either a declarative contract with separate realizations or one coherent implementation use case with owned requirements
- Requirement representations retain source requirement IDs and declare whether they are equivalent, partial, examples, or another clearly defined relation
- Early validation and post-validation contracts are captured when they simplify downstream logic or remove redundant validation
- Execution Logic and Implementation Plan steps include Input, Outcome, Logic, External state, Config parameters, and Metrics
- Scientific formulas use KaTeX in a technical Logic, Data, or `Invariants` layer when useful; workflow chains and invariant outlines remain prose-only and scannable
- `Invariants` is used only where selected state invariants and their derivations materially clarify the workflow, and its outline remains consistent with the detailed invariant and derivation entries
- **verifiable proof** is used only when formal text was successfully checked by the corresponding verifier
- `Implementation Logic` is added only when declarative workflow layers are insufficient for implementation, and `Implementation Logic Proposal` or omission is used when the algorithm should remain developer-owned
- Complex algorithmic decompositions and intermediate structures are made explicit in the plan when they are needed for a correct or maintainable implementation
- Output examples should stay thin and must not drift from the contract

## One-Line Heuristic

Use the planning contract for exact shape, choose the smallest sufficient use-case structure, then expand one layer family at a time while preserving user-authored structure and separating planned behavior from observed existing logic.
