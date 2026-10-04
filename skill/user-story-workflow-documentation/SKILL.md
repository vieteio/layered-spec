---
name: user-story-workflow-documentation
description: "Use when: creating or updating user-story workflow files for user-visible product behavior, especially mixed user/app actions, asynchronous, multi-actor, recovery-sensitive, or UI workflows that must map to lower-level use cases. Do not use for internal-only refactors or a solution specification with no meaningful user journey."
metadata:
  version: "0.2.3"
---

# User-Story Workflow Documentation

After creating or updating structured stories, follow `skill/layered-spec-core/references/validation.md`, including saved validation preferences, installation approval and permitted skips. This also applies when the skill is used outside the specification lifecycle.

Create user-story artifacts that describe how actors and the application progress through a product workflow. Keep the story level separate from technical implementation detail.

When this skill creates or edits a specification, follow `skill/layered-spec-core/references/skill-pack-versioning.md`.

## Locations And Inputs

- Story files: `specs/stories/<solution-name>_user_stories.md`
- Solution specifications: `specs/<spec-name>.md`
- Shared UI contracts: `specs/ui/layout-wireframes.md` and `specs/ui/style-and-icons.md`
- Optional task context: `specs/task-contexts/<task-name>/task_context.md`
- Technical workflow syntax: `planning/planning_contract.md`
- Invariant syntax: `skill/layered-spec-core/references/invariants.md`

Read related story files and solution specifications before deciding whether to create, amend, supersede, or leave an artifact unchanged. When the story affects or depends on non-local behavior, use `connected-code-mapping` to discover the relevant story context before writing the story section.

When task context is available, reuse its relevant user-visible directives, findings, and evidence. Treat it as an optional reusable source rather than a completeness guarantee. Inspect original or additional sources whenever the story needs information that is absent, ambiguous, stale, or story-specific. Keep story-only context in the story; write a finding back to an in-scope task context only when another artifact is expected to benefit or shared understanding must be corrected. Read `skill/layered-spec-core/references/task-context.md` before updating task context.

This skill remains responsible for the story's correctness and works standalone without a lifecycle workflow or task-context file.

A task may affect several named business or framework specs, and later tasks may amend the same story. Link the actual related artifacts rather than assuming their names match the task folder.

## Decide The Artifact Level

Create or amend a user-story file when work changes a user goal, user-visible state, interaction sequence, asynchronous progress, recovery, authorization journey, or a workflow involving more than one actor.

Create or amend a solution specification when work needs system-owned transitions across validation, durable state, external integrations, authority boundaries, delivery mechanisms, retries, reconciliation, or cross-module propagation.

For mixed requests, split the source statements:

- user actions, application-visible actions, waits, and expectations belong in the story;
- one application action in the story maps to one or more technical use cases that decompose its internal states;
- constraints about system boundaries, durable state, authority, external integrations, and delivery mechanisms belong in the use case.

Induce the missing story from a technical request when it changes a meaningful user journey. Do not invent a story for an internal-only refactor, local algorithm change, or non-user-visible maintenance task.

## Story Shape

Follow `planning/planning_contract.md` for section and layer boundaries, and `skill/layered-spec-core/references/requirements-and-realization.md` for references. Prefer `### S1 — <User goal>` for story headings; existing numbered headings are also supported. Each story begins with a workflow and includes nonempty `Uses` and `E2E tests` layers. Each state has a `Description` layer.

Use this structure when it fits the solution:

````md
# <Solution name> User Stories

## Terms

### <Term>
<definition>

## Connected Groups Or Observed Existing Logic

### <Connected story, use case, group, or observed behavior>
- Relationship: <how it reaches, resumes, constrains, or otherwise operates on this story state or transition>
- Affected story state or step: `<state or S<story>.step<step>>`
- Evidence: <story, use-case, code, or UI-contract reference>
- Planning implication: <reuse, amend, preserve, or validate>

## States

### State <state-key> — <State name>

Description:
- <user expectation and visible condition>

UI:
```text
<story-specific wireframe when needed>
```

Uses:
- State/<state-key> -> UC4

## User Stories

### S1 — <User goal>
initial state --user/app step--> next state --app/user step--> outcome

User expectations:
- <what the user does, observes, or can rely on>

Uses:
- "user/app step" -> UC4

Invariants:
<optional user-visible or product-level state invariants and their derivations>

E2E tests:
- <end-to-end acceptance scenario>
````

Add `Implementation checklist`, `Open questions`, and `Decision log` when the story is actively driving implementation. Preserve existing story structure when amending it.

For ID-based `Uses` sources, declare anchors explicitly in `Workflow anchors:`, for example `- step3: Application reads`, then use `S1.step3 -> UC4`. Quoted labels do not require invented step numbers. Every anchor reference must name a declared anchor that corresponds to the intended workflow step or state.

## Actors, Waits, And State Syntax

Use explicit actor names such as `User`, `Application`, `Agent`, or `Collaborator`. A story may show parallel or conditional state using the shared workflow operators:

```text
input prepared --Application processes input, User waits or continues other work--> processing finished
```

Waiting is an actor action over a transition, not a state. Record it in the transition label only when it changes ownership, available actions, cancellation/retry behavior, interruption handling, or a user-visible expectation.

