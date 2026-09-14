## Use cases

### 4. Process mutually recursive elements
element: Element
--dispatch by element type-->
[
  element_a --apply recursive-step-a--> result,
  element_b --apply recursive-step-b--> result
]

Detailed Workflow:

The following two chains are one recursive family. The caller resumes after its child returns.

- A documentation bullet, with no workflow declaration.

- `recursive-step-a`:
  element_a
  --extract nested B-->
  element_b
  --invoke recursive-step-b recursively-->
  result

This paragraph explains the base case. Its inline `a --call--> b` is an example only.

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

Some additional explanation may occur between chains.

input --prepare--> prepared

#### fenced-step

```text
prepared --finish--> output
```

Closing documentation remains Markdown.

Logic Details:
- Base case: terminal_b.
- Progress measure: consume one enclosing element at each recursive call.
