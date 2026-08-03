---
name: design-ux-guardrails
description: "Use when: designing or reviewing UI so layouts stay resilient under real content, interactive areas are never unexplained, and user flows remain legible across states and screen sizes. Synchronize story UI states with shared layout and style/icon contracts when they exist."
user-invocable: true
argument-hint: "Describe the UI surface, task mode, and whether you need design guidance, review, or wireframe updates before implementation."
---
# Design UX Guardrails

Use this skill when designing or reviewing UI so layouts stay resilient under real content, interactive areas are never unexplained, and user flows remain legible across states and screen sizes.

## Supporting Artifacts

- `references/design-system-sync.md`
- `skill/user-story-workflow-documentation/SKILL.md` when the UI belongs to a user-story workflow

## Use This Skill When

- the user asks for a new screen, component, or layout direction
- an existing UI needs usability or information-density improvements
- a design should be reviewed before implementation
- the task includes dynamic content, empty states, forms, lists, cards, panels, dialogs, or dashboards
- the goal is to avoid brittle layouts, silent empty areas, or confusing interaction states

## Do Not Use This Skill When

- the task is backend-only and has no user-facing surface
- the change is a small cosmetic tweak with no layout or interaction implications
- the user explicitly wants raw implementation without design reasoning

## Goal

Produce UI guidance or review output that:

- defines how the interface behaves with real, long, short, missing, loading, and erroneous content
- keeps interactive areas self-descriptive before the user has added any data
- makes overflow, truncation, wrapping, scrolling, and resizing decisions explicit
- preserves hierarchy, readability, and action clarity across desktop and mobile widths
- captures the missing UX states that usually cause regressions during implementation

## Core Rule

Do not design from the happy path only.

For every meaningful region, account for:

- maximum and minimum content size
- empty and first-use state
- loading, error, disabled, and success state when relevant
- narrow viewport behavior
- keyboard and accessibility behavior

## Guardrails

### 1. Bound Dynamic Content Explicitly

For every UI element that renders dynamic content, define the maximum space it may occupy and the fallback behavior once content exceeds that space.

Examples:

- single-line labels: truncate with ellipsis and expose full text through tooltip, expansion, or detail view
- multi-line text: wrap, clamp to a fixed number of lines, or place in a bounded scroll area
- media or previews: crop, letterbox, or constrain aspect ratio instead of letting layout break
- tables and lists: define column priorities, wrapping rules, and overflow strategy on narrow widths

Never leave overflow behavior implicit.

### 2. Do Not Leave User-Fill Areas Empty

Any region intended for user-created or interaction-created content must remain self-descriptive before the first item exists.

Use placeholders such as:

- short instructions
- call to action text
- starter templates
- example content
- recent or suggested items
- default selections when appropriate

Choose the placeholder that best reduces first-use friction for that specific surface.

### 3. Design All Core States Up Front

For each surface, explicitly cover the states that affect user comprehension:

- empty
- loading
- loaded
- error
- disabled
- saving or in-progress
- success or completion
- hover, focus, selected, and destructive states when interactive

If a state exists in runtime but not in design, implementation quality usually collapses.

### 3a. Write UI Copy From User-Visible Context

When naming labels, captions, helper text, or empty-state copy, distinguish between:

- context the agent knows from specs, code, stores, persistence, or internal workflows
- context the user can infer from the visible UI, current panel, nearby controls, and current task state

Write microcopy from the second set.

Rules:

- do not surface implementation details the user cannot act on or observe directly
- avoid codebase-only storage, transport, synchronization, or computation terminology unless the UI already teaches that concept explicitly
- use wireframes, visible layout contracts, and the active screen state to infer what the user can actually see around the current copy
- when wireframes or static code context are insufficient and tooling allows it, inspect the live page, rendered markup, or screenshots to verify what is actually visible to the user
- include not only the local control, but also the surrounding visible UI: the current surface, nearby sections, available actions, adjacent panels, and obvious local state
- rely on that visible context to shorten labels instead of restating the whole internal story
- prefer short sentences over dense explanatory clauses when the text is shown repeatedly

Microcopy should answer what this is and what the user should understand from it, not how the app stores or computes it.

### 4. Preserve Layout Stability

Avoid large layout shifts during async loading, validation, expansion, or content arrival.

Reserve space when possible for:

- skeletons or loading placeholders
- validation messages
- inline actions
- badges, counters, and status indicators

Prefer stable containers over interfaces that jump after each user action.

### 5. Keep Primary Actions Unambiguous

Every screen should make the next recommended action visually obvious.

Rules:

- one clear primary action per zone when possible
- secondary and destructive actions must not visually compete with the main task
- destructive actions need stronger confirmation or reversal support than neutral actions

### 6. Make Constraints Visible Before Failure

Do not force the user to discover format rules or content limits through errors alone.

Surface constraints early with:

- field hints
- examples
- unit labels
- character or item limits
- accepted formats

Validation should confirm and refine, not introduce the rules for the first time.

### 7. Optimize For Scanning Before Decoration

Strong UX depends on fast comprehension.

Use layout decisions that improve scan speed:

- clear visual grouping
- consistent spacing rhythm
- aligned labels and values
- predictable placement of controls
- restrained emphasis so only the most important items dominate

### 8. Treat Narrow Width As A First-Class Case

Do not assume desktop width is the real layout and mobile is a later compression step.

For each surface, define:

- what collapses
- what wraps
- what becomes scrollable
- what gets hidden behind progressive disclosure
- what must remain pinned because it is critical for orientation or action

### 9. Pair Empty States With Next Actions

An empty state should do more than explain absence.

It should also help the user move forward through:

- one suggested next action
- a template or example
- a shortcut to create the first item
- contextual explanation of why the area matters

### 10. Keep Interaction Feedback Immediate

Every significant user action needs visible feedback near the point of interaction.

Examples:

- loading indicator for submitted actions
- inline confirmation after save
- precise error near the failed field or action
- visible selected state for toggles, rows, tabs, or cards

Avoid making users infer whether the system accepted the action.

### 11. Make Dense Surfaces Progressively Legible

When a screen contains many controls or a lot of data, reduce cognitive load by staging complexity.

Use:

- progressive disclosure
- sensible defaults
- grouping into sections
- pinned summaries or headers
- filters and sorting only where they materially improve retrieval

### 12. Design Accessibility As Structure, Not Polish

Accessibility is not a late QA pass.

Account for:

- keyboard reachability
- focus visibility
- contrast
- semantic grouping and naming
- non-color cues for status and validation
- readable touch targets and pointer targets

### 13. Maintain A Wireframe As The Spatial Contract

When a visible layout change happens, update the wireframe first.

Use the wireframe to catch:

- unintended same-layer overlap
- missing space for growth states
- broken hierarchy
- narrow-width collisions

This targets base-layout collisions, not intentional layered UI such as:

- context menus
- popovers and tooltips
- dialogs and modal backdrops
- mobile drawers and navigation panels
- draggable floating windows

For intentional overlap, define:

- layer type
- trigger and placement
- stacking
- focus and dismissal
- background interaction

ASCII wireframes are usually enough.

Rules:

- keep wireframes for the key states, not only the happy path
- update them when visible structure changes
- do not implement while overlap risk or layer rules remain undefined
- treat the wireframe as the layout contract

Use `specs/ui/layout-wireframes.md` as the maintained shared wireframe contract when the repository has one. Put story-specific UI states and wireframes in the related file under `specs/stories/`, then map that state to the shared contract only when it changes reusable layout behavior.

### 13a. Maintain A Style And Icon Contract For Repeated Roles

When a visual role is reused across surfaces, document its canonical treatment instead of letting each component improvise.

Use `specs/ui/style-and-icons.md` as the visual contract when the repository has one for:

- icon choice for a role
- selected-row treatment
- semantic color meaning
- repeated status affordances
- menu versus overflow affordances

Rules:

- if two controls have the same role, they should use the same icon semantics
- if a new repeated role is introduced, add it to the contract in the same change
- do not treat the contract as optional documentation after implementation
- use the style contract together with the wireframe contract

### 14. Allocate Space For Future Growth, Not Only Current Content

Do not place new UI by filling the last visible gap in the current mockup.

Before adding an element, evaluate:

- what adjacent regions can grow later
- where validation, helper text, badges, and status messages may appear
- whether the new element creates a collision risk in dense or translated content
- whether the layout still works after one more related control is added later

Prefer layouts with explicit rows, columns, zones, and spacing budgets over ad hoc placement.

### 15. Split Overloaded Layouts Into Clearer Surfaces

When one screen accumulates too many elements, do not assume everything must remain visible at once.

If density, overlap risk, or scan difficulty becomes too high, consider restructuring the UI into:

- separate screens or routes
- modal or non-modal side panels
- drawers, menus, or popovers
- tabs or segmented views
- accordions or expandable sections
- multi-step flows when the task is sequential

Choose the split based on task structure:

- use separate screens when the user is switching context or entering a different task mode
- use floating surfaces when the secondary content is temporary, contextual, or needs quick dismissal
- use accordions or progressive sections when content belongs to the same task but should not compete at once
- use step flows when showing all inputs simultaneously would increase error rate or cognitive load

Do not split content only to hide layout problems. Split when it improves comprehension, focus, or task completion.

After splitting, verify:

- the primary task on each surface is clearer than before
- hidden content is still discoverable
- navigation between surfaces is explicit
- users can return without losing orientation or work
- the new surface does not become a second overloaded layout

### 16. Use One Spatial Review Checklist

When the visible structure changes, run one compact checklist that covers both base layout and intentional overlays.

