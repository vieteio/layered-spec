## Design-System Synchronization

For any UI, UX, styling, iconography, or visible component-state change, use these repository-local documents as source of truth when they exist:

- `specs/ui/layout-wireframes.md` for layout and spatial structure
- `specs/ui/style-and-icons.md` for icon roles, selection treatments, and semantic color usage

Required workflow:

1. Read the relevant sync document before making a design decision.
2. If the visible layout changes, update `layout-wireframes.md` in the same change and map it from the story-specific UI state when a user story exists.
3. If a new visual role, selection style, status color meaning, or icon decision is introduced, update `style-and-icons.md` in the same change.
4. Do not use different icons or different color semantics for the same role without first updating the contract.

Implementation rules:

- Use the repository's established icon system for recurring UI roles.
- Prefer semantic colors or design tokens over one-off raw color values for shared roles.
- Treat the docs above as synchronization points, not optional notes.
