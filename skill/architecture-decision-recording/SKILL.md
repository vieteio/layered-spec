---
name: architecture-decision-recording
description: "Use when an architecturally significant concern must be recorded, applied, updated, or superseded through an ADR, whether the decision comes directly from the user or from solution-basis evaluation. Do not use for a solution-local implementation choice that belongs only in one spec."
metadata:
  version: "0.2.3"
---
# Architecture Decision Recording

Create and maintain architecture decision records independently of any particular lifecycle workflow. An orchestrated workflow may supply task context, basis comparison, related artifacts, and decision status; standalone use may gather the same information directly.

When this skill creates or edits an ADR, follow `skill/layered-spec-core/references/skill-pack-versioning.md`.

## Locations

- Architecture directory: `specs/architecture/`
- Active repository template: `specs/architecture/template.md`
- ADR records: `specs/architecture/ADR-NNNN-<short-title>.md`
- Bundled default template: `assets/default_adr_template.md`
- Optional task context: `specs/task-contexts/CTX-NNNN-<task-slug>.md`
- Optional basis comparison: `specs/<solution-name>/candidates/comparison.md`
- Shared planning contract: `planning/planning_contract.md`

Exclude `architecture/template.md` from ADR discovery. Keep the architecture directory flat until a later architectural decision changes its organization.

## Architectural Significance

Use an ADR when a concern governs several specs or components, establishes a long-lived shared constraint, materially affects a quality attribute, changes a system boundary, or is risky or expensive to reverse.

Keep a choice in its canonical spec when its consequences are confined to that solution and its implementation use cases. When a concern has shared architectural and local application aspects, let the ADR own the shared rule and each consuming spec own only its local parameters or realization details.

## Context Acquisition And Reuse

Use all relevant available sources: the user request, existing ADRs and specs, task context when available, basis artifacts, source code, tests, configuration, operational evidence, and authoritative documentation.

A task-context file is reusable input, not a completeness guarantee or exclusive source. Reuse its relevant directives, findings, and evidence, then inspect original or additional sources when the ADR needs more context. Keep ADR-specific details in the ADR. Write back a finding to an in-scope task context only when it is useful to another artifact or corrects shared understanding.

Preserve useful references to consumed task-context identifiers. Do not promote an observed implementation or inferred finding into an architectural decision without an authoritative task instruction, accepted governance decision, or evidence-backed basis selection.

## Procedure

1. Identify one architectural concern and the authority for deciding it.
2. Inspect relevant proposed, accepted, and superseded ADRs and determine whether the concern uses an existing record, adds non-decision metadata, requires a new record, or changes an accepted decision.
3. Read [adr-lifecycle.md](references/adr-lifecycle.md) when creating a record, changing status, updating an accepted record, or handling supersession.
4. Gather the context and decision drivers needed for this concern. When task context exists, select only its relevant directives, findings, and supporting evidence.
5. If the active template exists, use it unchanged. If it is missing, create the architecture directory when necessary and copy `assets/default_adr_template.md` to `architecture/template.md`. Report an initialization failure and stop; do not silently use the bundled template as a fallback.
6. For a new ADR, allocate the next globally unique sequential identifier from existing `ADR-NNNN-*.md` files and create `ADR-NNNN-<short-title>.md` from the active template.
7. Complete the active template with the decision context, drivers, considered bases or reason comparison was unnecessary, decision, consequences, and affected specifications. Fit provenance into the closest appropriate template section when a user template does not provide a dedicated context-source section.
8. Create a new ADR as `proposed` unless the user or repository decision process explicitly authorizes another status. A direct user instruction can supply the decision without basis comparison, but does not silently change repository acceptance policy.
9. For a proposed architectural basis, keep the ADR `proposed` and reference the consuming spec's basis-validation requirements. Validation execution and result processing are outside this skill's current scope.
10. Add governing ADR references and distinct local consequences to consuming specs. Do not duplicate the ADR's rationale there.

Do not create an ADR for a deferred basis for which no working architectural decision exists. Keep the unresolved concern in its comparison or other owning artifact.

## Quality Checks

- The concern is architecturally significant and has one authoritative ADR.
- The decision authority is explicit.
- Applicable accepted ADRs were preserved or superseded rather than silently contradicted.
- Proposed ADRs are not treated as accepted constraints.
- Context and drivers are sufficient for the decision but exclude unrelated task material.
- Consumed task-context and comparison evidence is linked when useful.
- A proposed basis references its validation requirements without claiming confirmation.
- Affected specs reference the ADR and contain only their local consequences.
- The active template was preserved unchanged.
- No ADR was created for a deferred basis.

## One-Line Heuristic

Record one consequential shared decision once, preserve the evidence and lifecycle around it, and let every consuming spec reference it without copying its rationale.
