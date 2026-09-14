# Changelog

## 0.2.2-alpha

`Requirements` and `Invariants` layers are added into layered-spec.

### Requirements

Layered-spec now supports explicit requirements. For complex products, requirements provide a clear source of truth for the behavior that must be implemented and make development easier to manage as the product evolves.

The new `Requirements` layer records normative behavior separately from implementation details. Declarative use cases provide a higher level of abstraction: they can define requirements without prescribing an implementation, then map those requirements to one or more realizing use cases when implementation details are needed.

### Invariants

The new `Invariants` layer describes properties that must hold at selected workflow states and shows how transition logic derives each outcome invariant from earlier invariants.

Invariant definitions and derivations may use natural language, mathematical notation, pseudocode, Lean, or another named formalism. When formal verification is useful, an AI agent can generate the derivation in Lean and run a proof checker, making it possible to verify the corresponding specification logic.

## 0.2.0

### Layered-spec is partially rewritten using layered-spec

1. Layered-spec lifecycle is now described using layered-specs's own syntax. It is stored in your project's `/specs` folder at `specs/spec-lifecycle/workflow.md`, where it is explicit, easy to review, and fully customizable. You can extend layered-spec now with steps from your own workflow, such as BDD testing and PR preparation.

2. As the first lifecycle customization, this update adds specification completeness and consistency checks. These checks reduce the need for manual spec review and editing.

3. Loop syntax was added to support the changes above, making the layered-spec syntax minimally complete.
