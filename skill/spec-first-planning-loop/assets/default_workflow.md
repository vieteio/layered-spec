# Specification Lifecycle Workflow

## Workflow Chain

```text
task in chat
  --classify task and required planning route--> classified planning task
  --reverse-document existing behavior when necessary--> understood existing behavior
  --collect connected context when necessary--> grounded planning task
  --prepare layered technical use cases--> canonical solution spec
  --prepare implementation checklist--> reviewable solution spec with implementation checklist
| while completeness and consistency checks are needed and the specification has not passed both checks:
  reviewable solution spec with implementation checklist or corrected solution spec
    --check specification completeness--> completeness-checked solution spec
    --check specification consistency--> reviewable solution spec |
  --select handoff-->
[
  implementation is authorized
    --implement the plan in a loop--> implemented and synchronized solution spec,
  implementation requires confirmation
    --present the prepared specification and ask whether to implement it--> spec ready for user review
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
- Reviewable solution spec with implementation checklist, ready for the optional completeness and consistency loop.

Record:
- Explicitly deferred implementation work and checklist status.
- Whether the optional check loop was entered or skipped, and why.

Next:
- `Check specification completeness` when the check-loop condition applies.
- Otherwise, `Select the handoff`.

### Check specification completeness

Purpose:
- Ensure the solution specification and its supporting planning artifacts cover the task's required scope, applicable lifecycle outputs, and implementation work without silent omissions.
- If required missing content cannot be derived safely, request and process user input before completing the check.

Run when:
- Before the first iteration, run the check loop when one or more of these conditions apply:
  - the task was described partially and material behavior was developed while preparing the specification;
  - the specification contains material assumptions or non-obvious design decisions;
  - several workflows, branches, responsibilities, contracts, or planning artifacts must agree;
  - omissions or contradictions remain plausible;
  - the user explicitly requested the checks.
- Once the loop has started, keep it active until both checks have passed.

Skip when:
- Before the first iteration, skip the entire check loop when the task and result are narrow and unambiguous, the specification contains no material inference, the checklist follows directly from it, and no meaningful cross-artifact reconciliation is required.

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
    --resolve directly implied omissions or record blocking open questions--> updated or paused specification set |
```

1. Check that every applicable earlier lifecycle output is present in the correct artifact or has an explicit valid skip reason.
2. Check that the requested behavior, relevant states and branches, technical use cases, implementation checklist, open questions, and related-spec actions are represented where applicable.
3. Check that each implementation responsibility implied by the specification is covered by the checklist or explicitly deferred.
4. Treat an explicit exclusion or deferral as complete only when its scope and reason are recorded and it does not contradict the user's required outcome.
5. Correct an omission autonomously only when a single, straightforward correction is directly implied by the user request and authoritative planning context, preserves their meaning, and introduces no material behavior or design decision.
6. Treat missing representation of behavior already determined by authoritative context as correctable. Treat missing behavior whose meaning must be decided as unresolved.
7. When user judgment is required, stop developing the correction and record the finding as a blocking question in `Open questions`. State what is missing, why the available authorities do not determine the correction, and which artifacts or behavior the answer will affect. Do not develop speculative alternatives beyond what is needed to make the question understandable.
8. Do not treat the completeness check as passed while such questions remain unresolved.

Request next user input:
- Before requesting input, write every unresolved completeness finding that requires user judgment as a blocking question in `Open questions` and keep this step active.
- Request the information or decisions needed as one coherent question batch.
- Process the response into the affected planning artifacts and resume the completeness check.

Output:
- While awaiting required user input, the specification with unresolved completeness findings recorded as blocking open questions.
- After resolution, a completeness-checked solution spec and synchronized supporting planning artifacts, with no unresolved completeness findings for the current scope.
- After the check passes, a concise user-visible chat summary of what the check added or changed, including material omissions resolved and explicit exclusions or deferrals. If nothing changed, state that the check passed without changes.

Record:
- Material omissions that were resolved, explicit exclusions or deferrals, unresolved findings recorded as blocking questions, and user decisions required by the check.

Next:
- `Check specification consistency`.

### Check specification consistency

Purpose:
- Ensure the complete specification set expresses one compatible solution across the task requirements, recorded decisions, workflow states, artifact mappings, implementation checklist, and affected specifications.
- If conflicting authoritative inputs cannot be reconciled safely, request and process user input before completing the check.

Run when:
- `Check specification completeness` completed in the current check-loop iteration.

