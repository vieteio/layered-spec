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

`Invariants:` is the layer label. Its first-level list items—`Outline`, `Definitions`, `State invariants`, and `Derivations`—are internal subsections, not additional use-case layers. Indent each subsection's content beneath its list item, as shown above; do not write internal subsection labels as unindented peers of `Invariants:`. Omit any internal subsection that adds no value. Keep the outline concise and put long invariant definitions, assumptions, calculations, proofs, and formal text in the detailed entries below it.

## Identifiers And Workflow Mapping

- Give invariant checkpoints stable local identifiers such as `I4.1` when they are referenced by a derivation, requirement, test, or another artifact.
- Give non-trivial derivations stable local identifiers such as `D4.1`.
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
- Long formal or natural-language reasoning stays below the outline.
- Only normative invariant obligations are referenced from `Requirements`.
- A proof is described as verifiable only when successful formal verification is recorded.
