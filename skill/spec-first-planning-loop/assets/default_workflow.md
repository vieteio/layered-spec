# Specification Lifecycle Workflow

## Workflow Chain

```text
task in chat
  --classify task and required planning route--> classified planning task
  --reverse-document existing behavior when necessary--> understood existing behavior
  --collect connected context when necessary--> grounded planning task
  --prepare layered technical use cases--> canonical solution spec
  --prepare implementation checklist--> reviewable solution spec with implementation checklist
| while the specification for a complicated or large-scale task has not been verified against that task:
  reviewable solution spec with implementation checklist or corrected solution spec
    --check specification completeness--> completeness-checked solution spec
    --check specification consistency--> task-accurate reviewable solution spec |
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
- Reviewable solution spec with implementation checklist, ready for verification against the task when applicable.

Record:
- Explicitly deferred implementation work and checklist status.
- Whether the verification loop was entered or skipped, and why.

Next:
- `Check specification completeness` when the task is complicated or large-scale.
- Otherwise, `Select the handoff`.

### Check specification completeness

Purpose:
- Verify that the generated or updated specification completely represents the solution established from the task and available planning context, without accidental omissions or scope drift.
- When a completeness finding cannot be resolved from the established planning context or a reasonable non-blocking assumption, record it in `Open questions`; pause and request user input only when correct planning cannot continue without the answer.

Run when:
- The specification was prepared for a complicated or large-scale task.
- Once the verification loop has started, keep it active until both checks have passed or the active check is awaiting required user input.

Skip when:
- Before the first iteration, skip the verification loop when the task is not complicated or large-scale.

Input:
- The task together with all planning context established for it before and during specification preparation.
- The generated or updated specification and its supporting planning artifacts.

Logic:

```text
| while the specification has not passed the completeness check:
  established task context and current specification set
    --compare the prepared specification with the established solution--> completeness findings
    --resolve findings from the established planning context--> updated or paused specification set |
```

1. Treat the task as the authority for the requested outcome and scope. Use the planning context established during earlier lifecycle steps to interpret and elaborate it.
2. Inspect the specification as a whole so content that should have been recognized as relevant is not missed.
3. Check that the prepared specification and implementation checklist preserve the established solution without accidental omissions or scope drift.
4. Reasonable non-blocking assumptions may be made and recorded when they preserve the requested outcome and are supported by the available context.
5. Correct a finding autonomously only when its resolution follows from the established planning context or a reasonable non-blocking assumption.
6. Do not introduce a new solution decision solely to make the specification pass the check.
7. When a finding cannot be resolved from the established planning context or a reasonable non-blocking assumption, record it in `Open questions`. Classify it as blocking only when continuing would require an unsupported solution decision.
8. Do not treat the completeness check as passed while a blocking completeness finding remains unresolved.

Request next user input:
- When blocking completeness findings remain, request the information needed to resolve them as one coherent question batch and keep this step active.
- Process the response into the affected planning artifacts and resume the completeness check.

Output:
- While awaiting required user input, the specification with unresolved blocking completeness findings recorded in `Open questions`.
- After resolution, a completeness-checked solution spec with synchronized supporting planning artifacts.
- After the check passes, a concise user-visible chat summary of the inaccuracies corrected. If nothing changed, state that the check passed without changes.

Record:
- Completeness findings and their disposition.

Next:
- `Check specification consistency`.

### Check specification consistency

Purpose:
- Verify that the specification as a whole consistently expresses the solution established during specification preparation.
- When a consistency finding cannot be resolved from the established planning context or a reasonable non-blocking assumption, record it in `Open questions`; pause and request user input only when correct planning cannot continue without the answer.

Run when:
- `Check specification completeness` completed in the current check-loop iteration.

Input:
- The task together with all planning context established for it before and during specification preparation.
- The completeness-checked specification and its supporting planning artifacts.

Logic:

```text
| while the specification has not passed the consistency check:
  established task context and completeness-checked specification set
    --compare the specification with the established solution--> consistency findings
    --resolve findings from the established planning context--> updated or paused specification set |
```

1. Inspect the specification as a whole rather than limiting the check to content already identified as task-affected.
2. Treat a finding as relevant only when it prevents the specification from accurately expressing the established solution.
3. Preserve reasonable non-blocking assumptions that remain supported by the available context.
4. Correct a finding autonomously only when its resolution follows from the established planning context or a reasonable non-blocking assumption, and synchronize every affected planning artifact.
5. Do not introduce a new solution decision solely to make the specification pass the check.
6. When a finding cannot be resolved from the established planning context or a reasonable non-blocking assumption, record it in `Open questions`. Classify it as blocking only when continuing would require an unsupported solution decision.
7. Do not expand the task to resolve unrelated pre-existing issues.
8. Do not treat the consistency check as passed while a blocking consistency finding remains unresolved.

Request next user input:
- When blocking consistency findings remain, request the information needed to resolve them as one coherent question batch and keep this step active.
- Process the response into every affected artifact and resume the consistency check.

Output:
- While awaiting required user input, the specification with unresolved blocking consistency findings recorded in `Open questions`.
- After resolution, a task-accurate reviewable solution spec with synchronized supporting planning artifacts.
- After the check passes, a concise user-visible chat summary of the inaccuracies corrected. If nothing changed, state that the check passed without changes.

Record:
- Consistency findings and their disposition.

Next:
- `Check specification completeness` when resolving a consistency finding changed specification content.
- Otherwise, `Select the handoff`.

### Select the handoff

Purpose:
- Decide whether to stop for specification review or enter implementation using the task's readiness and the conversation-local implementation flow.

Input:
- Reviewable solution spec after the verification loop was skipped or completed.
- The user's current task request.
- Any unresolved questions or material planning decisions.

Conversation state:
- `implementation flow`: starts `inactive` in a new conversation, becomes `active` when the user's current task request authorizes implementation or when the user later authorizes implementation of a prepared specification, remains active across later lifecycle tasks, and becomes `inactive` when the user requests that automatic implementation stop.

Logic:
Support the user's work as a flow. In a new conversation, prepare the first specification without implementation unless the user's request already requires an implementation change. The first implementation authorization activates the flow. While the flow is active, later narrow and unambiguous tasks may proceed from specification update to implementation without separate confirmation.

1. Honor the requested outcome. A request requiring an implementation change authorizes implementation; a request limited to specification preparation or review does not.
2. When implementation is not authorized and the flow is inactive, stop after preparing the specification and request an implementation decision. A later decision resumes from the same specification and checklist.
3. When implementation is authorized while the flow is inactive, activate the flow, notify the user about its conversation scope and stopping condition, and continue after any required user input has been processed.
4. While the flow is active, a later task that does not request implementation directly may proceed automatically when the task and resulting specification are narrow and unambiguous, no blocking question remains, and the user has not limited the requested outcome to specification work. Otherwise, stop with the specification ready for review without deactivating the flow unless the user requests that it stop.
5. Whether the verification loop ran or was skipped does not itself authorize or prevent implementation.

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
