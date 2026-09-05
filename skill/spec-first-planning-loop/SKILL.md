---
name: spec-first-planning-loop
description: "Use for non-trivial coding tasks that should be planned through repository technical solution specifications before implementation. Initialize and follow the repository's customizable specification lifecycle, gather connected code context, request and process required user input, restore the bundled workflow only when explicitly requested, and keep planning files synchronized with implementation. Do not use for trivial local changes or pure analysis and reference documents that do not describe a process or state change."
metadata:
  version: "0.2.2"
argument-hint: "Describe the task, known code entry point or failing behavior, existing solution spec if any, and whether you want planning only or implementation after the spec."
user-invocable: true
---

# Spec-First Planning Loop

When this skill creates or edits a specification, follow `skill/layered-spec-core/references/skill-pack-versioning.md`.

For non-trivial tasks, this repository uses solution specifications to describe the intended change before implementation.

Solution specifications describe technical workflows, connected code, solution decisions, implementation details, and the implementation checklist.

The specification lifecycle describes how to turn a task description into a solution specification, prepare it for review, implement the approved specification, and keep the planning files synchronized with the code.

The active lifecycle chain and its step descriptions are stored in `specs/spec-lifecycle/workflow.md`. This skill explains how to initialize that file from the bundled default when necessary, follow its chain, use the specialized skills named by its steps, request and process user input, resume interrupted work, and decide when planning or implementation is complete.

## Workflow Template And Active File

- `assets/default_workflow.md` is the bundled default template and records its skill-pack version as `Default workflow version`.
- `specs/spec-lifecycle/workflow.md` is the only active lifecycle workflow and records the default-workflow version from which it was created or with which it was most recently synchronized.

Before starting a specification lifecycle:

1. Check whether the active workflow exists.
2. If it exists, use it without replacing it or reconciling it automatically with the bundled template.
3. If it is missing, create its parent directory when necessary, copy `assets/default_workflow.md` to the active path, report that the repository workflow was initialized, and then use the created active workflow.
4. If initialization fails, report the error and stop instead of silently executing the bundled template.

Treat changes to the bundled template as defaults for future initialization only. Never propagate them automatically into an existing active workflow.

Do not change the active workflow's recorded default-workflow version during ordinary customization. Update it only when the active workflow is initialized from, explicitly synchronized with, or explicitly restored from that bundled default version.

Restore the bundled default only when the user explicitly requests restoration. Before replacing an existing active workflow, show or summarize its differences from the bundled default and ensure the current version is recoverable through version control or a user-approved backup. After restoration, continue to treat the restored active file as the sole authority.

## Helping Users Customize The Lifecycle

When the user requests lifecycle behavior that conflicts with the active workflow, or expresses a lasting workflow preference that the active workflow does not support:

- Briefly explain at the relevant point that the specification lifecycle is defined in `specs/spec-lifecycle/workflow.md` and can be changed to support the requested behavior.
- Do not silently override the active workflow or treat a conflicting request as a permanent exception.
- Do not modify the active workflow unless the user asks to update or customize it.
- Do not show this help message when the user is already requesting a `workflow.md` update or has already been given the same explanation for the current preference.

## Files Used By This Skill

After ensuring that the active workflow exists, read both authoritative files completely before starting a non-trivial specification lifecycle:

- `specs/spec-lifecycle/workflow.md` describes the active lifecycle chain and every available step.
- `planning/planning_contract.md` describes the format used inside solution specifications, including workflow notation, layers, and section structure.

Use them together:

- Read the active `workflow.md` to determine what step comes next, why it exists, what it consumes, and what it must produce.
- Use this skill to decide whether the step runs, execute it, request and process user input required by the step, and continue to the next step.
- Read `planning_contract.md` when creating or updating the contents of a solution specification.
- When a workflow step names another skill, read that skill and use it to perform the step.
- Apply repository instructions while changing code, tests, databases, task lists, or workflow traces.

Files under `specs/spec-lifecycle/` define the planning process. They are not solution specifications for a particular task, so do not classify them as active, outdated, superseded, or archived solution specs.

## When To Use This Lifecycle

Use it when a task spans multiple files or responsibilities, changes an existing workflow, needs technical planning, may invalidate an older spec, or will be implemented from a reviewed solution specification.

Skip it for a genuinely local change that can be implemented safely without a meaningful plan. Also skip it for pure analysis or reference documents unless a specific section describes a workflow or state change that needs this lifecycle.

## Important Rules

- Preserve the user's concrete task language and existing authoritative spec content unless the current step requires a local correction.
- Do not silently skip an optional step when its description requires a recorded reason.
- Follow the step order in `workflow.md`; do not reconstruct the lifecycle from this skill or from specialized-skill instructions.
- Keep the task's main solution spec and affected older specs synchronized as implementation proceeds.

## How To Follow The Lifecycle

Each workflow step may use these fields:

- `Purpose`: why the step exists, what successful completion means, and which paused state is explicitly permitted. Use it as the completion check, not as execution logic.
- `Run when`: condition that enables the step.
- `Skip when`: condition that allows an optional step to be bypassed.
- `Input`: state and files consumed by the step.
- `Conversation state`: optional lifecycle state scoped to the current conversation and shared with later lifecycle tasks in that conversation.
- `Skill`: specialized skill used to perform the step.
- `Logic`: instructions written directly in the step, or supplementary instruction files linked from it, when no specialized skill is needed.
- `Request next user input`: optional step-specific instructions for requesting user input and processing the response.
- `Output`: state and files produced by the step.
- `Record`: decisions or evidence that must be written down.
- `Next`: following step, branch, or final workflow outcome.