When the intermediate visible condition matters, model that condition as a state and keep the waiting action on the transition:

```text
input prepared --Application starts processing--> processing progress is shown --Application processes input, User waits or continues other work--> processing finished
```

Do not create a state solely to express that an actor is waiting. A non-terminating process may be modeled as a state only when its condition, available actions, or visible status is meaningful to the story.

Do not duplicate both sides of an obvious interaction merely to say that one actor waits while the other acts.

Keep story workflow chains, states, and transition labels in user-readable prose. Do not use KaTeX in those chains. A scientific formula may appear in a story's `Invariants` layer when it defines or derives a user-visible or product-level guarantee; implementation-specific formulas belong in the mapped technical use case.

## Uses Rules

Map every material story state and application action to existing or planned technical use cases. Use a `Uses` layer with stable identifiers such as `S2.step3 -> UC5.2`.

- A technical use case may implement several story steps.
- A story step may use several technical use cases.
- When a story step uses a declarative use case, map the step to that declarative use case and optionally to its requirement IDs, for example `S2.step3 -> UC5/R5.1-R5.3`.
- Do not additionally map the story step to use cases listed in `Realized by` unless they represent distinct user-visible behavior.
- When no separate declarative use case exists, map the story step to the implementation use case that owns the behavior.
- A `Uses` target may be declarative or implementation-oriented. The referenced use case owns any further `Realized by`, `Realizes`, `Requirements`, or framework mappings.
- Keep mapping at the state/step level, not only as a broad document-to-document reference.
- Technical use cases may wait for a user input or external event, but their focus remains the system boundary and resulting system state.
- Story E2E scenarios may cite the normative requirements they cover, but no particular scenario syntax is required.
- Do not copy internal contracts, mechanisms, or algorithms into the story unless they are necessary to explain a visible expectation.
- When task development selected a basis set, link to its task-development summary only when that decision changes a visible expectation; do not copy candidate workflows into the story.

## Invariants Rules

Use an optional `Invariants` layer when selected story states have meaningful user-visible or product-level invariants and later state invariants are preserved, assembled, or derived through story transitions.

- Do not add invariants to every story state.
- Keep the invariant outline parallel to the story workflow and identify the story state or step associated with each invariant and derivation.
- When supplied rationale concerns user-visible or product-level invariants, preserve and assess it in `Rationale`; keep internal implementation rationale in the mapped technical use case.
- Keep internal algorithms, representation invariants, and implementation proofs in the mapped technical use case.
- Natural-language reasoning may be a proof, justification, or proof sketch. Use **verifiable proof** only when formal text was successfully checked by its verifier.
- Follow `skill/layered-spec-core/references/invariants.md` for the detailed layer shape, identifiers, formalisms, and requirement relationship.

## Connected Context Rules

Place `## Connected Groups Or Observed Existing Logic` after `Terms` and before `States` when the story has meaningful existing context. It is a concise map of relationships, not a duplicate of a code inventory or solution specification.

- Include another story when it reaches, resumes, changes, or relies on a state in this story.
- Include a technical use case when it creates, restores, constrains, or publishes a material story state.
- Include observed existing behavior when it changes a visible expectation, available action, recovery path, or E2E acceptance condition.
- Include a shared UI contract when it governs the visible treatment of a story state.
- Map every entry to the affected story state or step and cite its evidence.
- State the planning implication so later work knows whether to preserve, reuse, amend, or validate the connection.
- Omit incidental implementation readers and writers; keep their detailed ownership and data-flow mapping in the technical use case or connected-code map.
- Cite task-context directive, finding, or evidence identifiers when they were consumed and the provenance is useful. Do not create an intermediate materialized context-view artifact.

## UI Synchronization

When a story has visible UI states, invoke `design-ux-guardrails`.

- Put local wireframes and interaction states in the story's `UI` block.
- Update `specs/ui/layout-wireframes.md` when the shared page or pane geometry changes.
- Update `specs/ui/style-and-icons.md` when a reusable visual role, icon meaning, selection treatment, or semantic color changes.
- Record `story state -> UI state -> technical use case` mapping. Do not duplicate a shared UI rule in every story.

## Quality Checks

- Terms distinguish actors, user-visible artifacts, and technical terms that could otherwise be ambiguous.
- States describe visible conditions and user expectations, not hidden implementation steps.
- User stories include a compact workflow line followed by a `Uses` layer and E2E coverage.
- Story workflow chains remain user-readable prose; scientific formulas stay in an optional story-level `Invariants` layer or in mapped technical layers according to their scope.
- Story-level invariants describe only meaningful user-visible or product-level guarantees, and their derivations agree with the corresponding story transitions.
- Connected context identifies material related stories, use cases, observed behavior, and shared UI contracts without duplicating their internals.
- Every material application step uses one or more technical use cases, and the `Uses` mapping does not invent unsupported implementation detail.
- UI wireframes cover only story-specific layout; shared rules remain in `specs/ui/`.
- Existing stories and solution specifications remain consistent after the change.
- Task context is reused when available but is never treated as the story's exclusive source or completeness boundary.
- Standalone story authoring does not require a lifecycle workflow or task-context file.

## One-Line Heuristic

Describe the user journey as a chain of user and application states, then map each application transition to the technical use cases that make it true.
