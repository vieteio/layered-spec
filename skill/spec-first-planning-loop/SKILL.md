---
name: spec-first-planning-loop
description: "Use when: a non-trivial coding request needs a user-story workflow, a technical use-case spec, or both before implementation, plus connected code context and batched open questions. Route user-visible journeys through story mapping and UI contracts; do not use for pure analysis or reference documents unless a specific chapter genuinely needs workflow/state/step treatment."
argument-hint: "Describe the requested change, known anchor or failing flow if any, and whether the task needs a workflow-bearing spec, a workflow-bearing section inside a larger document, or a narrower direct implementation."
user-invocable: true
---

# Spec-First Planning Loop

Use this skill when a non-trivial request should be handled as a plan-first, implementation-second workflow.

This skill orchestrates the planning loop. It does not replace specialized planning skills.

## Supporting Artifacts

- Shared planning contract: `planning/planning_contract.md`
- Prompt for question batching and execution loop behavior: `prompts/plan implementation in a loop.prompt.md`
- Existing mapping skill: `skill/connected-code-mapping/SKILL.md`
- Existing layered planning skill: `skill/layered-workflow-planning/SKILL.md`
- User-story planning skill: `skill/user-story-workflow-documentation/SKILL.md`
- UI-state and shared-contract review: `skill/design-ux-guardrails/SKILL.md`
- Existing reverse-documentation skill: `skill/code-logic-workflow-documentation/SKILL.md`

## When To Use

- a request spans multiple files or layers
- an implementation update may invalidate an existing spec
- a refactoring changes workflow shape while preserving broad use cases
- a compatibility slice must be planned before code edits
- the user wants a workflow-bearing markdown spec or workflow-bearing spec section to drive later implementation

## Do Not Use This Skill When

- the task is trivial and isolated enough to implement directly without a meaningful spec
- the user explicitly asks for direct implementation and the change is genuinely local
- the requested markdown artifact is pure analysis or reference content with no workflow-bearing section to plan

## Goal

Drive every non-trivial request through this lifecycle:

1. collect planning context
2. classify whether the request needs a user story, a technical use-case spec, or both
3. create or update the selected artifacts under `specs/`
4. resolve or batch open questions
5. check whether the plan is clear enough to start implementation
6. continue into implementation only after the plan is coherent enough
7. keep the artifacts synchronized as implementation lands

Implemented plans become specs. The loop must therefore maintain both the current plan and older affected specs.

## Core Rule

Do not start with implementation for non-trivial work.

Start by classifying the requested behavior, then create or update the needed workflow-bearing artifact or section using the shared contract in `planning/planning_contract.md`.

If the requested document is mixed, apply the contract only to the chapter that actually needs workflow, state, or step logic.

## Decision Tree

### 1. Classify The Request

Determine whether the request is:

- trivial and local
- non-trivial but mostly new behavior
- non-trivial and refactoring existing behavior
- non-trivial and a compatibility or migration slice

Then classify its planning level:

- `user-story only`: a journey/UI clarification that does not change system behavior yet;
- `technical use case only`: internal behavior with no meaningful user-visible workflow;
- `mixed`: user/application actions or visible states plus technical behavior required to make them true.

Treat developer technical language as a possible source for an induced user story when the resulting change alters a user journey. Treat product-language details about system boundaries, authority, state ownership, or implementation constraints as technical use-case input rather than forcing them into the story.

If the request is non-trivial, continue with this skill.

### 2. Find Existing Spec Context

Inspect `specs/` for related plans or specs.

For each relevant spec, classify it as:

- `active`
- `updated by current plan`
- `partially outdated`
- `superseded`
- `archived`

Record the required action:

- `reuse`
- `amend`
- `mark outdated`
- `replace`
- `archive`

### 3. Choose The Specialized Planning Inputs

Use `user-story-workflow-documentation` when the request needs a user journey, visible states, user/application actions, waits that affect user behavior, or E2E acceptance. Create or amend `specs/stories/<feature>_user_stories.md` as needed.

