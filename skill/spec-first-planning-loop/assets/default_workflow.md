# Specification Lifecycle Workflow

- Default workflow version: `0.2.3`

## Workflow Chain

```text
task in chat
  --classify task and affected planning artifacts--> classified planning task
  --build shared task context--> context-enriched planning task
  --evaluate solution basis when needed-->
[
  basis fixed or no material alternatives
    --record why comparison is skipped--> confirmed basis handoff,
  materially different reasonable bases exist
    --develop focused candidates--> solution-basis candidates
    --compare candidates using available evidence, including task-context evidence--> solution-basis comparison
    --classify selection maturity-->
    [
      available evidence supports the selection
        --record confirmed basis--> confirmed basis handoff,
      one basis is suitable for implementation but requires implementation evidence
        --record proposed basis and its validation requirements--> proposed basis handoff,
      available evidence does not justify an implementation basis
        --record classified questions and deferred concerns--> deferred basis handoff
    ]
]
  --resolve applicable architecture decisions within the allowed basis handoff--> architecture-aware planning task
  --prepare layered use cases within the allowed decision handoffs--> canonical planning artifact set
  --prepare implementation checklist when implementation is planned--> reviewable planning artifact set
| while the planning artifact set has not been verified against the task and all relevant available context:
  reviewable planning artifact set or corrected planning artifact set
    --check completeness against the task and all relevant available context--> completeness-checked planning artifact set
    --check cross-artifact consistency and evidence references--> task-accurate reviewable planning artifact set |
  --select handoff-->
[
  implementation is authorized
    --implement the plan and synchronize code and planning artifacts--> implemented and synchronized planning artifact set,
  implementation requires confirmation
    --present the prepared artifacts and ask whether to implement them--> planning artifacts ready for user review
]
```

## Detailed Steps

### Classify the task

Purpose:
- Determine the planning route, required artifact levels, context and basis needs, and related-spec scope so later steps start from explicit state.

Input:
- User request and conversation-local decisions.
- Repository instructions and relevant existing planning artifacts.

Logic:
1. Classify the request as trivial/local, mostly new non-trivial behavior, a refactoring, or a compatibility/migration slice.
2. Classify the affected planning artifacts as task context, ADR, spec, or a combination.
3. Decide whether focused code inspection, connected-code mapping, or durable reverse documentation may contribute useful shared context.
4. Detect whether materially different reasonable solution bases may exist; do not select a basis before decision-relevant evidence is collected.
5. Identify related solution specs and preliminary actions: `reuse`, `amend`, `mark outdated`, `replace`, or `archive`.
6. Identify relevant ADRs under `specs/architecture/`, their status, and whether they constrain or may be superseded by the task.
7. Exclude `specs/spec-lifecycle/`, `specs/architecture/`, and `specs/task-contexts/` from solution-spec discovery and lifecycle classification. Exclude `architecture/template.md` from ADR discovery.

Output:
- Classified planning task with a planning anchor, affected artifact kinds, context needs, possible basis-decision scope, and related-spec actions.

Record:
- Meaningful scope assumptions and preliminary related-spec actions.

Next:
- `Build task context`.

### Build task context

Purpose:
- Create or resume reusable shared context for the logical task so later artifacts can reuse common directives, evidence, findings, and affected-artifact mappings.
- Completing this step does not certify that every artifact has sufficient context; each artifact-producing skill remains responsible for additional investigation needed by its output.

Input:
- Classified planning task.
- Current user request and relevant conversation clarifications.
- Repository instructions and existing task context when the logical task is being resumed.
- Potentially related ADRs, specs, source files, tests, configuration, and external evidence.

