# Mixed planning document

## Rendering architecture

### 2. This explanation is not a use case

Realizes:
- UC999/R999

## Use cases

### 4. Render the diagram workflow graph view
input --render graph--> diagram

Requirements:
R4.1: The diagram contains all required elements.

Requirement: Configuration requirement
The selected configuration is valid.

Requirement: 4.1
This identifier is distinct from R4.1.

Realized by:
- R4.1 -> UC7
- requirement Configuration requirement, requirement 4.1 -> use-case Check configuration

### UC7 — Construct elements
input --construct elements--> elements

Realizes:
- use-case Render the diagram workflow graph view/requirement R4.1

### Check configuration
configuration --check--> accepted configuration

Realizes:
- use-case 4/requirement Configuration requirement, use-case 4/requirement 4.1

Extension/Examples:
Input: this is body text.

```md
### 999. Not a declaration

Realizes:
- UC999/R999
```

## Notes

### 7. This numbered explanation is outside the region
