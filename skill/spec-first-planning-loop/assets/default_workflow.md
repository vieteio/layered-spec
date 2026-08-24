# Specification Lifecycle Workflow

## Workflow Chain

```text
task in chat
  --classify task and required planning route--> classified planning task
  --reverse-document existing behavior when necessary--> understood existing behavior
  --collect connected context when necessary--> grounded planning task
  --prepare layered technical use cases--> canonical solution spec
  --prepare implementation checklist--> solution spec with implementation checklist
| while the specification has not passed both checks:
  solution spec with implementation checklist or corrected solution spec
    --check specification completeness--> completeness-checked solution spec
    --check specification consistency--> reviewable solution spec |
  --select handoff-->
[
  stop with the spec ready for user review,
  implement now or after a later user request
    --implement the plan in a loop--> implemented and synchronized solution spec
]
```

## Detailed Steps

### Classify the task

Purpose:
- Determine the planning route, context needs, and related-spec scope so later steps start from explicit state.

Input:
- User request and conversation-local decisions.
- Repository instructions and relevant existing planning artifacts.

Logic:
1. Classify the request as trivial/local, mostly new non-trivial behavior, a refactoring, or a compatibility/migration slice.
2. Decide whether existing runtime behavior needs reverse documentation.
3. Decide whether connected-code mapping is required.
4. Identify related solution specs and preliminary actions: `reuse`, `amend`, `mark outdated`, `replace`, or `archive`.
5. Exclude `specs/spec-lifecycle/` from solution-spec discovery and lifecycle classification.

Output:
- Classified planning task with a planning anchor, context needs, and related-spec actions.

Record:
- Meaningful scope assumptions and preliminary related-spec actions.

Next:
- `Reverse-document existing behavior`.

### Reverse-document existing behavior

Purpose:
- Make uncertain existing behavior explicit enough to ground connected mapping and planning without presenting observations as planned behavior.

Run when:
- Existing runtime behavior cannot be described reliably enough from current specs and focused code inspection.

Skip when:
- Existing behavior is already clear enough to support connected mapping and planning.

Input:
- Classified planning task.
- Concrete runtime entrypoint or code path.

Skill:
- `code-logic-workflow-documentation`

Output:
- Standalone observed workflow context or an observed-logic section suitable for connected mapping.

Record:
- The reason for skipping when reverse documentation is unnecessary.

Next:
- `Collect connected context`.

### Collect connected context

Purpose:
- Trace the change across connected responsibilities so later decisions and specifications use evidence and do not omit affected surfaces.

Run when:
- The task is non-local, crosses ownership boundaries, or changes shared state or data shape.

Skip when:
- Focused observed logic is sufficient for a local technical-use-case spec.

Input:
- Classified planning task.
- Reverse-documented behavior when produced.
- Relevant existing specs.

Skill:
- `connected-code-mapping`

Output:
- Connected context in the canonical solution spec.

Record:
- Mapped responsibility groups, evidence, related-spec actions, compatibility strategy, validation path, and explicitly deferred surfaces.
- The reason for skipping when focused observed logic is sufficient.

Next:
- `Prepare technical use cases`.

### Prepare technical use cases

Purpose:
- Turn the grounded task into the canonical technical specification for the planned slice.

Input:
- Grounded planning task.
- Relevant existing specifications and connected context.

Skill:
- `layered-workflow-planning`

Output:
- Canonical solution spec with planning anchor, connected or observed logic, and complete technical use cases for the planned slice.

Record:
- Implementation-owned assumptions, local use-case questions, and affected-spec lifecycle decisions.

Next:
- `Prepare the implementation checklist`.

### Prepare the implementation checklist

Purpose:
- Translate the canonical solution spec into dependency-ordered, status-bearing implementation work that includes applicable maintenance, validation, and explicit deferrals.

Run when:
- The solution spec is intended to drive implementation.

Skip when:
- The requested artifact is intentionally limited to technical analysis without implementation planning.

Input:
- Canonical solution spec and related artifacts.

Logic:
1. Create a numbered status-bearing checklist in dependency order.
2. Include spec maintenance, shared state or helpers, runtime path, propagation, validation, and cleanup when those responsibilities apply.
3. Keep deferred work explicit rather than silently omitting it.
4. Add `Input`, `Outcome`, `Logic`, `External state`, `Config parameters`, and `Metrics` when a checklist task needs execution detail.
5. Keep current status markers accurate.

Output:
- Solution spec with implementation checklist awaiting completeness and consistency checks.

Record:
- Explicitly deferred implementation work and checklist status.

Next:
- `Check specification completeness`.

### Check specification completeness

Purpose:
- Ensure the solution specification and its supporting planning artifacts cover the task's required scope, applicable lifecycle outputs, and implementation work without silent omissions.
- If required missing content cannot be derived safely, request and process user input before completing the check.

Input:
- Solution spec with implementation checklist or corrected solution spec.
- User request and recorded decisions.
- Supporting connected-context artifacts produced by earlier steps.
- Planning contract and the recorded run or skip decisions for earlier lifecycle steps.

Logic:

