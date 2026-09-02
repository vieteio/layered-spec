---
name: code-logic-workflow-documentation
description: 'Use when: extracting an existing code path into a workflow-bearing document with workflow steps, state transitions, type or table definitions, and reference mappings. Do not use for pure analysis or reference documents that do not describe code-path behavior. In mixed documents, use this skill only for the workflow-bearing chapter.'
metadata:
  version: "0.2.2"
argument-hint: 'Describe the concrete code path, entrypoint, and the workflow-bearing document or chapter that should be documented.'
user-invocable: true
---

# Code Logic Workflow Documentation

When this skill creates or edits a specification, follow `skill/layered-spec-core/references/skill-pack-versioning.md`.

## When to Use
- Document an existing implementation before refactoring it
- Convert a code path into a standalone workflow note
- Explain how code-path states move through a pipeline
- Capture the tables, caches, models, and response shapes a workflow depends on
- Add navigation aids for large technical workflow documents

## Do Not Use This Skill When
- The requested document is pure analysis or reference material with no code-path behavior to trace
- The artifact is mixed and only one chapter needs workflow tracing; scope this skill to that chapter instead of rewriting the full document as a workflow note

## What This Skill Produces
- A standalone markdown document for a workflow-bearing code path
- Workflow traces written as state-to-state transitions
- A short workflow schema for each workflow, compatible with layered workflow planning syntax
- A definitions section for all referenced types, tables, and key runtime structures
- A reference table summarizing definitions and roles
- A state-name dictionary mapping workflow labels to definition headings
- Optional named layers such as `Data`, `Types`, `Tables`, `Detailed Workflow`, `Invariants`, `Logic Details`, `Observed Existing Logic`, `Realizes`, `Uses`, `Input Validation And Contracts`, `Implementation Logic`, `Implementation Logic Proposal`, and `Tests` when the user wants compatibility with planning artifacts that follow `planning/planning_contract.md`

## Procedure
1. Find the entrypoint and trace the call graph through the relevant code path.
2. Identify the concrete states in the workflow.
State examples: input text, parsed structure, canonical model, cache row, database table row, vector index entry, API response object.
When selected states have meaningful observed invariants, identify how those invariants are later preserved, assembled, or used to derive other state invariants through the implemented transitions. Do not invent invariants for every state.
3. Record the exact structures the workflow relies on.
Include database tables, cache tables, in-memory models, pipeline outputs, and response schemas.
Also note where weak input enters the workflow, where it is validated or normalized, and what stronger contract later steps rely on after that boundary.
4. Write the document so it is standalone.
Begin with definitions, then add the workflow traces, then add a short workflow schema for each workflow, then add navigation aids such as a reference table and a state-name dictionary.
5. Verify terminology consistency.
Keep the same naming across definitions, workflow steps, and lookup sections unless the user explicitly asks to preserve original workflow labels.

If the workflow has meaningful parent and child subflows, use hierarchical use-case numbering when emitting compatibility output that follows the shared planning contract.

Reverse documentation describes observed behavior and implementation. Do not promote an observed code path or observed invariant into a normative `Requirements` entry solely because the code currently behaves that way. When an authoritative planned specification already provides requirement IDs, the documented implementation may use `Realizes` to map concrete workflows and symbols back to those requirements. When a documented implementation step calls or delegates to another specified use case, it may use `Uses` to map that step to the referenced declarative or implementation use case.

## Workflow Syntax Compatibility

When the user wants compatibility with layered-workflow-planning or the shared planning contract in `planning/planning_contract.md`, use the operators and layer syntax defined in the contract.

Use that compatibility shape only for workflow-bearing artifacts or workflow-bearing sections of mixed documents.

That includes hierarchical use-case numbering when parent and child workflow cases should stay grouped, plus the distinction between declarative workflow layers and `Implementation Logic` or `Implementation Logic Proposal` when implementation detail is or is not clear enough to document.

When observed state invariants and their derivation are meaningful, use an `Invariants` layer and follow `skill/layered-spec-core/references/invariants.md`. Keep a concise outline mapped to the documented workflow and place long invariant definitions, calculations, natural-language proofs, or formal text in detailed entries below it.

Keep documented workflow schemas, state names, and transition labels in concise prose even when the code implements scientific logic. Put relevant KaTeX equations in `Logic Details`, `Execution Logic`, `Implementation Logic`, `Data`, or `Invariants`, with notation definitions and assumptions close to the equation. Use `$...$` inline and `$$...$$` for standalone formulas.

## Tests Layer Compatibility

