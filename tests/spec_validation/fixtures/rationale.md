## Use cases

### 1. Construct
validated input --normalize representation--> canonical input --construct result--> completed result

Invariants:
- Rationale:
  - `N1`:
    - note: Canonicalization preserves the accepted meaning.
    - assessment: supported
    - used by: D1
  - `N2`:
    - note: Canonical input is enough to construct a complete result.
    - assessment: qualified
    - qualification: Construction must cover every required element.
    - used by: D2
  - `N3`:
    - note: Input validation guarantees a complete result.
    - assessment: rejected
    - reason: Validation does not construct the result.
    - replacement: Construction establishes completeness.
  - note: Performance is sufficient.
    - assessment: unsupported
    - reason: Measurements are unavailable.

- State invariants:
  - `I1` at `validated input`: Input is valid.
  - `I2` at `canonical input`: Meaning is preserved.
  - `I3` at `completed result`: Result is complete.

- Derivations:
  - `D1: I1 -> I2`
    - workflow transition: `normalize representation`
    - justification: Normalization preserves meaning.
  - `D2: I2 -> I3`
    - workflow transition: `construct result`
    - justification: Construction establishes each required element.
