# layered-spec

Compact syntax for layered workflow descriptions that lets you add details gradually during an interactive session with an AI agent. Code can be generated from a complete set of workflow descriptions.

## Community

Join our [Discord](https://discord.gg/jumWsKCCe5) to discuss the spec and skills further development.

## Contributing

Contributions are welcome. To get started:

- **Discuss first** — join the [Discord](https://discord.gg/jumWsKCCe5) or open a GitHub issue to describe your idea before submitting a pull request.
- **Syntax changes** — include a concrete before/after example and confirm that existing README examples remain valid.
- **Skill changes** — share your personal experience of how the skill worked for you to confirm it functions as intended, and describe how the change affects the iterative planning interaction model (`layered-workflow-planning/SKILL.md`).
- **Docs and fixes** — open a pull request directly against `main` with a short description of what changed and why.
- **Bug reports** — open a GitHub issue with a minimal layered-spec example, the expected behavior, and the actual behavior.

## General idea

Solution logic can be fully described in several layers, starting with a workflow diagram and then adding details gradually.

This process can be significantly accelerated in an interactive session with an AI agent.

Compact layered syntax makes this interactive work concise, fast, and convenient.

This repository contains a ready-to-use skill for planning new features interactively with an AI agent.

## Interactive planning approach

Describe the app or new feature in a free-form way to give the AI agent a general understanding.
This can also be a code refactoring task rather than a feature. The workflow syntax supports that, see the syntax below.

Then prepare workflows for each meaningful use case, each of which may start with some trigger such as user input or an API call.

Ask the AI agent to add workflows for any missing use cases.

Next, add layers to some workflows, fill those layers with examples, and ask the AI agent to complete the corresponding layers in other workflows.

Use typed workflows to control data flow strictly.

Recommended layers:

- Workflow
- Types and tables
- Logic
- Events and endpoints
- Detailed typed workflow
- Tests

## Layered syntax

### Workflow syntax

```python
step: state 1 --step name--> state 2
conditional branches: [branch1, branch2, branch3]
parallel branches: (branch1, branch2, branch3)
workflow refactoring: {workflow1} --refactoring step--> {workflow2}
```

Example:

```python
state 1 --step name 1--> state 2 --step name 2--> [
conditional state 1 --branch 1 step--> branch 1 state,
conditional state 2 --branch 2 step--> branch 2 state
] --step name 3--> final state
```

### Layered use cases

```md
### 1. use_case_name
workflow
Layer_1_name: layer content
Layer_2_name:
multi line
layer content
Layer_3_name: multi line
layer
content
```

#### Type or table layer syntax

Type description syntax:

```yaml
Type_name
 - field_name1: optional_type # optional comment; for a table, the field name is a column
 - field_name2: optional_type
   - nested_field_name: optional_type # nested fields are not relevant for tables
```

### Typed detailed workflow layer syntax

After type layers are defined, typed syntax can be used for the detailed workflow.

Syntax:

```python
step: state 1: Type --step name--> state 2: Type
conditional branches: [branch1, branch2, branch3]
parallel branches: (branch1, branch2, branch3)
workflow refactoring: {workflow1} --refactoring step--> {workflow2}
```

Example:

```python
state 1: Tuple[A, B] --step name 1--> state 2: List[X] --step name 2--> [
conditional state 1 --branch 1 step--> branch 1 state,
conditional state 2 --branch 2 step--> branch 2 state
] --step name 3--> final state
```
