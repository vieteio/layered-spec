# Requirements And Use-Case Realization

Use this reference when a technical specification needs identified requirements or needs to distinguish required behavior from the implementation workflows that make it true.

## Progressive Structure Selection

Start with one implementation use case and introduce only the additional structure needed to keep behavior and implementation clear:

```text
technical behavior
  --describe directly when workflow and logic are sufficient-->
implementation use case

technical behavior with non-trivial requirements
  --identify requirements without splitting a coherent implementation-->
implementation use case with Requirements and Logic

independently substantial required behavior and implementation decomposition
  --separate what is required from several realizing workflows-->
declarative use case with Requirements
  --is realized by-->
realizing use cases
```

Use these selection rules:

1. Use one implementation use case with a workflow and `Logic` when those layers completely describe the behavior.
2. Add `Requirements` to that implementation use case when non-trivial conditions, invariant obligations, rejection rules, or required outcomes need stable identifiers and explicit normative wording.
3. Split out a declarative use case when its requirements and the implementation decomposition each need an independently understandable workflow, normally because several use cases jointly realize the requirements or reusable framework logic must remain separate.

Do not introduce a declarative use case merely because a `Requirements` layer exists.

For each requirement ID, the definition written directly in `Requirements` is authoritative. Optional duplicate or translated representations must reference that ID and preserve its meaning. Use a workflow chain when explicit input and outcome states improve the requirement, EARS when behavioral natural language is clearer, a hierarchical contract when one umbrella obligation benefits from detailed clauses, and an identified constraint when the rule is not naturally a transition.

## Declarative And Implementation Use Cases

An implementation use case states how technical behavior is performed. It contains an implementation-oriented workflow and the logic, structures, boundaries, and tests needed to implement it. It may also own a `Requirements` layer when the normative behavior needs explicit definition but a separate declarative workflow would add no clarity.

A declarative use case states what technical behavior is required independently of its implementation decomposition. It normally contains:

- one semantic workflow under the use-case heading;
- a `Requirements` layer with identified workflow chains, EARS requirements, hierarchical contracts, or non-transition constraints;
- a `Realized by` layer mapping those requirements to realizing use cases.

A use case referenced by realization mappings adds a `Realizes` layer naming the requirements it implements. The realizing use case may itself be declarative: it may own more detailed requirements and a further `Realized by` layer while also declaring which upstream requirements it `Realizes`.

Do not add `Realized by` or `Realizes` when an implementation use case owns and implements its own requirements. Hierarchical numbering expresses containment, not realization by itself. Use explicit mappings whenever requirements are owned by a separate declarative use case, even when realizing use cases are numbered as children of that declarative use case.

Keep a local realization under its parent when that placement communicates ownership. Keep a reusable framework workflow as a separately identified use case or separate specification. A declarative use case formally implemented by that framework references it through `Realized by`; an implementation use case whose behavior relies on the framework references it through `Uses`.

## Requirements Layer

The `Requirements` layer specifies declarative behavior through EARS requirements, identified workflow chains, hierarchical contracts, or identified non-transition constraints. Chains make required inputs and outcomes explicit; EARS expresses behavior in controlled natural language. A hierarchical contract uses a parent requirement as its umbrella obligation and descendant requirement IDs as its clauses. Keep the contract and its clauses under the owning use case. Each requirement has a stable ID.

Use stable identifiers such as `R4.1`, where `4` is the owning use-case number and `1` is the local requirement number.

```md
Requirements:

R4.1:
accepted input
--construct every required result element-->
complete result

R4.2:
complete result
--validate publication constraints-->
publishable result
```

Use the optional form names `contract`, `EARS`, and `chain` when they make the requirement structure easier to read. Ordinary identified requirements remain valid without a form name.

```md
Requirements:

R4.3 contract:
A result is published only when it is complete.

R4.3.1 EARS:
When validation finds a missing required element, the system SHALL reject the result.

R4.3.2 chain:
validated complete result
--atomically publish the result-->
committed result

R4.3.3:
A rejected result leaves the previously committed state unchanged.
```

Requirements inside this layer are normative whether the owner is an implementation use case or a separate declarative use case. Workflow text outside the layer may also describe planned or observed behavior, but it does not become a requirement merely because it uses workflow syntax.

Preserve an identifier when wording is clarified without changing its meaning. Assign a new identifier when the required behavior changes materially.

### Select Operators From Meaning

