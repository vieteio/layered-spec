# Planning Contract

This document defines the canonical shape for planning artifacts in this repository.

Implemented plans become specs. Later implementation updates, refactorings, or compatibility slices may leave older specs partially outdated or fully superseded. Planning must therefore create new specs and keep affected existing specs synchronized.

Specifications created or edited with this pack record the current skill-pack version as defined in `skill/layered-spec-core/references/skill-pack-versioning.md`.

## Primary Location


Store generated plans and active specs in this folder:

- `specs/`

Use this folder as the default planning and spec registry unless a narrower location is explicitly required by the task.

Use these locations:

- `specs/<simple-solution>.md` for a solution with no candidate evaluation;
- `specs/<solution-name>/spec.md` for a solution with task development artifacts;
- `specs/task-contexts/CTX-NNNN-<task-slug>.md` for reusable shared context assembled for one logical task;
- `specs/<solution-name>/candidates/<basis-name>.md` for focused basis candidates;
- `specs/<solution-name>/candidates/comparison.md` for the basis comparison;
- `specs/architecture/template.md` for the active repository ADR template;
- `specs/architecture/ADR-NNNN-<short-title>.md` for an architectural decision record.

`specs/spec-lifecycle/` contains specification-lifecycle policy rather than generated solution specifications. Do not classify files in that folder with solution-spec lifecycle states such as `active`, `partially outdated`, `superseded`, or `archived`.

`specs/architecture/` contains the active ADR template and architectural decision records rather than solution specifications. Exclude the directory from solution-spec lifecycle classification, and exclude `architecture/template.md` from ADR discovery. Keep this directory flat until a later architecture-organization decision introduces narrower subdirectories.

`specs/task-contexts/` contains task-scoped reusable context rather than solution specifications. Read `skill/layered-spec-core/references/task-context.md` for its file shape, stable identifiers, reuse boundary, and legacy compatibility rules. A task context is not an exclusive source or a certification that every artifact has sufficient context.

Existing `specs/<solution-name>/connected_context.md` files remain valid legacy evidence artifacts. Do not migrate them automatically. New task development uses task context when shared context is useful rather than creating another solution-local `connected_context.md`.

When an existing single-file solution spec needs candidate evaluation, move its full content to `<solution-name>/spec.md`, then leave a short compatibility pointer at the original path. Preserve the content before replacing the old file.

## Terms

- `task`: the request, problem, or desired change.
- `solution`: the intended response to a task; it can be a new capability, refactoring, compatibility slice, or broader application logic.
- `solution spec`: the planning artifact that describes a solution.
- `basis`: a technology, API, protocol, framework, algorithm, or approach that supplies composable workflow steps.
- `candidate`: a focused partial solution that evaluates one basis for one decision scope.
- `decision reach`: whether one selected concern is `solution-local` or `architectural`.
- `ADR`: the authoritative record for one architecturally significant selected concern and its rationale.
- `task context`: optional reusable directives, evidence, findings, affected-artifact mappings, and gaps collected for one logical task.
- `basis state`: whether a basis is `confirmed`, `proposed` for implementation-backed validation, or `deferred` without a justified working basis.


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

ADRs use their own status inside each record, such as `proposed`, `accepted`, or `superseded`. Do not apply solution-spec lifecycle states to ADRs. A proposed ADR is pending rather than an authoritative existing-system constraint. When an accepted decision changes, create a superseding ADR and preserve the earlier record.

## Required Top-Level Sections

Every non-trivial planning artifact should use these top-level sections in this order:

1. `Title and scope`
2. `Planning anchor`
3. `Connected groups or observed existing logic`
4. `Task development` when a material basis decision was evaluated
5. `Use cases`
6. `Implementation checklist`
7. `Open questions`
8. `Decision log`

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
- relevant ADRs under `specs/architecture/`, their status, and whether they constrain or may be superseded by the task
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
8. Governing architecture decisions

The `Specs` group should list:

- relevant files under `specs/`
- why each spec is connected to the planning anchor
- whether it remains authoritative or must be updated, marked outdated, or superseded

The `Governing architecture decisions` group should list:

- each relevant ADR and its status;
- the affected decision concern;
- how an accepted ADR constrains the task, or why changed evidence may require a superseding decision;
- the specifications that consume the decision.

When the task is local and full connected mapping is unnecessary, this section may instead contain `Observed Existing Logic` with focused notes only.

When task context is available, reuse its relevant directives, findings, and evidence and cite stable identifiers where provenance is useful. Supplement it with original or additional sources whenever this spec needs context that is absent, incomplete, ambiguous, stale, or artifact-specific. Keep information local here when it has no expected cross-artifact consumer. Write newly discovered information back to an in-scope task context only when it is useful to several artifacts or corrects shared understanding.

This section is written directly into the spec. Do not create an intermediate materialized context-view artifact. A task-context file is reusable input rather than a completeness boundary, so the artifact owner remains responsible for this section whether or not task context exists.

## Task development

Use `task development` in prose and `## Task development` as the section heading. Include it only when a solution has two or more reasonable bases whose selection materially changes workflow behavior, policy compliance, operational metrics, or architecture. It is not required when the basis is already fixed by task requirements, repository policy, or an authoritative existing-system contract.

Record each concern's basis state as:

- `confirmed`: available evidence supports selection and complete dependent use cases;
- `proposed`: one basis is justified as an implementation proposal, but implementation must produce evidence defined by stable validation requirements in the consuming spec;
- `deferred`: available evidence does not justify a working basis, so dependent use cases remain blocked while unrelated planning may continue.

Classify every selected concern independently as `solution-local` or `architectural` and assign it exactly one authoritative record. A composed basis set may contain concerns with different reach.

For a confirmed or proposed solution-local concern, the canonical solution spec records:

- decision scope and non-negotiable constraints;
- basis state, selected or proposed basis, and `solution-local` decision reach;
- that the current spec is authoritative;
- candidate and comparison artifact links;
- the use cases that consume the selected capabilities.

For a confirmed or proposed architectural concern, one ADR under `specs/architecture/` owns the context, drivers, considered bases, decision, consequences, evidence, and affected specs. `architecture-decision-recording` owns ADR creation and lifecycle; basis evaluation hands the concern to it instead of creating the ADR itself. A consuming spec records:

- decision scope and `architectural` reach;
- a relative link to the governing ADR;
- the candidate comparison link;
- only local application consequences or parameters;
- the use cases that consume the selected capabilities.

Do not duplicate one decision's rationale in its ADR and consuming specs. Split ownership only when the architectural concern and the solution-local concern are distinct; never create two authoritative copies of the same concern.

Candidate files are focused evaluation slices rather than complete specs. `solution-basis-evaluation` owns their workflow shape, comparison criteria, and migration procedure.

Candidate evaluation may select multiple compatible bases for different solution concerns. Use cases assemble selected capabilities from their authoritative local records or governing ADRs and do not silently reopen a recorded decision.

When a spec consumes a proposed basis, add stable basis-validation requirements to its owning `Requirements` layer and include their execution in the implementation checklist. State the evidence to produce, confirmation criteria, and reconsideration criteria. Basis-validation execution and result processing are separate follow-up work in this version; after implementation, ask the user whether required basis validation should be performed.

Do not create an ADR or selected-basis record for a deferred concern.

Task-development stages have these dependency constraints:

- `Solution-basis candidate development and comparison`: candidates and comparisons cite available evidence, including task-context identifiers when consumed. Task context is reusable input rather than a prerequisite or completeness guarantee.
- `Task-development summary`: the comparison is complete; every concern has a basis state and allowed planning scope; and every confirmed or proposed concern has a classified decision reach and authoritative local record or ADR handoff.
- `Use-case completion`: confirmed or proposed basis capabilities consumed by each use case are defined from their authoritative local record or governing ADR. Proposed-basis consumers include their validation requirements. Deferred-basis consumers remain blocked.
- `Dependent-stage completion`: outputs from every prerequisite stage are persisted and verified before the dependent stage is completed.