```text
| while the specification has not passed the completeness check:
  current specification and supporting planning artifacts
    --compare required scope with represented workflows, contracts, decisions, and checklist--> completeness findings
    --resolve derivable omissions and record explicit exclusions or deferrals--> updated specification set |
```

1. Check that every applicable earlier lifecycle output is present in the correct artifact or has an explicit valid skip reason.
2. Check that the requested behavior, relevant states and branches, technical use cases, implementation checklist, open questions, and related-spec actions are represented where applicable.
3. Check that each implementation responsibility implied by the specification is covered by the checklist or explicitly deferred.
4. Treat an explicit exclusion or deferral as complete only when its scope and reason are recorded and it does not contradict the user's required outcome.
5. Resolve omissions from available evidence. Do not invent required behavior merely to make the check pass.

Request next user input:
- Request the information or decision needed when an unresolved completeness finding cannot be resolved safely from the available task and repository context.
- Process the response into the affected planning artifacts and resume the completeness check.

Output:
- Completeness-checked solution spec and synchronized supporting planning artifacts, with no unresolved completeness findings for the current scope.

Record:
- Material omissions that were resolved, explicit exclusions or deferrals, and user decisions required by the check.

Next:
- `Check specification consistency`.

### Check specification consistency

Purpose:
- Ensure the complete specification set expresses one compatible solution across the task requirements, recorded decisions, workflow states, artifact mappings, implementation checklist, and affected specifications.
- If conflicting authoritative inputs cannot be reconciled safely, request and process user input before completing the check.

Input:
- Completeness-checked solution spec.
- Supporting planning artifacts and related specifications.
- User request, repository rules, and recorded decisions.

Logic:

```text
| while the specification has not passed the consistency check:
  completeness-checked specification set
    --compare shared concepts, transitions, contracts, mappings, and decisions--> consistency findings
    --resolve contradictions and synchronize affected artifacts--> updated specification set |
```

1. Compare repeated or connected concepts across the task language, planning anchor, connected context, technical use cases, checklist, open questions, decision log, and affected related specs.
2. Check state and transition compatibility, terminology, scope, ownership, ordering, mappings, data and API contracts, assumptions, deferrals, and completion status where applicable.
3. Distinguish an intentional planned change from a contradiction with observed existing behavior.
4. Resolve findings using the user request, explicit user decisions, and repository rules as authorities. Do not silently choose between conflicting authoritative inputs.
5. Synchronize every artifact affected by a correction rather than repairing only the location where the inconsistency was discovered.

Request next user input:
- Request the decision needed when authoritative inputs conflict or more than one materially different correction remains valid.
- Process the response into every affected artifact and resume the consistency check.

Output:
- Complete and consistent reviewable solution spec with synchronized supporting planning artifacts.

Record:
- Material inconsistencies that were resolved, the authority used for each non-obvious correction, and user decisions required by the check.

Next:
- `Check specification completeness` when resolving a consistency finding changed specification content.
- Otherwise, `Select the handoff`.

### Select the handoff

Purpose:
- Choose whether to stop with a reviewable specification or enter authorized implementation without discarding the current specification state.

Input:
- Reviewable solution spec.
- The user's current instruction about implementation.

Logic:
1. Stop with the spec ready for review when the user requested planning only or has not authorized implementation.
2. Continue to implementation when the user requested immediate implementation or later explicitly asks to implement the reviewed spec.
3. Do not enter `Implement the plan` or start non-trivial implementation until this step has established user authorization.
4. A later implementation request resumes from the same canonical spec and checklist.

Output:
- Terminal `spec ready for user review`, or authorization to enter the implementation loop.

Next:
- Terminal, or `Implement the plan`.

### Implement the plan

Purpose:
- Implement and verify every authorized implementation-checklist item while keeping affected specifications synchronized.
- If correct progress is blocked, request user input with one coherent batch of blocking questions.

Run when:
- The user has authorized implementation of the reviewable solution spec.

Input:
- Canonical solution spec and implementation checklist.
- Related connected-context artifacts.
- Current repository state.

Logic:

```text
| while unfinished implementation checklist items remain:
  current spec, repository, and checklist
    --select the next dependency-ready task--> selected implementation task
    --classify affected planning artifacts--> task with synchronization scope
    --implement the task--> updated repository
    --run focused and required validation--> verified implementation task
    --synchronize affected specs, decisions, and checklist-->
  current spec, repository, and checklist |
```

- Select the next dependency-ready checklist task without offering arbitrary alternatives.
- Ensure implementation matches the technical-use-case contracts.
- Run focused tests and required broader validation. Use browser-based manual verification when UI behavior requires it.
- Do not mark implementation complete while affected specs or checklist statuses are stale.

Request next user input:
- When correct implementation cannot continue without resolving one or more blocking decisions, request one coherent batch of blocking questions, including related plan-extension decisions.
- Do not request input for non-blocking uncertainties.
- Process the response as decisions for continuing the unfinished implementation-checklist items, then resume the implementation loop.

Output:
- Implemented and verified solution with synchronized planning artifacts.

Record:
- Validation evidence, implementation decisions, affected-spec status changes, and completed checklist tasks.

Next:
- Terminal `implemented and synchronized solution spec`.