Input:
- Completeness-checked solution spec.
- Supporting planning artifacts and related specifications.
- User request, repository rules, and recorded decisions.

Logic:

```text
| while the specification has not passed the consistency check:
  completeness-checked specification set
    --compare shared concepts, transitions, contracts, mappings, and decisions--> consistency findings
    --apply authority-determined corrections or record blocking open questions--> updated or paused specification set |
```

1. Compare repeated or connected concepts across the task language, planning anchor, connected context, technical use cases, checklist, open questions, decision log, and affected related specs.
2. Check state and transition compatibility, terminology, scope, ownership, ordering, mappings, data and API contracts, assumptions, deferrals, and completion status where applicable.
3. Distinguish an intentional planned change from a contradiction with observed existing behavior.
4. Correct an inconsistency autonomously only when a single, straightforward correction is directly implied by the user request and authoritative planning context, preserves their meaning, and introduces no material behavior or design decision.
5. Treat mechanical synchronization to one clear authority as correctable. Treat conflicts between authoritative inputs or multiple materially different valid corrections as unresolved.
6. When user judgment is required, stop developing the correction and record the finding as a blocking question in `Open questions`. State what conflicts, why the available authorities do not determine the correction, and which artifacts or behavior the answer will affect. Do not develop speculative alternatives beyond what is needed to make the question understandable.
7. Synchronize every artifact affected by an authority-determined correction rather than repairing only the location where the inconsistency was discovered.
8. Do not treat the consistency check as passed while such questions remain unresolved.

Request next user input:
- Before requesting input, write every unresolved consistency finding that requires user judgment as a blocking question in `Open questions` and keep this step active.
- Request the required decisions as one coherent question batch.
- Process the response into every affected artifact and resume the consistency check.

Output:
- While awaiting required user input, the specification with unresolved consistency findings recorded as blocking open questions.
- After resolution, a complete and consistent reviewable solution spec with synchronized supporting planning artifacts.
- After the check passes, a concise user-visible chat summary of what the check changed or synchronized, including material contradictions resolved and the affected artifacts or sections. If nothing changed, state that the check passed without changes.

Record:
- Material inconsistencies that were resolved, the authority used for each non-obvious correction, unresolved findings recorded as blocking questions, and user decisions required by the check.

Next:
- `Check specification completeness` when resolving a consistency finding changed specification content.
- Otherwise, `Select the handoff`.

### Select the handoff

Purpose:
- Decide whether to stop for specification review or enter implementation using the task's readiness and the conversation-local implementation flow.

Input:
- Reviewable solution spec after the optional check loop was skipped or completed.
- The user's current task request.
- Any unresolved questions or material planning decisions.

Conversation state:
- `implementation flow`: starts `inactive` in a new conversation, becomes `active` when the user's current task request authorizes implementation or when the user later authorizes implementation of a prepared specification, remains active across later lifecycle tasks, and becomes `inactive` when the user requests that automatic implementation stop.

Logic:
Support the user's work as a flow. In a new conversation, prepare the first specification without implementation unless the user's request already requires an implementation change. The first implementation authorization activates the flow. While the flow is active, later narrow and unambiguous tasks may proceed from specification update to implementation without separate confirmation.

1. Honor the requested outcome. A request requiring an implementation change authorizes implementation; a request limited to specification preparation or review does not.
2. When implementation is not authorized and the flow is inactive, stop after preparing the specification and request an implementation decision. A later decision resumes from the same specification and checklist.
3. When implementation is authorized while the flow is inactive, activate the flow, notify the user about its conversation scope and stopping condition, and continue after any required user input has been processed.
4. While the flow is active, proceed directly to implementation when the task and resulting specification are narrow and unambiguous, the check loop was skipped, and no material question remains. Otherwise, stop with the specification ready for review without deactivating the flow unless the user requests that it stop.

Request next user input:
- When implementation requires confirmation, present the prepared specification and ask whether the user wants to proceed with its implementation.
- Do not request this decision when the current task request already authorizes implementation or explicitly limits the outcome to specification preparation or review.
- Make the requested decision clear and treat any unambiguous implementation authorization as confirmation, regardless of its wording.
- Keep this step available for a later response. When the response authorizes implementation, process it as input for this handoff, update the conversation state, and continue according to the logic above.

Output:
- Terminal `spec ready for user review`, or authorization to enter the implementation loop.
- When this handoff activates the implementation flow, a user-visible notification that the flow is active, including its conversation scope and stopping condition.

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