Do not present a deferred basis as selected or complete a use case that depends on it. Obtain context from all relevant available sources rather than treating task-context presence or absence as the completeness test.

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

### Requirements And Implementation Structure

Use the smallest use-case structure that preserves both the required behavior and the implementation logic:

1. Use one implementation use case with its workflow and `Logic` layers when they describe the behavior completely. Do not add `Requirements` or a declarative parent only for structural uniformity.
2. Add `Requirements` directly to the implementation use case when non-trivial conditions, invariant obligations, rejection rules, or required outcomes need an explicit normative definition but one implementation workflow remains coherent. The use case's workflow and logic implement its own requirements; do not add self-referential `Realized by` or `Realizes` mappings.
3. Introduce a declarative use case with separate realization mappings when the required behavior and its implementation decomposition each need an independently understandable structure, normally because several use cases jointly realize the behavior. Map the requirements through `Realized by`, and add the symmetric `Realizes` mapping to each realizing use case. A realizing use case may itself be declarative and may therefore contain `Realizes`, its own `Requirements`, and a further `Realized by` layer.

The `Requirements` layer may specify declarative behavior through EARS requirements, identified workflow chains, hierarchical contracts, or identified non-transition constraints. A hierarchical contract uses a parent requirement as its umbrella obligation and descendant requirement IDs as its clauses. Each requirement has a stable ID.

Hierarchical numbering expresses containment; it does not replace explicit realization mappings. When requirements belong to a separate declarative use case, that use case maps them through `Realized by`, and every realizing use case provides the symmetric `Realizes` mapping. A reusable framework use case remains separately identified; an implementation use case whose behavior relies on it references it through `Uses`.

For each requirement ID, the definition written directly in `Requirements` is authoritative. Optional duplicate or translated representations must reference that ID and preserve its meaning. The definition may be an EARS requirement, a workflow chain, a hierarchical contract entry or clause, or an identified non-transition constraint. EARS, Gherkin, RIDDL, or other representations also declare their format and semantic relation in `Requirement representations`; the contract does not require one scenario or translation syntax.

Read `skill/layered-spec-core/references/requirements-and-realization.md` when a specification uses a `Requirements` layer, separate declarative and realizing use cases, `Realized by`, `Realizes`, `Uses`, framework boundaries, or external requirement representations.

Read `skill/layered-spec-core/references/invariants.md` when a use case uses an `Invariants` layer to record invariants for selected states or derive later state invariants from earlier ones.

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
- `Invariants`
- `Logic Details`
- `Observed Existing Logic`
- `Input Validation And Contracts`
- `Tests`
- `Validation`
- `Use Case Questions`
- `Requirements`
- `Realized by`
- `Realizes`
- `Uses`
- `Requirement representations`

Use additional layer names only when they communicate a distinct responsibility clearly.

### Invariants Layer Syntax

Use `Invariants` when selected workflow states have meaningful invariants and the derivation of later state invariants should be explicit. It is a selective parallel chain over the main workflow and does not require an invariant for every state.

Keep a concise invariant outline in the layer, then place long invariant definitions, assumptions, calculations, proofs, and formal text in its detailed state-invariant and derivation entries. A derivation identifies its source invariant or invariants, target invariant or invariants, and the workflow transition or transition span that establishes the target.

Invariants and derivations may use natural language, mathematical notation, pseudocode, Lean, or another named formalism. Natural-language reasoning may be a proof, justification, or proof sketch. Call it a **verifiable proof** only when it is expressed in a formalism and successfully verified by the corresponding checker.

An invariant is not automatically a normative requirement. A requirement may reference an invariant owned by the same use case when satisfying that invariant is required. When an invariant belongs to a realizing use case, keep the owning requirement self-contained, retain the realization mappings, and let the invariant derivation identify the requirement it justifies.