- Use composition when one required transition follows another.
- Use product when several required calculations or effects participate together.
- Use coproduct when one decision has alternative cases or outcomes.
- Use a loop when required behavior repeats while a stated condition applies.
- Use an explicit recursive call when a required transition invokes the same workflow chain or another chain in one mutually recursive family.
- Use separate requirement chains when obligations are independent rather than alternatives.

Do not flatten consecutive stages, simultaneous obligations, and rejection behavior into one coproduct merely because they were originally written as separate requirement sentences.

Recursion does not introduce another delimiter. Use the ordinary workflow operators for each recursive step body, name every recursive call target, and follow `recursive-workflows.md` for compact versus hierarchical decomposition and family-level termination rules.

### Non-Workflow Requirements

Do not force every requirement into an artificial transition. A requirement may instead be an identified:

- invariant;
- type or schema constraint;
- formula or quantitative limit;
- table or matrix;
- architectural or compatibility constraint.

Place the requirement in the layer that expresses it most precisely and retain its requirement ID so realization and verification can still refer to it.

### Requirements And Invariants

The `Requirements` and `Invariants` layers have different responsibilities:

- `Requirements` declares normative obligations.
- `Invariants` records meaningful invariants for selected workflow states and explains how later state invariants follow from earlier state invariants through workflow logic.

An invariant is not normative merely because it appears in `Invariants`. When the invariant and requirement have the same owning use case, a requirement may reference it:

```md
Requirements:

R1:
A completed result satisfies `I3`.
```

The invariant definition supplies the referenced condition. Its derivation supplies the proof, justification, or proof sketch that the owning workflow establishes it.

When an invariant belongs to a realizing use case, keep the owning requirement definition self-contained, retain the `Realized by` / `Realizes` mapping, and let the realizing use case's invariant derivation identify the requirement it justifies. The invariant derivation provides reasoning about realization; it does not replace realization mappings.

Natural-language reasoning may be a proof. Call it a **verifiable proof** only when it is expressed in a formalism and successfully verified by the corresponding checker.

Follow [invariants.md](invariants.md) for invariant identifiers, outlines, derivations, supported formalisms, and technical-use-case boundaries.

## Realization Mapping

Use realization mappings only when requirements are owned by a separate declarative use case. The declarative use case maps requirements to the use cases that formally implement them:

```md
Realized by:
- R4.1 -> UC4.1, UC4.2
- R4.2 -> UC4.3
```

Each realizing use case provides the symmetric reverse mapping:

```md
Realizes:
- UC4/R4.1
```

The owning use-case prefix may be omitted when the requirement owner is unambiguous in the same local use-case group. Qualify the owner for cross-spec mappings or whenever another requirement could have the same local ID.

A declarative realizing use case may map an upstream requirement into its own more detailed requirements:

```md
Realized by:
- R4.1 -> UC7/R7.1, UC7/R7.2

### 7. Framework contract
...

Realizes:
- UC4/R4.1
```

Many-to-many mappings are valid. A requirement may need several realizing use cases, and one reusable use case may realize parts of several requirements. Every `Realized by` target must contain the matching `Realizes` entry, including when the target is declarative.

An implementation use case that provides shared infrastructure without directly satisfying one requirement should say so and name its consumers. Do not create a false requirement merely to give infrastructure a mapping target.

## Uses And Framework Boundaries

Use `Uses` when the internal logic of an implementation-use-case step relies on another use case. `Uses` identifies that reliance on the referenced use case; it does not by itself claim that the caller realizes the referenced requirements.

Map the workflow step that delegates to or depends on the referenced use case:

```md
Uses:
- validate and commit operation -> UC7
```

The target may be either:

- a declarative use case, whose `Requirements` and `Realized by` layers define the framework boundary and its formal realizations; or
- an implementation use case, which may own a `Requirements` layer directly when one coherent framework workflow both defines and implements the contract.

Use the first form when the framework contract and its realizations each need independently understandable structure. Use the second form when a separate declarative framework use case would add no clarity. Several callers may use the same separately identified framework use case or framework specification; do not duplicate its requirements or realizations under each caller.

For recursive invocation, a `Uses` entry may target the same implementation use case or another use case that eventually calls back. Such self-referential or mutually referential `Uses` mappings describe the recursive call graph and are valid when the recursive family has a reachable exit plus a progress, cycle, or depth-limit contract. This does not relax the prohibition on cycles in `Realized by` / `Realizes` mappings.

## Requirement Representations