Logic:
1. Read `../../skill/layered-spec-core/references/task-context.md` completely.
2. Create a task-context file for a new logical task or resume the existing file for a continuation. Seed it with the outcome, scope, task directives and their authority, known sources, preliminary affected artifacts, and open concerns; do not create an empty placeholder.
3. Inspect related planning artifacts, repository rules, and focused code entry points. Add reusable evidence with stable identifiers and provenance.
4. When shared understanding requires tracing a non-local change across ownership, dataflow, persistence, propagation, or validation responsibilities, read and use `connected-code-mapping`. Contribute the reusable evidence, artifact-neutral findings, concern relationships, and affected-surface map to task context.
5. When an important existing workflow is insufficiently documented and durable documentation would simplify later work, read and use `code-logic-workflow-documentation`. Create or update the observed workflow documentation, link it from task context, and extract reusable evidence and findings. Record small observations directly instead of creating unnecessary durable documentation.
6. Synthesize artifact-neutral findings that connect directives and evidence to architectural, implementation, validation, or unresolved concerns. Record their derivations and potential consumers.
7. Repeat focused inspection, connected mapping, reverse documentation, and synthesis while additional shared context is useful for known downstream work. Record remaining gaps for the artifact owner that can resolve them.
8. Record the current revision, affected artifacts, gaps, and expected consumers. Keep artifact-specific details out of shared context when no other consumer is expected.

Output:
- An active reusable task context under `specs/task-contexts/`.
- Optional observed workflow documentation when durable reverse documentation was useful.
- A context-enriched planning task; not a completeness certification for later artifacts.

Record:
- Task directives and authority, evidence and provenance, artifact-neutral findings and derivations, related artifacts and actions, relevant ADR status, material gaps and conflicts, and explicitly deferred shared investigation.
- The reason connected mapping or durable reverse documentation was unnecessary when that distinction is material.

Next:
- `Evaluate solution basis`.

### Evaluate solution basis

Purpose:
- Produce the strongest evidence-backed basis state for each concern before dependent use cases are prepared: confirmed, proposed for implementation-backed validation, or deferred without a justified working basis; or record why comparison is unnecessary.

Run when:
- Two or more reasonable technologies, APIs, protocols, frameworks, algorithms, or approaches materially change workflow behavior, policy compliance, operational metrics, or architecture.

Skip when:
- An explicit requirement, repository policy, authoritative contract, or applicable accepted ADR whose context remains valid fixes the basis; or no materially different reasonable alternatives exist.

Input:
- Task outcome and non-negotiable constraints.
- Task context when available and all other relevant evidence needed by the comparison.

Skill:
- `solution-basis-evaluation`

Output:
- Candidate and comparison artifacts with `confirmed`, `proposed`, or `deferred` basis state per concern.
- For each confirmed or proposed concern, a decision reach and either an authoritative solution-local record or an architectural decision handoff.
- For each proposed concern, stable planned spec requirements defining validation evidence, confirmation criteria, and reconsideration criteria.
- For each deferred concern, no selected basis or decision record and a blocker limited to dependent planning.
- Confirmed basis handoff with an explicit skip reason when evaluation does not run.

Record:
- Decision scope, basis state, selected or proposed basis when present, rejected and deferred bases, evidence, assumptions, validation requirements, decision reach and local record or architectural handoff, allowed consumers, or explicit skip reason.

Next:
- `Resolve architecture decisions`.

### Resolve architecture decisions

Purpose:
- Apply an existing architecture decision or create, update, or supersede the one ADR that authoritatively owns each architectural concern permitted by the basis handoff.
- Leave a deferred architectural concern unresolved without inventing an ADR.

Run when:
- The task contains a direct architectural decision, changes an accepted decision, produces a confirmed or proposed architectural basis, or needs an existing ADR applied or synchronized.

Skip when:
- No architectural concern or affected ADR is relevant.

Input:
- Original task and relevant conversation decisions.
- Task context when available and any additional ADR-specific sources.
- Existing ADRs and affected or planned specifications.
- Confirmed, proposed, or deferred basis handoff when evaluation ran.

Skill:
- `architecture-decision-recording`

