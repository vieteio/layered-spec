## Use cases

### 1. Validate and build
raw input --validate--> validated input --build--> complete result

Requirements:
R1.1: The result is complete.

Invariants:
- Outline:

  ```text
  I1 @ validated input --D1: build--> I2 @ complete result
  ```

- Definitions:

  - `Complete(x)`: all required elements are present.

- State invariants:

  - `I1` at `validated input`: Input is valid.
  - `I2` at `complete result`: `Complete(result)`.

- Derivations:

  - `D1: I1 -> I2`
    - workflow transition: `build`
    - justification: Construction preserves all required elements.

Tests:
 - description: A complete result is produced.
   requirements: R1.1
   expected outcome: All required elements are present.