Use `design-ux-guardrails` after the story is known when the request changes visible UI. Keep story-specific wireframes in the story, reusable geometry in `specs/ui/layout-wireframes.md`, and reusable visual/icon rules in `specs/ui/style-and-icons.md`.

Use `connected-code-mapping` when the task is non-local, crosses system boundaries, or changes authority, data shape, durable state, or propagation.

Use `code-logic-workflow-documentation` when the task first needs a reliable reverse-engineered explanation of existing runtime behavior before new planning can proceed.

Use `layered-workflow-planning` to expand technical use cases and layers after the existing context is understood. Map story application steps to those use cases; do not repeat the full user journey inside the technical spec.

If the target artifact has no workflow-bearing section, do not force it through the layered contract just because it is non-trivial.

These skills may be combined in this order:

1. reverse-document existing behavior when necessary
2. map connected impacted surfaces when necessary
3. create or amend a user story when the request has a user-visible journey
4. review story UI states and shared UI contracts when visible UI changes
5. write or refine technical use cases in the shared contract shape

## Required Output Shape

The produced technical use-case plan and any related user story must follow their respective shapes in `planning/planning_contract.md`.

That requirement applies to workflow-bearing specs and workflow-bearing sections, not to pure analysis documents.

Use the contract as the single source of truth for top-level sections, use-case shape, optional layers, and question placement.

## Planning Loop

### Step 1. Create Or Update The Spec

Write or amend the plan/spec in `specs/`.

The artifact should include:

- planning anchor and changed assumption
- a story/use-case classification and links between the required levels
- connected existing logic when needed
- use cases with workflow lines, hierarchical numbering when that clarifies parent and child cases, and relevant layers
- user-story mappings for material application steps when the request is mixed
- story-specific UI states and shared UI-contract updates when the request changes visible UI
- early input validation and the post-validation contracts that downstream steps may rely on when that boundary matters
- `Implementation Logic` when declarative workflow layers are not enough to explain the coding path, or `Implementation Logic Proposal` when implementation detail should remain developer-owned
- implementation notes when created functions or methods should mention the workflow step in their docstrings
- local use-case ambiguities in `Use Case Questions` when they affect only one use case
- an `Implementation checklist` with numbered checkbox tasks and current status markers
- grouped open questions for general or escalated items
- decision log entries for assumptions and spec status changes

Wording rule for the produced spec:

- preserve concrete task-native terms when they already identify distinct states, artifacts, actors, or inputs
- do not swap those concrete terms for broader aliases that force the reader to infer whether the meaning stayed the same
- prefer wording that reuses the user's own meaning-bearing words and phrases when they are already accurate for the workflow, state, or artifact being described
- preserve wording that carries distinctions about role, state, scope, timing, ownership, comparison, or exceptions when those distinctions matter to the task
- when introducing helper names or intermediate structures in the spec, name them after the concrete data they hold or the concrete transformation they perform
- if a broader label is introduced for readability, define it immediately from the concrete inputs, outputs, persisted state, or boundary it refers to
- if a shorter label is needed, introduce it only after naming the original concrete term and only when the shortened label does not erase distinctions
- if a generated term would reasonably trigger a clarification question like "what is this referring to here?", keep the original wording or define the term immediately

### Step 2. Batch Questions

Follow `prompts/plan implementation in a loop.prompt.md`.

Rules:

- do not stop after each newly discovered ambiguity
- collect a coherent batch of new plan-extension questions
- continue working until the batch is ready
- stop only for the grouped question batch or a truly blocking ambiguity

Keep a question inside the relevant use case when it is local to that use case.

Promote it into the top-level `Open questions` batch when it becomes cross-cutting, globally blocking, or ready for user escalation as part of the current batch.

Question categories:

- `blocking`: planning or implementation cannot continue correctly
- `non-blocking`: the loop may continue under an explicit assumption if allowed

### Step 3. Resume After Answers

When the user answers the question batch:

- update the same plan/spec
- move resolved assumptions into `Decision log`
- update `Implementation checklist`
- continue planning or implementation from the same artifact

### Step 4. Check Plan Readiness Before Implementation

Before starting implementation, review the current plan/spec for completeness and consistency.

The plan is clear enough to start implementation only when:

- the changed behavior and planning anchor are specific enough to guide code changes
- the relevant use cases and required layers are present for the slice being implemented
- when the slice is user-visible, the relevant user story, its technical mappings, and its UI-state ownership are present
- use-case numbering is explicit enough to distinguish top-level cases from parent-child refinements when the workflow needs that structure
- validation boundaries and post-validation contracts are explicit enough when inner steps depend on stronger assumptions or should avoid redundant re-validation
- important files, functions, types, tables, or workflow states are named when implementation depends on them
- if the workflow description is still too declarative for coding, the plan adds `Implementation Logic` or explicitly leaves the algorithm developer-owned via `Implementation Logic Proposal` or omission
- the `Implementation checklist` is actionable enough to execute without guessing the next major step and reflects actual status through checkbox markers
- unresolved ambiguities are either captured as explicit assumptions or kept in `Open questions` / `Use Case Questions`
- no local contradiction remains between use cases, layers, the implementation checklist, and the decision log

If the plan is not clear enough:

- amend the plan/spec first
- add missing layers, details, or assumptions
- batch new user questions when the missing detail cannot be derived safely
- stop before implementation until the user reviews the plan update or answers the blocking questions

This readiness check is the last planning gate before implementation starts.

### Step 5. Keep Spec And Code In Sync

As implementation lands:

- update the current spec
- update or mark older impacted specs as outdated or superseded
- mention the workflow step in the docstring when a created function or method directly implements it
- do not leave code green while affected specs remain stale

## Implementation Checklist Rule

The `Implementation checklist` should normally follow this sequence:

1. [ ] spec maintenance or new spec creation
2. [ ] shared state or shared helper updates
3. [ ] runtime path updates
4. [ ] propagation updates
5. [ ] validation
6. [ ] cleanup

Spec maintenance is a first-class step, not cleanup.

## Quality Checks

- non-trivial work starts with a plan/spec update, not code edits
- the plan is stored in `specs/`
- mixed user-visible work distinguishes story-level workflows from technical use cases and keeps their mappings current
- user-story UI states are synchronized with `specs/ui/` contracts through `design-ux-guardrails` when visible UI changes
- related existing specs are scanned and classified
- use-case layers stay under each use case
- hierarchical use-case numbering is used when parent-child workflow relationships need to stay explicit
- title and scope wording stays concrete and task-native rather than leading with generic meta-summary language
- concrete task-native terms are preserved across workflow lines and layers; shorthand is introduced only when it is already established or is defined immediately without blurring distinctions
- helper and intermediate-structure names in the spec stay concrete enough that the reader can infer their contents, operation, and preserved distinctions without translating from generic planning vocabulary
- local questions may stay in `Use Case Questions`; general or escalated questions are grouped in the top-level `Open questions` section
- plans capture early validation and the downstream contracts that follow from it when that simplifies the implementation slice
- declarative workflow plans gain `Implementation Logic` when implementation detail is required, or explicitly leave the algorithm to the developer via `Implementation Logic Proposal` or omission
- implementation guidance captures when function or method docstrings should name the workflow step they implement
- implementation starts only after an explicit plan-readiness check confirms the plan is complete and consistent enough for the active slice
- if the readiness check finds missing detail or ambiguity, the plan is amended and/or the user is asked before implementation begins
- the `Implementation checklist` uses numbered checkbox items and keeps spec maintenance in that checklist
- refactoring updates use workflow refactoring syntax when helpful
- implementation does not finish while affected specs remain stale

## One-Line Heuristic

For any non-trivial request that needs workflow-bearing planning: inspect existing specs, gather connected context, write the workflow-bearing plan or chapter in `specs/` using the shared contract, batch open questions, run a plan-readiness check, then implement while keeping specs synchronized with the code.