Checklist:

- wireframes updated for the relevant states
- no unintended base-layer overlap or hierarchy break
- growth space exists for content, validation, and async states
- intentional overlays have explicit layer and interaction rules
- scrolling, clipping, and pointer behavior are intentional

## Workflow

### 0. Locate The Story And Shared Contract

When the request changes a user-visible workflow, first identify the related user-story state or create it through `user-story-workflow-documentation`.

- Keep a state-specific wireframe, visible expectation, and technical mapping in the story.
- Keep shared geometry in `specs/ui/layout-wireframes.md`.
- Keep reusable visual roles in `specs/ui/style-and-icons.md`.
- Do not copy a shared rule into each story or promote a one-off story detail into the shared contract without reuse value.

### 1. Inventory The Surface

Identify:

- the user goal
- the main regions on screen
- the actions available in each region
- the dynamic data each region can contain

### 2. Map Content Extremes

For every dynamic region, state:

- shortest realistic content
- longest realistic content
- empty content
- async content
- invalid or failed content

Then define the containment strategy for each extreme.

### 3. Define First-Use And Empty States

For every user-fill or interaction-fill area, specify:

- what appears before content exists
- why that placeholder helps the user
- what action the placeholder should encourage

### 4. Specify Responsive Behavior

Describe what changes across width ranges:

- layout stacking or splitting
- content truncation or wrapping rules
- scroll containers
- pinned controls or headers
- hidden or collapsed secondary actions

### 5. Update The Spatial Contract

Produce or refresh wireframes for:

- the primary use case
- the empty or first-use state
- the densest realistic state
- the narrow-width version when layout changes materially

Then run the spatial review checklist. Do not continue until it passes.

### 6. Cover Interaction States

For each important action, define:

- idle appearance
- hover and focus behavior
- disabled behavior
- in-progress behavior
- success or failure feedback

### 7. Run The Guardrail Check

Before finalizing, verify:

- no dynamic content can break the layout silently
- no intended content area is blank and unexplained
- the wireframe has been updated for any visible layout change
- the style and icon contract has been updated for any new repeated visual role
- the story UI state maps to the technical use case when the change belongs to a user journey
- new base-layer elements do not intersect with existing base-layer elements in dense or narrow states
- intentionally overlapping elements have explicit layer, focus, dismissal, and interaction rules
- every core user action has visible feedback
- the primary action is obvious
- narrow-width behavior is intentional
- accessibility is covered structurally

## Output Format

When using this skill, structure the response around:

### UI Intent

- user goal
- primary action
- critical regions

### Dynamic Content Rules

- region-by-region size and overflow decisions

### Empty And Placeholder Strategy

- what appears before user content exists
- how that state prompts action

### State Coverage

- loading, empty, error, disabled, success, and selected states as relevant

### Responsive Behavior

- breakpoint or narrow-width adaptations

### Wireframes

- ASCII wireframes for the key states
- short notes for overlap avoidance or layer rules when needed

### Spatial Review Checklist

- a short pass/fail checklist covering both layout collisions and intentional overlay rules

### Spatial Review Template

Use this compact template when reporting a UI change review:

```text
Spatial review

- Wireframes: updated for [states] / missing [states]
- Base-layer overlap: pass | fail
- Growth space: pass | fail
- Hierarchy after change: pass | fail
- Intentional overlays: none | defined | missing rules
- Overlay rules: trigger [ok/missing], placement [ok/missing], stacking [ok/missing], focus [ok/missing], dismissal [ok/missing], background interaction [ok/missing]
- Long or async content: pass | fail
- Scroll or clipping risks: none | described | unresolved

Required follow-up

- [action item]
- [action item]
```

Keep the template short. Only expand the failing lines.

### Risks And Missing Decisions

- unresolved UX questions that need product input before implementation

## Quality Checks

A strong result from this skill must satisfy all of these:

- names the primary action and user goal
- defines overflow behavior for every major dynamic region
- provides placeholders for user-fill areas instead of leaving them blank
- covers empty, loading, and error states where relevant
- explains narrow-width behavior explicitly
- includes updated wireframes when the visible structure changes
- maps story-specific UI states to the shared contract and technical use cases when a user story exists
- distinguishes intentional overlays from accidental collisions
- includes immediate feedback for important interactions
- accounts for keyboard and accessibility behavior

## Common Failure Modes

- designing only the ideal data case
- leaving large empty panels with no guidance or next action
- using truncation without any recovery path to the full content
- relying on color alone for meaning
- adding actions everywhere so the main task loses priority
- letting validation or async status move content unpredictably
- adding a new element without redrawing the affected layout
- banning valid overlays instead of defining their layering and interaction rules
- compressing desktop layouts into mobile without rethinking hierarchy

## One-Line Heuristic

Design every surface as if the content will be longer than expected, the viewport will be narrower than expected, and the user will arrive with no prior context.
