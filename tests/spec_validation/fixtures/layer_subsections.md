# Grouped layers

## Use cases

### 1. Build
input --build--> result

Requirements:
- Contract:
  R1: The result includes every input item.

Realized by:
- Implementation:
  - R1 -> UC2

Workflow anchors:
- Transitions:
  - step1: build

Tests:
- Coverage:
  - requirements: R1

Logic:
- Design considerations:
  Keep ordering stable across retries.

Detailed Workflow:
- Execution:
  Process and validate each item.

  - process-item:
    item --process--> processed item

  processed item --validate--> checked item

- Notes:
  An empty input produces an empty result.

### 2. Process input
input --process--> result

Realizes:
- Parent contract:
  - UC1/R1
