## Use cases

### 1. Build
input --build--> result

Invariants:
- State invariants:
  - `I1` at `input`: Input is valid.
  - `I2` at `result`: Result is complete.

- Derivations:
  - `D1: I1 -> I2`
    - workflow transition: build
    - justification: Construction supplies every required result element.

- Design considerations:
  - The representation may change later.
  - Keep this explanation separate from the derivation above.

- Alternatives:
  A different representation could reduce storage.

- Design considerations:
  These notes concern a later optimization.

- Rationale:
  - `N1`:
    - note: Construction covers the required elements.
    - assessment: supported
    - used by: D1