When the user wants compatibility with layered-workflow-planning or the shared planning contract, a `Tests` layer may be added using the syntax defined in the contract.

## Workflow Schema

For each documented workflow, add one short workflow schema in the notation below:

`trigger --step 1 description--> state 1 --step 2 description--> state 2`

Use it as a compact overview, not as a replacement for the detailed workflow trace.

Guidelines:
- Start from the workflow trigger or entry condition
- Use short state names that match the document terminology
- Keep step descriptions short and action-oriented
- If the workflow has branches, use branch operators or write one short schema per branch before the detailed trace

Example:

`request received --load source text--> raw text --extract structure--> extracted model --build embeddings--> vector index --resolve matches--> response`

## Output Shape

```md
# <Document Title>

Brief purpose and scope.

## Definitions

### <Structure Name>
Type: <runtime type or persistence type>

Purpose: <what role it plays>

Key fields:
- <field>
- <field>

## Definition Reference Table

| Definition heading | Kind | Short role in workflow |
| --- | --- | --- |

## State Name Dictionary

| Workflow state name | Definition heading |
| --- | --- |

## <Workflow Name>

Workflow:
`trigger --step 1 description--> state 1 --step 2 description--> state 2`

Types:
<Optional type definitions when useful>

Data:
<Optional concrete constants, templates, lists, matrices, tables, or other structured values when they materially shape the workflow>

Tables:
<Optional table definitions when useful>

Detailed Workflow:
<Optional typed workflow when intermediate state structure matters>

Invariants:
<Optional selected state invariants, concise invariant outline, and detailed preservation or derivation reasoning>

Logic Details:
<Optional rules or missing logic not obvious from the trace>

Input Validation And Contracts:
<Optional validation boundary, normalization rules, and post-validation assumptions used by later steps>

Implementation Logic:
<Optional algorithmic detail, intermediate structures, indexes, trees, graphs, or other containers needed to explain how the implementation works>

Implementation Logic Proposal:
<Optional high-level implementation notes when the full algorithm is not clear from the existing code needs developer clarification>

Observed Existing Logic:
<Optional notes that make the artifact compatible with forward planning documents>

Realizes:
<Optional existing requirement IDs realized by this documented implementation>

Uses:
<Optional implementation workflow step to referenced use-case mappings>

Tests:
<Optional regression scenarios tied to the documented workflow using the Tests layer syntax>

1. <Step title>
State name: <state label>
Type: <type>
Elements: <important fields>
Transition: <how state changes>
```

## Quality Checks
- Every workflow state mentioned later has a definition or an explicit mapping to one
- Type names and persistence names are not mixed together without explanation
- Cache states, index states, and persisted rows are distinguished clearly
- The document can be read without opening the code first
- Navigation sections do not silently rename workflow labels unless requested
- Each workflow includes a short workflow schema that matches the detailed trace
- If named layers are used, they stay compatible with layered-workflow-planning naming and with `planning/planning_contract.md`
- Observed workflows remain distinguishable from normative requirements; `Realizes` mappings are added only when their requirement source already exists
- `Uses` identifies observed calls or delegation to an existing specified use case without claiming requirement realization
- An observed `Invariants` layer maps only meaningful state invariants and their derivations to the documented workflow without silently promoting them into requirements
- **verifiable proof** is used only when formal text was successfully checked by the corresponding verifier
- Early validation boundaries and their downstream contracts are documented when later workflow steps rely on stronger assumptions
- `Implementation Logic` is used only when declarative workflow layers are not enough to explain the implementation, and `Implementation Logic Proposal` or omission is used when the full algorithm is not recoverable yet from the existing code and needs developer clarification
- Scientific formulas that clarify observed logic use KaTeX in a technical Logic, Data, or `Invariants` layer; workflow schemas stay prose-only and scannable
- If a `Tests` layer is used, it reflects the documented behavior rather than speculative future behavior and each test entry includes at least `description` or `workflow`

## Common Variations
- If the user wants production terminology, rename the document terms while leaving code references unchanged
- If the user wants original labels preserved, keep workflow state names intact and map them through the state-name dictionary
- If multiple workflows merge, document each branch separately before describing the merge stage
- If the user wants direct compatibility with forward solution planning documents, keep the reverse-engineered content in named layers such as `Data`, `Types`, `Tables`, `Detailed Workflow`, `Invariants`, `Logic Details`, `Input Validation And Contracts`, `Implementation Logic`, `Implementation Logic Proposal`, `Observed Existing Logic`, and `Tests`, then place that content into a plan/spec that follows `planning/planning_contract.md`
