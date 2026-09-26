# Invariants Layer

Use an `Invariants` layer when selected workflow states have meaningful invariants and the derivation of later state invariants should be explicit. The layer forms a selective parallel chain over the main workflow: it may skip states that have no useful invariant and one derivation may cover one or several workflow transitions.

An invariant is a predicate or guaranteed property associated with a named workflow state. A derivation explains why one or more invariants at earlier states are preserved, combined, or otherwise used to establish invariants at a later state.

Do not add invariants mechanically to every state. Add the layer only when the invariants or their derivation materially clarify required behavior, implementation correctness, review, or future verification.

## Shape

Use this shape when all parts are useful:

````md
Invariants:
- Outline:

  ```text
  I1 @ validated input
    --D1: normalize representation-->
  I2 @ canonical input
    --D2: construct result-->
  I3 @ completed result
  ```

- Rationale:

  - `N1`:
    - note: Canonicalization should preserve the accepted meaning of the input.
    - assessment: supported
    - used by: D1
  - `N2`:
    - note: A canonical input should be sufficient to construct a complete result.
    - assessment: qualified
    - qualification: Completeness also depends on the construction step covering every required result element.
    - used by: D2
  - `N3`:
    - note: Successful input validation alone guarantees a complete result.
    - assessment: rejected
    - reason: Validation constrains the input but does not construct the result; completeness requires separate construction reasoning.

- Definitions:

  - `Valid(x)`: `x` satisfies the accepted input constraints.
  - `Equivalent(a, b)`: `a` and `b` have the same accepted meaning.
  - `Complete(r)`: `r` contains every required result element.

- State invariants:

  - `I1` at `validated input`: `Valid(input)`.
  - `I2` at `canonical input`: `Valid(canonical_input)` and `Equivalent(input, canonical_input)`.
  - `I3` at `completed result`: `Complete(result)` and the result is derived from `canonical_input`.

- Derivations:

  - `D1: I1 -> I2`
    - workflow transition: `normalize representation`
    - justification: Normalization preserves the accepted meaning while producing the canonical representation.
  - `D2: I2 -> I3`
    - workflow transition: `construct result`
    - justification: Construction consumes the canonical input and establishes every required result element.
````

`Invariants:` is the layer label. Its first-level list items—`Outline`, `Rationale`, `Definitions`, `State invariants`, and `Derivations`—are internal subsections, not additional use-case layers. Indent each subsection's content beneath its list item, as shown above; do not write internal subsection labels as unindented peers of `Invariants:`. Omit any internal subsection that adds no value. Keep the outline concise and put long rationale, invariant definitions, assumptions, calculations, proofs, and formal text in the detailed entries below it.

## Rationale

Use the optional `Rationale` subsection when a developer supplies ideas explaining why proposed solution logic should work or why a direction should lead to a correct solution. A rationale is input to solution and proof development; it is not itself an invariant or an accepted derivation.

Preserve the supplied meaning rather than silently rewriting it into a correct argument. Give a rationale note a stable local identifier such as `N1` when an assessment, derivation, decision, or question refers to it.

Assess each retained rationale note with one of these values:

- `supported`: the rationale is correct and relevant enough to guide invariant selection or derivation;
- `qualified`: part of the rationale is useful after an explicit correction, limitation, or additional condition;
- `unsupported`: available information does not establish the rationale, but does not show it to be incorrect;
- `rejected`: the rationale is completely incorrect, and the correct justification, solution, or direction is different.

For `qualified`, state the qualification. For `unsupported` or `rejected`, state the reason; for `rejected`, identify the replacement justification, solution, or direction when it is known. Only `supported` and explicitly qualified parts may be cited by `used by` as inputs to derivations. Every derivation must remain understandable and justified without treating a rationale note or its assessment as proof.

An assessment records the planning judgment supported by currently available reasoning and evidence. It is not formal verification and does not make a rationale a verifiable proof.

A note that is not referenced can omit its identifier:

```md
- Rationale:
  - note: This direction still needs evidence.
    - assessment: unsupported
    - reason: The required measurements are not available.
```

Indent continuation text, nested lists and fenced blocks beneath the field they belong to.

Use comma-separated derivation references in `used by`, for example `D1, UC4/D4.1` or `other.md#use-case Build/D2`.

## Identifiers And Workflow Mapping

- Give invariant checkpoints stable local identifiers such as `I4.1` when they are referenced by a derivation, requirement, test, or another artifact.
- Give non-trivial derivations stable local identifiers such as `D4.1`.
- Give retained rationale notes stable local identifiers such as `N4.1` when they are referenced by an assessment, derivation, decision, or question.
- Qualify cross-use-case or cross-artifact references with their owner, for example `UC4/I4.1`.
- Associate every invariant with a state named in the main workflow or identify the corresponding use-case state unambiguously.
- Associate every derivation with the workflow transition or consecutive transition span whose logic establishes the target invariant.
- A derivation may consume several source invariants and establish one or several target invariants, for example `D4.3: I4.1, I4.2 -> I4.4`.
- A preservation derivation may restate the same invariant at a later checkpoint; use distinct checkpoint identifiers when the source and target assertions must be referenced separately.

The invariant outline uses the shared workflow operators when branches, parallel inputs, or loops matter. It remains an outline rather than a container for the complete proof.

## Invariant Definitions, Derivations, And Proofs

State invariants and derivations may use natural language, mathematical notation, pseudocode, a proof assistant such as Lean, or another named formalism. Use the representation that communicates the property and its derivation most precisely.

- Keep notation definitions, domains, assumptions, and referenced workflow states close to the invariant or derivation that needs them.
- Use KaTeX for mathematical invariants and derivations when it improves clarity.
- Use fenced code blocks with an appropriate language tag for formal or executable text.
- Natural-language reasoning may be called a proof, justification, or proof sketch according to its completeness.
- Call text a **verifiable proof** only when it is expressed in a formalism and successfully verified by the corresponding checker.
- Formal-looking text is not a verified result by itself. Record the checker and verification result when that distinction matters.

The layer may express a base case, an inductive step, loop preservation, termination reasoning, branch-specific guarantees, composition rules, or a direct derivation between selected workflow states. Do not require one proof pattern for every workflow.

## Relationship To Requirements

An invariant is not automatically a normative requirement. The `Invariants` layer defines selected state invariants and explains their derivation. The `Requirements` layer remains the source of normative obligations.

When a requirement and invariant belong to the same use case, the requirement may reference the invariant:

```md
Requirements:

  R1:
A completed result satisfies `I3`.
```

The referenced invariant defines the required state condition, and its derivations provide the proof, justification, or proof sketch showing how the workflow establishes it.

When the invariant belongs to a realizing use case rather than the requirement owner, keep the requirement definition self-contained. Use the normal `Realized by` / `Realizes` mapping, and let the realizing use case's invariant derivation identify the requirement it justifies. `Invariants` does not replace `Realized by`, `Realizes`, `Uses`, tests, or requirement-representation mappings.

Do not promote an invariant observed in current implementation into a requirement without an authoritative requirement source or explicit planning decision.

## Technical Boundary

A technical use case may use `Invariants` for application-owned, algorithmic, representation, safety, or other implementation-relevant invariants and their derivations.

## Quality Checks

- Every invariant belongs to a meaningful named workflow state.
- Every derivation identifies its source invariant or invariants, target invariant or invariants, and corresponding workflow transition or transition span.
- The outline agrees with the detailed invariant and derivation entries.
- Every retained rationale note has an assessment; qualified notes state their qualification, unsupported or rejected notes state their reason, and rejected notes identify the replacement justification, solution, or direction when known.
- Only supported rationale and explicitly qualified parts are cited by derivations, and rationale never substitutes for derivation reasoning.
- Long formal or natural-language reasoning stays below the outline.
- Only normative invariant obligations are referenced from `Requirements`.
- A proof is described as verifiable only when successful formal verification is recorded.
