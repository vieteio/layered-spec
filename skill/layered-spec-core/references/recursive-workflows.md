# Recursive Workflows

Use this reference when a workflow directly or mutually invokes itself, processes recursively shaped data, dispatches to different recursive steps by data variant, or traverses references that may contain cycles.

Recursion is a relationship between workflow chains. It does not add a new workflow delimiter. Express each chain with the ordinary workflow operators, show each recursive call as a named transition, and reference another use case through `Uses` when the called chain has its own use case.

## Terms

- `recursive family`: the set of workflow chains that can call one another recursively;
- `recursive step body`: one distinct chain in that family, often associated with one recursive data variant;
- `recursive call`: a transition that invokes a chain in the same recursive family;
- `base or exit case`: a reachable path that returns without another recursive call;
- `progress measure`: the property that moves calls toward an exit, such as a strict substructure, shorter remainder, consumed input, or decreasing depth.

## Generation Rules

When generating a recursive workflow:

1. Identify the recursive family and the data variants or conditions that select its step bodies.
2. Generate one workflow chain for every distinct recursive step body.
3. Show every recursive call explicitly and name its target chain or use case.
4. Keep short related chains in one use case under `Detailed Workflow`. Give a compact chain a stable local label such as `recursive-step-a`.
5. Use hierarchical child use cases when recursive step bodies process distinct data variants, contain substantial independent logic, have separate validation or error behavior, or need their own tests.
6. Let the caller own only the call and its continuation. Do not duplicate the called chain's internal logic at each call site.
7. Record the recursive family's reachable base or exit cases and progress measure in `Logic Details`, `Implementation Logic`, or `Invariants`, according to the level of rigor needed.
8. State cycle detection, memoization, maximum depth, or explicit failure behavior when the input contract does not guarantee finite tree-shaped data.

An individual recursive step does not need a local exit when it delegates to another step. The whole self-recursive or mutually recursive family still needs a reachable exit and a termination contract.

## Operator Selection

- Use composition when recursive calls or their continuations are ordered.
- Use a coproduct for type-directed dispatch or alternative base and recursive cases.
- Use a product when independent recursive branches participate together.
- Use a loop when a collection is iterated; keep any recursive call inside the loop explicit.
- Use separate chains when recursive obligations are related by calls rather than by sequence, choice, or parallel participation.

## Template 1: Direct Structural Recursion

```md
### N. Process recursive sequence
sequence: Sequence
--dispatch by sequence shape-->
[
  empty_sequence
  --produce base result-->
  result: Result,

  head_and_tail
  --process tail recursively through UCN-->
  tail_result: Result
  --combine head with tail result-->
  result: Result
]

Uses:
- process tail recursively -> UCN

Logic Details:
- Base case: the sequence is empty.
- Progress measure: the recursive call receives the strict tail.
- Termination: every call reduces the sequence length by one.
```

This self-referential `Uses` entry records invocation. It is not a realization mapping.

## Template 2: Compact Mutual Recursion

Use separate labels when several short recursive step bodies remain readable inside one use case.

```md
### N. Process mutually recursive elements
element: Element
--dispatch by element type-->
[
  element_a --apply recursive-step-a--> result,
  element_b --apply recursive-step-b--> result
]

Detailed Workflow:

- `recursive-step-a`:
  element_a
  --extract nested B-->
  element_b
  --invoke recursive-step-b recursively-->
  result

- `recursive-step-b`:
  element_b
  --inspect B form-->
  [
    terminal_b
    --produce base result-->
    result,

    b_with_nested_a
    --invoke recursive-step-a recursively-->
    nested_result
    --complete B-->
    result
  ]

Logic Details:
- `recursive-step-a` has no local exit and always delegates to `recursive-step-b`.
- Base case: `terminal_b` in `recursive-step-b`.
- Progress measure: every A-to-B or B-to-A transition consumes one enclosing element.
```

## Template 3: Hierarchical Type-Dispatched Recursion

Use hierarchical child use cases when the recursive variants deserve separate workflow ownership.

```md
### N. Process recursive structure
recursive_structure: RecursiveElement
--dispatch by element type-->
[
  element_a --use UCN.1--> result,
  element_b --use UCN.2--> result,
  element_c --use UCN.3--> result
]

### N.1 Process element A
element_a
--inspect nested value-->
[
  A with inner B
  --process inner B through UCN.2-->
  b_result
  --complete A-->
  result,

  terminal A
  --produce base result-->
  result
]

Uses:
- process inner B -> UCN.2

### N.2 Process element B
element_b
--extract nested element-->
nested_element
--dispatch recursively through UCN-->
nested_result
--complete B-->
result

Uses:
- dispatch nested element recursively -> UCN

### N.3 Process element C
element_c --produce terminal result--> result
```

The parent owns type dispatch. Each child owns one recursive variant's logic. Calls return to the caller's continuation after the referenced use case produces its result.

## Template 4: Multiple Recursive Children

Use a product when child computations are independent and their results participate together:

```text
branch(left, right)
--split recursive children-->
(
  left --process recursively through UCN--> left_result,
  right --process recursively through UCN--> right_result
)
--combine child results-->
branch_result
```

Use composition when execution order matters:

```text
branch(left, right)
--process left recursively through UCN-->
branch_with_left_result
--process right recursively through UCN-->
child_results
--combine-->
branch_result
```

Do not use product merely because a node has several children. Select it only when the recursive child computations are independent in the workflow semantics.

## Template 5: Collection Iteration With Recursive Dispatch

When a recursive structure contains a collection of child variants, use a loop for collection iteration and a coproduct for each child's type dispatch:

```text
| for each child element:
  child
  --dispatch by element type-->
  [
    element_a --use recursive-step-a--> child_result,
    element_b --use recursive-step-b--> child_result,
    element_c --use recursive-step-c--> child_result
  ]
  --append-->
  accumulated_results
|
```

The loop controls collection traversal. The referenced step controls recursion over the selected child's recursive shape.

## Template 6: Guarded Graph Recursion

Use an explicit branch when recursive references may revisit an active node:

```md
### N. Traverse referenced nodes
node + active_path
--check recursive path-->
[
  node already in active_path
  --raise recursive-cycle error-->
  recursion_error,

  unseen node
  --add node to active path-->
  active_node
  --process descendants recursively through UCN-->
  descendant_results
  --remove node and assemble result-->
  node_result
]

Uses:
- process descendants recursively -> UCN

Logic Details:
- Base case: the node has no descendants, or a previously completed node has a reusable result.
- Progress measure: traversal advances to an unvisited descendant.
- Active-path repetition raises an explicit error; it is not treated as an empty result.
```

Use a completed-result cache only when reuse is part of the actual behavior. Do not invent memoization as a silent fallback for cycles.

## Quality Checks

- Every distinct recursive step body has one owning workflow chain.
- Every recursive call names its target chain or use case.
- Type-directed dispatch uses a coproduct rather than a flat list of simultaneously processed variants.
- Collection iteration and recursion remain separate structures.
- Every recursive family has at least one reachable base or exit case.
- Every recursive family states a progress measure or explicit cycle/depth-limit behavior.
- A step without a local exit delegates to a step from which a family-level exit is reachable.
- `Uses` cycles represent intentional recursion; `Realized by` / `Realizes` cycles remain invalid.
- Recursive child logic is defined once and is not duplicated at its call sites.