Follow `skill/layered-spec-core/references/invariants.md` for the exact shape, identifiers, workflow mapping, proof terminology, requirement relationship, and technical-use-case boundary.

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

Put formulas primarily in `Execution Logic`, `Implementation Logic`, `Logic Details`, `Data`, or `Invariants`. Use inline KaTeX (`$...$`) for a short expression within a sentence and display KaTeX (`$$...$$`) for a standalone equation, derivation, or multi-line aligned expression.

Do not put KaTeX in workflow lines, transition labels, branch labels, or workflow-state names. Those chains must remain scannable state-to-state prose. Give the chain a concise semantic state or step name, then place the formula in the relevant detailed layer and refer to the named state or quantity there.

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
- `Invariants`

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
   requirements: optional requirement ids
   input: input description
   workflow: state 1 with given input --one or several steps--> final state 1
   expected outcome: expected output or exception description
```

Rules:

- The optional test file name line may be omitted.
- At least one of `description` or `workflow` must be present for each test entry.
- If `workflow` is present, `input` and `expected outcome` should usually be present as well.
- When a test verifies identified requirements, add their IDs to the test entry. A scenario or external representation does not replace its canonical requirement unless equivalent coverage is explicitly declared and validated.

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

When requirement mappings are present, retain the requirement IDs satisfied by each implementation task so checklist completion can be traced back to normative behavior.

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
- discovers relevant ADRs, preserves their lifecycle state, and references architectural rationale instead of duplicating it
- records every evaluated concern as confirmed, proposed, or deferred with exactly one allowed decision destination
- includes stable validation requirements when a spec consumes a proposed basis
- leaves deferred-basis-dependent use cases blocked without blocking unrelated planning
- treats task context as reusable shared evidence rather than a completeness boundary or exclusive source
- includes spec maintenance in the implementation checklist when relevant
- records code-to-spec traceability when implementation boundaries map cleanly to use-case workflow steps
- uses workflow operators consistently, including refactoring syntax when updating an existing implementation path
- uses KaTeX for scientific formulas only where it clarifies technical logic, data, or invariants, while keeping workflow chains and invariant outlines as readable prose
- uses `Invariants` only for meaningful workflow states, keeps its outline concise, and maps every derivation from identified source invariants through workflow logic to identified target invariants
- reserves **verifiable proof** for formal text successfully checked by its corresponding verifier
- uses hierarchical use-case numbering when parent and child use cases need distinct workflow treatment
- plans early validation and the post-validation contract when later workflow steps depend on stronger assumptions
- uses `Implementation Logic` only when algorithmic detail is needed beyond declarative workflow behavior, and uses `Implementation Logic Proposal` or omission when the implementation should stay developer-owned
- introduces non-trivial decompositions and intermediate algorithmic structures in the plan when implementation quality depends on them
- uses the smallest sufficient use-case structure and does not introduce a declarative parent when one implementation use case remains clear
- keeps non-trivial requirements on the owning implementation use case when separate declarative requirements and realizing use cases are unnecessary
- uses identified requirement entries and symmetric `Realized by` / `Realizes` mappings when required behavior and its realization both need separate structures
- permits a declarative realizing use case to contain `Realizes`, its own `Requirements`, and `Realized by`
- uses `Uses` to map implementation-use-case steps to referenced declarative or implementation use cases, including reusable framework boundaries
- keeps the definition under each requirement ID as the meaning that optional duplicate or translated representations must preserve
- checks that every requirement is implemented by its owning use case or is realized, explicitly deferred, or declared outside implementation ownership; every realization mapping is symmetric, and non-deferred declarative requirements eventually reach implementation coverage
- uses direct task-native wording in `Title and scope` and avoids abstract boilerplate
- groups `Title and scope` by conceptual subchange rather than raw edit order when multiple related changes are involved
- keeps `Title and scope` readable by using one compact lead sentence + an optional second sentence when detail is needed
