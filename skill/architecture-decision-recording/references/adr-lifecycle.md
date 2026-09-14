# ADR Lifecycle

Use this reference when creating an ADR, changing its status, updating an accepted record, or handling a replacement decision.

## Statuses

- `proposed`: a concrete decision is recorded for review or validation but is not yet an authoritative repository constraint.
- `accepted`: the repository decision process has accepted the decision; consuming work must follow it while its context remains valid.
- `superseded`: a later ADR replaces the decision. Preserve the historical record and link the replacement.

Do not infer acceptance merely because an ADR file exists, a basis was selected, or implementation began. Use the user's explicit authority and repository process.

## Determine The Operation

For one architectural concern, choose exactly one operation:

- `apply existing`: an accepted ADR remains valid; reference it without rewriting its rationale.
- `update metadata`: the decision is unchanged and only affected-spec links, validation references, or factual non-rationale metadata need synchronization.
- `create`: no ADR records the decision.
- `supersede`: an accepted decision or its governing context changes materially; create a new ADR and preserve the old one.
- `leave unresolved`: no decision is justified, including a deferred basis; create no ADR.

Do not rewrite an accepted ADR's historical context, alternatives, decision, or consequences to make a new decision appear old. A metadata update must not change the meaning of the accepted decision.

## Direct And Evaluated Decisions

A direct user architectural instruction may provide the decision and make basis comparison unnecessary. Record the instruction and its authority in the ADR context, together with the reason alternatives were not evaluated.

When solution-basis evaluation supplies the decision, link its comparison and summarize only the option information needed to understand the ADR. The comparison owns detailed candidate findings.

A proposed basis may be implemented to produce confirmation evidence. Keep its architectural ADR proposed and link the stable basis-validation requirements in the consuming spec. This version records the unresolved requirement but does not execute validation or define how results confirm, revise, or abandon the proposal.

## Context Selection

Select context independently for each ADR:

1. Fix the ADR's decision scope.
2. Reuse relevant task directives and artifact-neutral findings when task context is available.
3. Include supporting evidence needed to understand the forces and drivers.
4. Inspect original or additional sources when the shared context is insufficient.
5. Keep artifact-local implementation details in consuming specs.
6. Write newly discovered shared findings back to an in-scope task context when useful across artifacts.

The ADR must remain understandable without copying the complete task context. Preserve source links and stable identifiers where they add traceability.

## Creation And Supersession

Allocate the next `ADR-NNNN` identifier globally within the flat architecture directory. Never reuse a removed or superseded number.

For supersession:

1. Create the replacement ADR and set its `Supersedes` reference.
2. Restate the continuing architectural rules needed to make the replacement authoritative without consulting the old ADR for current behavior.
3. Mark the old ADR `superseded` and add a `Superseded by` reference without rewriting its historical rationale.
4. Redirect consuming specifications to the replacement ADR.

## Affected Specifications

List every known consuming spec and state how it is governed. A planned spec may be named before it exists and synchronized after creation. Consuming specs reference the ADR and own only distinct local parameters, workflows, or realization details.