Every step must define `Purpose`. A step normally defines either `Skill` or `Logic`, not both. A step that may pause for a user response should define `Request next user input`. Step headings are stable identifiers; do not rely on step numbers when extending the workflow.

Preserve workflow-declared `Conversation state` after a lifecycle task reaches a final outcome so later tasks in the same conversation can use it. Reset that state for a new conversation. Do not infer conversation state that the active workflow does not declare, and do not write it into solution artifacts unless the step's `Record` instructions require that.

When `Logic` links to supplementary instructions, resolve relative paths from the active `workflow.md` location and read each selected file completely before executing the step. If a referenced file is missing or cannot be read, report the error and keep the step incomplete instead of inventing fallback instructions.

Follow these instructions:

1. Read `workflow.md` and `planning_contract.md` completely.
2. If resuming an existing lifecycle, continue from its current unfinished step or permitted handoff. Otherwise, start with the first step defined by the active workflow chain.
3. Find the detailed description of the current step.
4. Read `Purpose` to understand what the step must accomplish before it can finish.
5. Use the request, repository rules, existing files, earlier outputs, and declared conversation state to evaluate `Run when` and `Skip when`.
6. Perform the step:
   - if it names a `Skill`, read that skill completely and follow its instructions;
   - if it contains `Logic`, follow those instructions directly.
7. Update declared `Conversation state`, `Output`, and `Record` items before following `Next`.
8. When skipping a step or branch, record the reason if its description requires one.
9. Before leaving the step, confirm that its execution, output, and next transition fulfill its `Purpose`. Treat an incomplete result as a paused state only when `Purpose` permits it and the step defines how to request the next user input.
10. Use `planning_contract.md` to interpret workflow arrows, branches, parallel states, refactoring transitions, typed workflows, loops, and recursive calls.
11. When `Request next user input` instructs the step to request input, follow `Requesting And Processing User Input` and keep the current step active until the response is processed.
12. Continue until the chain reaches a final outcome, the user selects a permitted stopping point, or the active step is awaiting required user input.

## Running A Skill-Backed Step

A `Skill` field in `workflow.md` names the specialized skill that performs that step. Resolve the available skill by name, read it completely, and apply it only when the lifecycle selects that step.

The connection between a lifecycle step and a specialized skill belongs in `workflow.md`. Do not add lifecycle step names or lifecycle ordering to the specialized skill itself.

If a named skill is unavailable or cannot be read, report that clearly. Continue without it only when the step itself or the user provides an explicit safe fallback; never silently substitute another procedure.

## Choosing And Skipping Steps

- Choose a branch from the current task state and existing evidence, not from arbitrary alternatives.
- Write down a branch decision when the step requires it, usually in the task's decision log or relevant planning section.
- A user may choose a permitted stopping point, but that choice does not remove prerequisite files required by the workflow or planning contract.
- When skipping connected mapping or another optional step, preserve the state required by the next step and record the skip reason when requested.

## Requesting And Processing User Input

When the active step's `Request next user input` instructions call for input:

1. Follow its instructions to request the next user input.
2. Keep the current workflow step active while waiting for the response; do not follow `Next` unless the step explicitly says otherwise.
3. Process the response for the same step, applying it to the relevant planning files, implementation state, and decisions as instructed.
4. Continue according to the current step's instructions after the response is processed.

Do not restart from the workflow's first step unless the response materially replaces the task itself. Continue processing the current step otherwise.

```text
| while the active step requests next user input:
  active workflow step --request the input described by the step--> awaiting user response
  --process the response for the same step--> updated active workflow step |
```

## Final Outcomes

The final outcomes mean:

- `spec ready for user review`: the planning files and implementation checklist are ready, but implementation is not authorized by this branch.
- `implemented and synchronized solution spec`: no authorized checklist tasks remain, required validation has completed, and affected planning files match the implemented behavior.

## Before Finishing

- Both lifecycle files were read before starting.
- The active workflow existed or was initialized visibly from `assets/default_workflow.md`; the bundled template was not used as a hidden fallback.
- The active workflow records the default-workflow version from which it was created or with which it was most recently synchronized.
- An existing active workflow was not overwritten automatically, and restoration occurred only when explicitly requested.
- The current step came from `workflow.md`.
- Every step has a concise `Purpose`, and its execution, output, and next transition fulfill that purpose.
- Workflow notation and solution-spec structure follow `planning_contract.md`.
- A skill-backed step used the skill named by the workflow without adding lifecycle knowledge to that specialized skill.
- An inline step followed the `Logic` written in the workflow.
- Required branch and skip decisions were recorded.
- User input was requested and processed according to the active step's `Request next user input` instructions.
- Workflow-declared conversation state was preserved across lifecycle tasks in the same conversation, reset for a new conversation, and kept out of solution artifacts unless the workflow required it there.
- Lifecycle-policy files were excluded from solution-spec searches and status classification.
- Work resumed from the interrupted step and existing files instead of restarting unnecessarily.
- The implemented behavior and all affected planning files are synchronized.