Output:
- Applicable governing ADR references, newly proposed ADRs, synchronized non-decision metadata, superseding ADRs, or an explicit unresolved result for deferred architectural concerns.

Record:
- ADR operation and authority, status, relevant context and evidence references, basis comparison when applicable, affected specifications, supersession links, or reason no ADR was created.

Next:
- `Prepare use cases`.

### Prepare use cases

Purpose:
- Produce or update the canonical solution specification from all relevant available context using the smallest use-case structure that preserves required behavior and implementation logic.
- Reuse shared context when available without treating it as complete or exclusive.

Run when:
- The task requires application-owned state transitions, validation, persistence, APIs, events, implementation logic, or another workflow-bearing section.

Skip when:
- The requested artifact intentionally stops at task context, basis evaluation, or an ADR without use-case planning.

Input:
- Original task and relevant conversation decisions.
- Task context when available, plus original or additional sources required for this artifact.
- Confirmed, proposed, or deferred basis handoff and applicable governing or proposed ADRs.

Skill:
- `layered-workflow-planning`

Output:
- Canonical solution spec with planning anchor, connected or observed logic, task-development handoff when applicable, governing ADR references without duplicated rationale, and use cases in the smallest sufficient form: implementation workflow and logic alone, implementation with owned requirements, or declarative requirements mapped to separate implementation use cases.
- Complete dependent use cases for confirmed concerns; use cases with stable basis-validation requirements for proposed concerns; scoped blockers instead of completed dependent use cases for deferred concerns; and unrelated planning allowed to continue.
- Updated task context only when newly discovered information is useful across artifacts or corrects existing shared understanding.

Record:
- Selected use-case structure and its reason when requirements or separate realization mappings are introduced; requirement-to-realization mappings when applicable; basis state and validation-requirement references; implementation-owned assumptions; artifact-local context and questions; shared findings written back when useful; and affected-spec lifecycle decisions.

Next:
- `Prepare the implementation checklist`.

### Prepare the implementation checklist

Purpose:
- Translate the canonical solution spec into dependency-ordered, status-bearing implementation work that includes applicable maintenance, validation, and explicit deferrals.

Run when:
- The solution spec is intended to drive implementation.

Skip when:
- The requested artifact is intentionally limited to analysis or decision recording without implementation planning.

Input:
- Canonical solution spec and related artifacts.

Logic:
1. Create a numbered status-bearing checklist in dependency order.
2. Include spec maintenance, shared state or helpers, runtime path, propagation, validation, and cleanup when those responsibilities apply.
3. Keep deferred work explicit rather than silently omitting it.
4. Add `Input`, `Outcome`, `Logic`, `External state`, `Config parameters`, and `Metrics` when a checklist task needs execution detail.
5. Derive implementation work from implementation use cases and retain the requirement IDs each task implements when requirements are present, whether they are owned by the same use case or mapped from a separate declarative use case.
6. Keep current status markers accurate.

Output:
- Reviewable planning artifact set with implementation checklist, ready for verification against the task and all relevant available context when applicable.

Record:
- Explicitly deferred implementation work and checklist status.
- Whether the verification loop was entered or skipped, and why.

Next:
- `Check specification completeness` when the task is complicated or large-scale.
- Otherwise, `Select the handoff`.

### Check specification completeness

Purpose:
- Verify that the generated or updated planning artifact set completely represents the solution established from the task and all relevant available context, without accidental omissions or scope drift.
- When a completeness finding cannot be resolved from relevant available context or a reasonable non-blocking assumption, record it in `Open questions`; pause and request user input only when correct planning cannot continue without the answer.

Run when:
- The specification was prepared for a complicated or large-scale task.
- Once the verification loop has started, keep it active until both checks have passed or the active check is awaiting required user input.

Skip when:
- Before the first iteration, skip the verification loop when the task is not complicated or large-scale.

Input:
- The task, optional shared task context, artifact-local context, and all other relevant context established before and during artifact preparation.
- The generated or updated planning artifact set.

