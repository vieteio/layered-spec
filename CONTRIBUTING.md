# Contributing to layered-spec

Thank you for your interest in contributing! This guide covers how to get involved with the project.

## Community

Join the [Discord](https://discord.gg/jumWsKCCe5) to discuss ideas, ask questions, and coordinate contributions before opening issues or pull requests.

## Ways to Contribute

- **Improve the layered syntax** — propose additions or clarifications to the workflow, typed workflow, type, table, or tests syntax.
- **Improve the planning skill** — refine the rules, heuristics, or output strategy in `layered-workflow-planning/SKILL.md`.
- **Improve documentation** — fix typos, clarify examples, or add missing sections in `README.md` or other docs.
- **Report issues** — open a GitHub issue describing a problem or limitation you encountered.
- **Share use cases** — open an issue or discussion describing a planning scenario that the current syntax or skill handles poorly.

## Submitting Changes

1. Fork the repository and create a branch from `main`.
2. Make your changes with clear, focused commits.
3. Open a pull request against `main` with a short description of what changed and why.
4. Link any related issue in the pull request description.

## Syntax and Skill Changes

When proposing a change to the workflow syntax or the planning skill:

- Include a concrete before/after example that demonstrates the improvement.
- Confirm that existing examples in `README.md` still parse correctly under the proposed syntax.
- If the change affects the skill interaction model, describe how it affects iterative planning sessions.

## Style Guidelines

- Keep syntax examples minimal and self-contained.
- Use the layer names defined in `SKILL.md` unless proposing a change to those names.
- Write documentation in plain, direct language consistent with the existing README style.

## Reporting Bugs or Requesting Features

Open a GitHub issue and include:

- A short description of the problem or feature.
- A minimal layered-spec example that reproduces the issue or illustrates the request.
- The expected behavior and the actual behavior if reporting a bug.