Use `Requirement representations` when requirements are translated into another syntax for review, parsing, test generation, code generation, analysis, or visualization.

```md
Requirement representations:

- RP4.1:
  - source: R4.1
  - format: EARS
  - relation: equivalent
  - artifact: inline

- RP4.2:
  - source: R4.1, R4.2
  - format: Gherkin
  - relation: examples
  - artifact: `features/result-publication.feature`

- RP4.3:
  - source: R4.1, R4.2
  - format: RIDDL
  - relation: partial
  - artifact: `domain/result-publication.riddl`
```

Use these relation values when they fit:

- `equivalent`: intended to preserve the complete source requirement;
- `partial`: represents only a declared part of the source semantics;
- `examples`: illustrates selected cases without replacing the requirement;
- `derived`: generated output whose exact coverage is declared separately.

The format and semantic relation are separate decisions. Gherkin commonly provides executable examples. EARS can closely restate behavioral requirements. RIDDL can represent a broader domain, structure, and behavior model for several translation targets. Other formats may be used without changing the canonical relationship.

An EARS entry belongs here only when it duplicates or translates another canonical requirement. When EARS is the canonical body of the requirement itself, keep it directly under `Requirements` and do not create a representation entry merely to repeat it.

Every checked-in representation must retain its source requirement IDs. Prefer generated representations. If a representation is edited independently, define how it is synchronized and which form wins when the two disagree.

Parsing an external representation does not by itself create a complete test. Executable coverage may still require bindings, fixtures, assertions, test data, environment setup, and a declared observable boundary.

## Scenarios And Tests

Do not require one scenario syntax. Scenarios may be written in Gherkin, another BDD language, ordinary workflow notation, or a test framework's native form.

A scenario normally demonstrates part of a requirement. It does not replace the complete normative requirement unless its representation explicitly declares and validates equivalent coverage.

Map tests and scenarios to requirement IDs:

```md
Tests:
- description: incomplete results are rejected without mutating committed state
  requirements: R4.2, R4.3.3
  workflow: incomplete result --validate publication constraints--> rejected result
  expected outcome: the previously committed state remains unchanged
```

## Consistency And Completeness

A complete specification satisfies these checks:

- every requested technical behavior belongs to an implementation use case, a declarative use case, or an identified requirement;
- every requirement is implemented by its owning implementation use case or is realized, explicitly deferred, or declared outside implementation ownership;
- every `Realized by` mapping has a symmetric `Realizes` mapping on its target, whether that target is declarative or implementation-oriented;
- every non-deferred declarative requirement is eventually covered by an implementation use case, directly or through further realizing use cases, unless it is declared outside implementation ownership;
- realization mappings do not form cycles;
- every `Uses` entry belongs to an implementation use case, identifies the source step or state, and resolves to an existing declarative or implementation use case;
- every cyclic `Uses` group represents an intentional recursive family with explicit call targets, a reachable exit, and progress, cycle, or depth-limit behavior;
- requirements and their owning implementation workflow or mapped realizing workflows agree on input, outcome, ordering, failure, and ownership semantics;
- every requirement that references an invariant resolves to that invariant, and its owning or realizing workflow agrees with the invariant derivation;
- every required test or scenario identifies the requirements it covers;
- every external representation declares its source, format, and semantic relation;
- an `equivalent` representation covers all source semantics;
- a `partial` or `examples` representation does not claim completeness;
- observed implementation behavior is not silently promoted into a normative requirement.

## Compact Example

When the workflow and logic are sufficient, keep the implementation use case simple:

```md
### 2. Calculate an output size
source value
--measure and add configured padding-->
output size

Logic Details:
Measure the source value with the active configuration, then add the configured padding.
```

An implementation use case may own its requirements directly:

```md
### 3. Reject an incomplete result
committed state + incomplete result
--reject without mutation-->
unchanged committed state

Requirements:

R3.1: A rejected result SHALL NOT replace or mutate the committed state.

Logic Details:
Validate the complete result before updating committed state.
```

Use a separate declarative parent when several use cases realize the required behavior:

```md
### 4. Produce a complete result
normalized input
--produce and validate the result-->
publishable result

Requirements:

R4.1:
normalized input
--construct all required elements-->
complete candidate

R4.2:
complete candidate
--validate publication constraints-->
publishable result

Realized by:
- R4.1 -> UC4.1
- R4.2 -> UC4.2

### 4.1 Construct the candidate
normalized input
--construct required elements-->
complete candidate

Realizes:
- R4.1
```