Logic:

```text
| while the planning artifact set has not passed the completeness check:
  task and all relevant available context with current planning artifact set
    --compare the prepared artifacts with the established solution--> completeness findings
    --resolve findings from relevant available context--> updated or paused planning artifact set |
```

1. Treat the task as the authority for the requested outcome and scope. Use all relevant available context to interpret and elaborate it.
2. Inspect the applicable planning artifact set as a whole so content that should have been recognized as relevant is not missed.
3. Check that the prepared artifacts and implementation checklist preserve the established solution without accidental omissions or scope drift.
4. Treat task context as reusable evidence, not as the boundary of the check. Include artifact-local and original-source context when relevant.
5. Reasonable non-blocking assumptions may be made and recorded when they preserve the requested outcome and are supported by the available context.
6. Correct a finding autonomously only when its resolution follows from relevant available context or a reasonable non-blocking assumption.
7. Do not introduce a new solution decision solely to make the artifact set pass the check.
8. When a finding cannot be resolved from relevant available context or a reasonable non-blocking assumption, record it in `Open questions`. Classify it as blocking only when continuing would require an unsupported solution decision.
9. Do not treat the completeness check as passed while a blocking completeness finding remains unresolved.

Request next user input:
- When blocking completeness findings remain, request the information needed to resolve them as one coherent question batch and keep this step active.
- Process the response into the affected planning artifacts and resume the completeness check.

Output:
- While awaiting required user input, the planning artifact set with unresolved blocking completeness findings recorded in `Open questions`.
- After resolution, a completeness-checked planning artifact set.
- After the check passes, a concise user-visible chat summary of the inaccuracies corrected. If nothing changed, state that the check passed without changes.

Record:
- Completeness findings and their disposition.

Next:
- `Check specification consistency`.

### Check specification consistency

Purpose:
- Verify that the planning artifact set consistently expresses the solution established during artifact preparation.
- When a consistency finding cannot be resolved from relevant available context or a reasonable non-blocking assumption, record it in `Open questions`; pause and request user input only when correct planning cannot continue without the answer.

Run when:
- `Check specification completeness` completed in the current check-loop iteration.

Input:
- The task together with all relevant available context established before and during artifact preparation.
- The completeness-checked planning artifact set.

Logic:

```text
| while the planning artifact set has not passed the consistency check:
  task and all relevant available context with completeness-checked planning artifact set
    --compare the artifacts with the established solution--> consistency findings
    --resolve findings from relevant available context--> updated or paused planning artifact set |
```

1. Inspect the planning artifact set as a whole rather than limiting the check to content already identified as task-affected.
2. Treat a finding as relevant only when it prevents the artifact set from accurately expressing the established solution.
3. Preserve reasonable non-blocking assumptions that remain supported by the available context.
4. Correct a finding autonomously only when its resolution follows from relevant available context or a reasonable non-blocking assumption, and synchronize every affected planning artifact.
5. Do not introduce a new solution decision solely to make the artifact set pass the check.
6. When a finding cannot be resolved from relevant available context or a reasonable non-blocking assumption, record it in `Open questions`. Classify it as blocking only when continuing would require an unsupported solution decision.
7. Do not expand the task to resolve unrelated pre-existing issues.
8. Do not treat the consistency check as passed while a blocking consistency finding remains unresolved.

Request next user input:
- When blocking consistency findings remain, request the information needed to resolve them as one coherent question batch and keep this step active.
- Process the response into every affected artifact and resume the consistency check.

Output:
- While awaiting required user input, the planning artifact set with unresolved blocking consistency findings recorded in `Open questions`.
- After resolution, a task-accurate reviewable planning artifact set.
- After the check passes, a concise user-visible chat summary of the inaccuracies corrected. If nothing changed, state that the check passed without changes.

Record:
- Consistency findings and their disposition.

Next:
- `Check specification completeness` when resolving a consistency finding changed specification content.
- Otherwise, `Select the handoff`.

