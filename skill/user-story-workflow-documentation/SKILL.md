---
name: user-story-workflow-documentation
description: "Use when: creating or updating user-story workflow files for user-visible product behavior, especially mixed user/app actions, asynchronous, multi-actor, recovery-sensitive, or UI workflows that must map to lower-level technical use cases. Do not use for internal-only refactors or a purely technical use-case specification with no meaningful user journey."
---

# User-Story Workflow Documentation

Create user-story artifacts that describe how actors and the application progress through a product workflow. Keep the story level separate from technical implementation detail.

## Locations And Inputs

- Story files: `specs/stories/<feature>_user_stories.md`
- Technical use-case specs: `specs/<feature>.md`
- Shared UI contracts: `specs/ui/layout-wireframes.md` and `specs/ui/style-and-icons.md`
- Technical workflow syntax: `planning/planning_contract.md`

Read related story files and technical specs before deciding whether to create, amend, supersede, or leave an artifact unchanged. When the story affects or depends on non-local behavior, use `connected-code-mapping` to discover the relevant story context before writing the story section.

## Decide The Artifact Level

Create or amend a user-story file when work changes a user goal, user-visible state, interaction sequence, asynchronous progress, recovery, authorization journey, or a workflow involving more than one actor.

Create or amend a technical use-case spec when work needs system-owned transitions across validation, durable state, external integrations, authority boundaries, delivery mechanisms, retries, reconciliation, or cross-module propagation.

For mixed requests, split the source statements:

- user actions, application-visible actions, waits, and expectations belong in the story;
- one application action in the story maps to one or more technical use cases that decompose its internal states;
- constraints about system boundaries, durable state, authority, external integrations, and delivery mechanisms belong in the use case.

Induce the missing story from a technical request when it changes a meaningful user journey. Do not invent a story for an internal-only refactor, local algorithm change, or non-user-visible maintenance task.

## Story Shape

Use this structure when it fits the feature:

````md
# <Feature> User Stories

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

### <State name>
Description:
- <user expectation and visible condition>

UI:
```text
<story-specific wireframe when needed>
```

Technical mapping: <use-case ids and technical states>

## User Stories

### 1. <User goal>
initial state --user/app step--> next state --app/user step--> outcome

User expectations:
- <what the user does, observes, or can rely on>

Technical mapping:
- `<story step or state> -> <use-case id / technical state>`

E2E tests:
- <end-to-end acceptance scenario>
````

Add `Implementation checklist`, `Open questions`, and `Decision log` when the story is actively driving implementation. Preserve existing story structure when amending it.

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

## Technical Mapping Rules

Map every material story state and application action to existing or planned technical use cases. Use stable identifiers such as `S2.step3 -> UC5.2`.

- A technical use case may implement several story steps.
- A story step may use several technical use cases.
- Keep mapping at the state/step level, not only as a broad document-to-document reference.
- Technical use cases may wait for a user input or external event, but their focus remains the system boundary and resulting system state.
- Do not copy internal contracts, mechanisms, or algorithms into the story unless they are necessary to explain a visible expectation.

## Connected Context Rules

Place `## Connected Groups Or Observed Existing Logic` after `Terms` and before `States` when the story has meaningful existing context. It is a concise map of relationships, not a duplicate of a code inventory or technical use-case specification.

- Include another story when it reaches, resumes, changes, or relies on a state in this story.
- Include a technical use case when it creates, restores, constrains, or publishes a material story state.
- Include observed existing behavior when it changes a visible expectation, available action, recovery path, or E2E acceptance condition.
- Include a shared UI contract when it governs the visible treatment of a story state.
- Map every entry to the affected story state or step and cite its evidence.
- State the planning implication so later work knows whether to preserve, reuse, amend, or validate the connection.
- Omit incidental implementation readers and writers; keep their detailed ownership and data-flow mapping in the technical use case or connected-code map.

## UI Synchronization

When a story has visible UI states, invoke `design-ux-guardrails`.

- Put local wireframes and interaction states in the story's `UI` block.
- Update `specs/ui/layout-wireframes.md` when shared page or pane geometry changes.
- Update `specs/ui/style-and-icons.md` when a reusable visual role, icon meaning, selection treatment, or semantic color changes.
- Record `story state -> UI state -> technical use case` mapping. Do not duplicate a shared UI rule in every story.

## Quality Checks

- Terms distinguish actors, user-visible artifacts, and technical terms that could otherwise be ambiguous.
- States describe visible conditions and user expectations, not hidden implementation steps.
- User stories include a compact workflow line followed by mappings and E2E coverage.
- Connected context identifies material related stories, use cases, observed behavior, and shared UI contracts without duplicating their internals.
- Every material application step maps to one or more technical use cases, and the mapping does not invent unsupported implementation detail.
- UI wireframes cover only story-specific layout; shared rules remain in `specs/ui/`.
- Existing stories and technical specs remain consistent after the change.

## One-Line Heuristic

Describe the user journey as a chain of user and application states, then map each application transition to the technical use cases that make it true.
