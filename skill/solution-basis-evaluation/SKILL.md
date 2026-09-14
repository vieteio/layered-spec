---
name: solution-basis-evaluation
description: "Use when: a non-trivial task has multiple reasonable technologies, APIs, protocols, frameworks, algorithms, or approaches whose choice materially changes workflow behavior, policy compliance, operational metrics, or architecture. Create focused candidates, compare them with explicit evidence, classify each concern as confirmed, proposed, or deferred, and persist solution-local decisions or hand architectural decisions to ADR recording. Do not use when the basis is already fixed by task requirements, policy, or an authoritative existing-system contract."
metadata:
  version: "0.2.3"
---
# Solution Basis Evaluation

Use this skill when a consequential solution choice remains open. It may run standalone or receive context and artifact constraints from an orchestrated planning workflow.

When this skill creates or edits a specification, follow `skill/layered-spec-core/references/skill-pack-versioning.md`.

## Locations And Inputs

- Simple solution spec: `specs/<solution-name>.md`
- Solution directory: `specs/<solution-name>/`
- Canonical solution spec after candidate evaluation: `specs/<solution-name>/spec.md`
- Optional task context: `specs/task-contexts/CTX-NNNN-<task-slug>.md`
- Candidate artifacts: `specs/<solution-name>/candidates/`
- Architecture directory: `specs/architecture/`
- Architectural decision records: `specs/architecture/ADR-NNNN-<short-title>.md`
- Shared planning contract: `planning/planning_contract.md`
- Task-context contract: `skill/layered-spec-core/references/task-context.md`
- Candidate artifact details: `references/candidate-artifacts.md`
- Existing-system evidence discovery: `skill/connected-code-mapping/SKILL.md` and `skill/code-logic-workflow-documentation/SKILL.md` when needed

Use `task development` in prose and `## Task development` in solution specs. Do not treat it as a proper-name phase.

## When Evaluation Is Needed

Evaluate bases only when all of these are true:

- two or more bases are reasonable under the known task and existing-system constraints;
- each basis supplies materially different atomic workflow steps, delivery semantics, operating behavior, or policy implications;
- the choice is not already fixed by an explicit requirement, repository policy, or authoritative platform contract;
- selecting one basis without comparison would leave a consequential assumption unexamined.

Do not manufacture alternatives. For example, do not evaluate a new transport when the task or existing public contract already requires a specific transport.

## Workflow

### 1. Establish The Evaluation Scope

Record the task outcome, non-negotiable rules, affected expectations, and existing-system constraints. Inspect relevant ADRs under `specs/architecture/`, excluding `template.md`, before proposing candidates.

Treat an applicable accepted ADR whose context remains valid as an authoritative constraint. Skip evaluation when it already fixes the basis. A proposed ADR is pending rather than authoritative. When new evidence invalidates an accepted ADR's context, evaluate a superseding decision instead of silently contradicting or rewriting the accepted record.

Use all relevant available context: the task, existing artifacts, code, tests, configuration, operational evidence, and authoritative documentation. When task context is available, reuse its candidate-relevant directives, findings, and supporting evidence, then inspect original or additional sources when the evaluation needs more. Task context is optional reusable input rather than a completeness guarantee.

When new information is useful to several artifacts or corrects shared understanding, write it back to an in-scope task context. Keep candidate-specific detail in the candidate or comparison. Treat observed constraints as evidence, not as an automatic choice of the current implementation. Do not require a task-context file for standalone evaluation.

### 2. Identify Reasonable Bases

For each candidate basis, state:

- the technology, API, protocol, framework, algorithm, or approach being evaluated;
- the atomic steps it contributes to a solution workflow;
- the task concern it addresses;
- the evidence that makes it reasonable;
- any known disqualifying condition.

Use a basis set when different concerns need different compatible bases. Do not force one global basis when the solution is intentionally composed from several selected bases.

### 3. Create Focused Candidate Artifacts

Create one `candidates/<basis-name>.md` file per reasonable basis. Read `references/candidate-artifacts.md` for the candidate workflow shape, permitted evaluation layers, and rules that keep candidates focused rather than complete solution specs.

### 4. Compare And Classify Basis State

Create `candidates/comparison.md` using the comparison shape and criteria rules in `references/candidate-artifacts.md`.

Classify each concern independently:

- `confirmed`: available evidence supports the basis selection;
- `proposed`: one basis is justified as an implementation proposal, but implementation must produce evidence defined by stable validation requirements;
- `deferred`: available evidence does not justify a working basis.