### Select the handoff

Purpose:
- Decide whether to stop for planning-artifact review or enter implementation using the task's readiness and the conversation-local implementation flow.

Input:
- Reviewable planning artifact set after the verification loop was skipped or completed.
- The user's current task request.
- Any unresolved questions or material planning decisions.

Conversation state:
- `implementation flow`: starts `inactive` in a new conversation, becomes `active` when the user's current task request authorizes implementation or when the user later authorizes implementation of prepared planning artifacts, remains active across later lifecycle tasks, and becomes `inactive` when the user requests that automatic implementation stop.

Logic:
Support the user's work as a flow. In a new conversation, prepare the first specification without implementation unless the user's request already requires an implementation change. The first implementation authorization activates the flow. While the flow is active, later narrow and unambiguous tasks may proceed from specification update to implementation without separate confirmation.

1. Honor the requested outcome. A request requiring an implementation change authorizes implementation; a request limited to specification preparation or review does not.
2. When implementation is not authorized and the flow is inactive, stop after preparing the planning artifact set and request an implementation decision. A later decision resumes from the same artifacts and checklist.
3. When implementation is authorized while the flow is inactive, activate the flow and notify the user that later eligible tasks in the current conversation may proceed to implementation without separate confirmation until the user asks to stop the flow. Then continue to implementation after resolving any required user input.
4. While the flow is active, a later task that does not request implementation directly may proceed automatically when the task and resulting planning artifacts are narrow and unambiguous, no blocking question remains, and the user has not limited the requested outcome to specification work. Otherwise, stop with the artifacts ready for review without deactivating the flow unless the user requests that it stop.
5. Whether the verification loop ran or was skipped does not itself authorize or prevent implementation.

Request next user input:
- When implementation requires confirmation, present the prepared planning artifacts and ask whether the user wants to proceed with implementation.
- Do not request this decision when the current task request already authorizes implementation or explicitly limits the outcome to specification preparation or review.
- Make the requested decision clear and treat any unambiguous implementation authorization as confirmation, regardless of its wording.
- Keep this step available for a later response. When the response authorizes implementation, process it as input for this handoff, update the conversation state, and continue according to the logic above.

Output:
- Terminal `planning artifacts ready for user review`, or authorization to enter the implementation loop.
- When this handoff activates the implementation flow, a user-visible notification that later eligible tasks in the current conversation may proceed to implementation without separate confirmation until the user asks to stop the flow.

Next:
- Terminal, or `Implement the plan`.

### Implement the plan

Purpose:
- Implement and verify every authorized implementation-checklist item while keeping affected specifications synchronized.
- If correct progress is blocked, request user input with one coherent batch of blocking questions.

Run when:
- The user has authorized implementation of the reviewable planning artifact set.

Input:
- Canonical solution spec and implementation checklist.
- Related task context when available, basis artifacts, ADRs, and other planning artifacts.
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
- Ensure implementation matches each confirmed or proposed local record or governing ADR and all use-case contracts. Do not implement a deferred-basis-dependent use case as though its basis were selected.
- Run focused tests and required broader validation.
- Ordinary implementation validation does not include executing a proposed basis's separately recorded basis-validation requirements. After implementation, when such requirements remain, ask the user whether they should be performed as a separate follow-up. Validation execution and result processing are outside this workflow version's scope.
- Do not mark implementation complete while affected specs or checklist statuses are stale.

Request next user input:
- When correct implementation cannot continue without resolving one or more blocking decisions, request one coherent batch of blocking questions, including related plan-extension decisions.
- Do not request input for non-blocking uncertainties.
- Process the response as decisions for continuing the unfinished implementation-checklist items, then resume the implementation loop.

Output:
- Implemented and synchronized planning artifact set.

Record:
- Validation evidence, implementation decisions, affected-spec status changes, and completed checklist tasks.

Next:
- Terminal `implemented and synchronized planning artifact set`.
