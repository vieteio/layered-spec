---
name: plan implementation in a loop
description: When you need to execute a series of tasks in a loop, updating the plan as you go.
---

<!-- Tip: Use /create-prompt in chat to generate content with agent assistance -->

Work on plan implementation in a loop, where you:
 - classify whether the next task affects a user story, technical use case, shared UI contract, or more than one level
 - pick next task from the plan
 - implement the task
 - ensure that implementation matches the story expectations, technical use-case contract, and UI guidelines in `specs/ui/` when they apply. Run tests, use Playwright MCP to emulate manual tests
 - update story mappings, technical use cases, shared UI contracts, and task state before picking the next task.

1. work in a loop without interruptions until all tasks done.
2. do not stop to offer me two or more options of next development.
select next step by youself according to the plan.
3. if you see, that it is reasonable to extend plan with new tasks, collect few such tasks in a batch and then ask me about the whole batch
4. do not stop after each new task, continue to work in a loop until the batch of new tasks to ask me is collected
