# layered-spec

![Visitors](https://visitor-badge.laobi.icu/badge?page_id=vieteio.layered-spec)


Compact syntax for spec-programming which makes AI code generation **predictable** for well-decomposed tasks and speed up development.

## General idea

Solution logic can be fully described in several layers, starting with a workflow diagram and then adding details gradually.

AI-agent generates high quality specs from task in chat.
First 1-3 layers are for review by a user, remaining layers are for reliable code generation by AI.

Compact layered syntax makes spec driven development concise, fast, and convenient.

## New! Layered-spec is partially rewritten using layered-spec

1. Layered-spec lifecycle is now described using layered-specs's own syntax. It is stored in your project's `/specs` folder at `specs/spec-lifecycle/workflow.md`, where it is explicit, easy to review, and fully customizable. You can extend layered-spec now with steps from your own workflow, such as BDD testing and PR preparation.

2. As the first lifecycle customization, this update adds specification completeness and consistency checks. These checks reduce the need for manual spec review and editing.

3. Loop syntax was added to support changes above, making the layered-spec syntax minimally complete.

## Quick start

1. Install spec skills
```bash
npm install -g @viete-io/layered-spec@latest
cd your-project
layered-spec init
```
2. Describe task in a chat and add "Make spec for that" or "Update spec for that"

3. Then review spec and edit it in chat with AI

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

Spec lifecycle files live under:
- `specs/spec-lifecycle/workflow.md` — repository lifecycle workflow that users can review and customize

Describe a task in chat with an AI agent and ask it to create a spec. Review the spec and refine it in chat. When the spec is correct, ask the agent to implement it in a loop.

### Install skills for your IDE or agent

#### npm

```bash
npm install -g @viete-io/layered-spec@latest
cd your-project
layered-spec init
```

Requires Node.js 20.19.0 or later.

#### Select a release version

The default install always uses the newest stable release (`latest`):

```bash
npm install -g @viete-io/layered-spec
# equivalent: npm install -g @viete-io/layered-spec@latest
```

Use `next` to try the newest prerelease, or use an exact version to keep an installation reproducible:

```bash
npm install -g @viete-io/layered-spec@next
npm install -g @viete-io/layered-spec@0.2.0-alpha.0
```

To return to the stable release, install `@latest` again. The selected package version is recorded in `.agents/layered-spec-skillpack.json` (or the selected host's equivalent manifest) when you run `layered-spec init`.

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
workflow loop: | loop condition: input --step name--> outcome |
```

Place loop workflows in fenced text blocks or inline code so the enclosing `|` characters are not interpreted as a Markdown table.

Example:

```python
state 1 --step name 1--> state 2 --step name 2--> [
  conditional state 1 --branch 1 step--> branch 1 state,
  conditional state 2 --branch 2 step--> branch 2 state
] --step name 3--> final state

| process each file: file --perform analysis--> report |

| while unfinished work items remain:
  current work state --select next item--> selected item
  --process item--> updated work state |
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