A proposed basis records its assumptions, required evidence, confirmation criteria, reconsideration criteria, and allowed consumers. A deferred concern has no selected basis and blocks only dependent planning.

### 5. Classify Decision Reach

For every confirmed or proposed concern, classify decision reach independently:

- `solution-local`: the selection is confined to the current solution and the use cases that implement it;
- `architectural`: the selection governs several specs or components, establishes a long-lived shared constraint, materially affects quality attributes, or is risky or expensive to reverse.

Assign exactly one authoritative record to each confirmed or proposed concern. A composed basis set may contain concerns with different reach. Do not use `both` as duplicate ownership: an ADR owns the shared architectural decision, while a consuming spec owns only distinct local application details or parameters. Do not classify decision reach or create a decision record for a deferred concern.

### 6. Persist Or Hand Off The Decision

For a confirmed or proposed solution-local concern, record the basis in the canonical `spec.md`:

````md
## Task development

- Decision scope: <concern evaluated>
- Basis state: `confirmed` or `proposed`
- Selected or proposed basis: <basis assigned to this concern>
- Decision reach: `solution-local`
- Authoritative record: this specification
- Candidate artifacts: `candidates/<basis-name>.md`
- Comparison: `candidates/comparison.md`
- Use-case handoff: <the use cases that now consume the selected capabilities>
- Basis-validation requirements: <stable requirement IDs when proposed, or none>
````

For a confirmed or proposed architectural concern, produce an ADR handoff containing:

- decision scope and basis state;
- selected or proposed basis;
- relevant context, drivers, task-context identifiers, and comparison link;
- affected and planned consuming specifications;
- proposed-basis validation requirement references when applicable.

`architecture-decision-recording` owns template resolution, ADR discovery and lifecycle, identifier allocation, creation, supersession, and consumer synchronization. This skill does not create or update ADRs itself. After an ADR has been recorded, a consuming spec uses:

````md
## Task development

- Decision scope: <concern evaluated>
- Basis state: `confirmed` or `proposed`
- Decision reach: `architectural`
- Governing ADR: `../architecture/ADR-NNNN-<short-title>.md`
- Comparison: `candidates/comparison.md`
- Local consequences: <only consequences or parameters owned by this specification>
- Use-case handoff: <the use cases that consume the selected capabilities>
- Basis-validation requirements: <stable requirement IDs when proposed, or none>
````

For a deferred concern, keep its questions and missing evidence authoritative in `comparison.md`; create no selected-basis record or ADR handoff. Preserve candidate and comparison artifacts as evidence.

Planning may consume confirmed bases completely. It may consume a proposed basis only with stable basis-validation requirements in the relevant spec. Those requirements state the evidence implementation must produce, confirmation criteria, and reconsideration criteria. Validation execution and result processing are outside this skill's current scope. A deferred concern blocks only dependent use cases.

## Existing Spec Migration

When an existing single-file solution spec needs candidate evaluation, follow the migration procedure in `references/candidate-artifacts.md`.

## Quality Checks

- Every candidate differs through an explicit basis and material workflow consequence.
- Candidate workflows are sufficient to discriminate the choice but are not full solution specs.
- Each comparison conclusion cites task rules, observed existing logic, measurement, or authoritative documentation.
- Each candidate and comparison finding cites available evidence, including task-context identifiers when consumed.
- The selected result may be a composed basis set, not only one winner.
- Every concern has one `confirmed`, `proposed`, or `deferred` basis state.
- Every confirmed or proposed concern has one `solution-local` or `architectural` reach and exactly one authoritative record or ADR handoff.
- Every proposed concern defines stable validation requirements and does not claim confirmation.
- Every deferred concern has no selected-basis record or ADR handoff and blocks only dependent planning.
- A canonical solution spec owns a local selection or references its governing ADR without duplicating architectural rationale.
- Use cases consume selected capabilities from their authoritative records and do not silently reopen a resolved comparison or ADR.
- Task context is reused when available but is never treated as an exclusive source or completeness guarantee.
- Standalone evaluation does not require a lifecycle workflow or task-context file.

## One-Line Heuristic

When a consequential solution choice is genuinely open, compare the smallest workflow slices that make the bases behave differently, classify each concern as confirmed, proposed, or deferred, and persist locally or hand architectural decisions to their ADR owner.
