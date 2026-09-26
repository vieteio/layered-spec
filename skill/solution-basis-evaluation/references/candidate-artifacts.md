# Candidate Artifacts

Use this reference when creating candidate and comparison artifacts for `solution-basis-evaluation`.

## Storage And Task Ownership

Read [task-context.md](../../layered-spec-core/references/task-context.md) for task-folder structure, identity, and naming. Candidate paths below are relative to `specs/task-contexts/<task-name>/`, not to a spec. Create `candidates/` only when evaluation is needed; standalone evaluation need not create `task_context.md`.

One task comparison may cover several concerns and serve several consuming specs. Give candidates distinct filenames within that task; include the concern in the filename when the basis name alone would collide. Link affected and planned specs explicitly and resolve every path relative to the document that contains it. Spec names and task names need not match.

## Candidate File Shape

Create one `candidates/<basis-name>.md` file per reasonable basis. A candidate is a focused evaluation slice, not a complete solution spec.

````md
# <Task title>: <Basis name> candidate

## Basis
- Basis: <technology, API, protocol, framework, algorithm, or approach>
- Decision scope: <solution concern>
- Atomic capabilities: <steps this basis contributes>
- Constraints and assumptions: <known facts>
- Consuming specifications: <relative links or planned spec paths>

## Candidate workflows

### 1. <Candidate use case>
initial state --basis-specific step--> resulting state

Delivery semantics:
- <ordering, replay, acknowledgement, or lifecycle behavior when relevant>

Operational metrics:
- <latency, throughput, resource, cost, or other task metric>

Policy and trust boundaries:
- <authorization, security, privacy, compliance, or ownership rule when relevant>

## Evaluation evidence
- <task-context identifier when consumed, observed code, authoritative documentation, measurement, or explicit task rule>

## Open questions
- <only evidence gaps that prevent a confident comparison>
````

Use named layers that expose the decision. Add `Tables`, `Files And Functions`, migrations, or full implementation plans only when they are necessary to compare the bases.

## Comparison File Shape

Create `candidates/comparison.md` with:

```md
# <Task title> candidate comparison

## Evaluation scope
- <decision scope and non-negotiable constraints>

## Criteria
- <task policy, user expectation, observable metric, or authority rule>

## Findings
### <Basis name>
- Evidence: <task-context identifier when consumed, citation, or observation>
- Result against criteria: <finding>

## Selection
### <Decision concern>
- Basis state: `confirmed`, `proposed`, or `deferred`
- Selected or proposed basis: <basis assigned to a confirmed or proposed concern; omit when deferred>
- Decision reach: `solution-local` or `architectural`; omit when deferred
- Authoritative record or handoff: <canonical spec, ADR path after recording, pending ADR handoff, or none when deferred>
- Consuming specifications: <paths or planned specifications>
- Rejected bases: <basis and evidence-backed reason>
- Deferred bases: <basis, missing evidence, and smallest validation or prototype>
- Proposed-basis assumptions: <required when proposed>
- Basis-validation requirements: <stable planned spec requirement IDs, evidence to produce, confirmation criteria, and reconsideration criteria when proposed>
- Allowed planning: <complete dependent planning, proposed-basis planning with validation requirements, or unrelated planning only>
```

Repeat the concern subsection when a composed basis set evaluates several concerns. Each confirmed or proposed concern has exactly one authoritative record: use an ADR for an architectural concern and the canonical solution spec for a solution-local concern. During basis evaluation, an architectural concern may temporarily record a pending ADR handoff; replace it with the ADR path after `architecture-decision-recording` completes. Do not record the same decision rationale in both places. A deferred concern has no authoritative decision record.

Use `proposed` only when one basis is justified and safe enough to implement for evidence. Use `deferred` when no working basis is justified or implementation merely to gather evidence would be unsafe or disproportionate. Basis-validation execution and result processing are outside this version's scope.

Compare efficiency, operating cost, delivery semantics, reliability, security, policy compliance, and task-specific rules when relevant. Implementation complexity is not a primary criterion. Record it only when it creates a concrete reliability, security, policy, or operational constraint.

## Spec Ownership

Basis evaluation does not change a spec's name or location. Store candidates and comparison in the logical task's workspace and link them from the affected spec as needed. Keep the selected local basis, relevant assumptions, local consequences, and validation requirements in the owning spec; the comparison is supporting evaluation, not the only description of the selected solution.
