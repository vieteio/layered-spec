# layered-spec

![Visitors](https://visitor-badge.laobi.icu/badge?page_id=vieteio.layered-spec)


Compact syntax for spec-programming which makes AI code generation **predictable** for well-decomposed tasks and speed up development.

> **✨ New!** Layered-spec now includes a User-stories level, supplementing spec with a context, UI layers and e2e tests.

## General idea

Solution logic can be fully described in several layers, starting with a workflow chain and then adding details gradually.

AI-agent generates high quality specs from task in chat.
First 1-3 layers are for review by a user, remaining layers are for reliable code generation by AI.

Compact layered syntax makes spec driven development concise, fast, and convenient.

## Quick start

1. Install spec skills
```bash
npm install -g @viete-io/layered-spec@latest
cd your-project
layered-spec init
```
2. Describe task in a chat and add "Make spec for that" or "Update spec for that"

3. Review spec and refine it in chat with AI

4. When spec is ready, write in chat "Implement the spec" or "Implement spec update"

### Spec driven vibecoding

Skip spec review step.

Limit your work to
1. Describe task and add "Make spec for that"
2. Next message in chat "Implement the spec"

AI agent will decompose moderate level complexity tasks well into use-cases with detailed workflow chains and then will generate code properly for well decomposed tasks.

## Skills

This repository contains a layered-spec skillpack for planning new features or refactoring through chat with an AI agent.

Canonical skill sources live under:

- `skill/` — skill definitions
- `planning/planning_contract.md` — spec structure description
- `prompts/` — supporting prompt files used by the planning loop

Describe a task in chat with an AI agent and ask it to create a spec. Review the spec and refine it in chat. When the spec is correct, ask the agent to implement it in a loop.

### Install skills for your IDE or agent

#### npm

```bash
npm install -g @viete-io/layered-spec@latest
cd your-project
layered-spec init
```

Requires Node.js 20.19.0 or later.

#### Python installer

Clone this repository, then run the existing Python installer from its root:

```bash
python scripts/install_skillpack.py --host <host_name> 
```

Requires Python 3.10 or later.

#### Installer options

`init` installs all supported hosts by default: `vscode`, `cursor`, `claude`, `codex`, and `antigravity`. Use `--host <host_name>` to install only one host.

Repo-scoped installs place skills under each host's expected directory (for example `.github/skills/` for VS Code / GitHub Copilot, `.cursor/skills/` for Cursor). The installer rewrites internal path references to match the selected host while keeping generated specs in `specs/`.

## Demo project

See the [layered-spec meetup demo](https://github.com/vieteio/layered-spec-meetup-demo) project with spec and AI-agent chat log in the repo.

## User-stories

**✨ New!** User stories are added as a new level. They are extracted automatically from tasks descriptions in a chat.

User stories are separated well from specifications. A user story describes an end-to-end scenario, including the user's actions and the application's responses. A spec describes only application actions, so each action begins with an event—most often one initiated by the user.

User stories also include UI layers that describe the interface the user interacts with during the scenario.

## Recommended spec layers:

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

## Contributing

Contributions are welcome. To get started:

- **Discuss first** — join the [Discord](https://discord.gg/jumWsKCCe5) or open a GitHub issue to describe your idea before submitting a pull request.
- **Syntax changes** — include a concrete before/after example and confirm that existing README examples remain valid.
- **Skill changes** — describe the purpose of new or existing skill update, share your personal experience of how the skill worked for you to confirm it functions as intended.
- **Docs and fixes** — open a pull request directly against `main` with a short description of what changed and why.
- **Bug reports** — open a GitHub issue with a minimal layered-spec example, the expected behavior, and the actual behavior.

## License

Released under the MIT License — free for commercial and non-commercial use.
