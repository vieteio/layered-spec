# layered-design

Compact syntax for layred workflow description, which lets to add details gradually in interactive session with AI agent. Code can be generated from the complete set of workflows descriptions.

## General idea

Solution logic can be fully described in several layers starting from workflow diagram with following graduall details addition.

That process can be highly speed up in interactive session with AI agent.

Compact layered syntax makes this interactive work compact, quick and convenient.

This repo contains ready skill for new feature planning, which enables interactive work with AI agent.

## Interactive planning approach

Describe the app or new feature in a free format to give AI agent general understanding.
That can be even not a feature, but code refactoring task. Workflow syntax supports that, see the syntax below.

Then preapre workflows for each meaningfull use-case, which may start with come trigger like user input or API call.

Ask AI agent to add workflows for missing use-cases.

Next add layer by layer to some workflows, fill layers with examples and ask AI agent to complete other layers.

Use typed workflows to control dataflow stricktly.

Recommended layers:
 - Workflow
 - Types and tables
 - Logic
 - Events and endpoints
 - Detailed typed workflow
 - Tests

## Layered syntax

### Workflow syntax

step: state 1 --step name--> state 2
conditional branches: [branch1, branch2, branch3]
parralel branches: (branch1, branch2, branch3)
workflow refactoring: {workflow1} --refactoring step--> {workflow2}

Example
state 1 --step name 1--> state 2 --step name 2--> [
conditional outcome state 1 --branch 1 step--> branch 1 state,
conditional outcome state 2 --branch 2 step--> branch 2 state
] --step name 3--> final state

### Layered use cases

1. use_case_name
workflow
Layer_1_name: layer content
Layer_2_name:
multi line
layer content
Layer_3_name: multi line
layer
content

#### Type or table layer syntax
Type description syntax:
Type_name
 - filed_name1: optional_type # optional comment, field name for table is a column
 - field_name2: optional_type
   - nested_field_name: optional_type # nested fields are not relevant for tables

### Typed detailed workflow layer syntax
After types layers types syntax for detailed workflow can be used
Syntax:
step: state 1: Type --step name--> state 2: Type
conditional branches: [branch1, branch2, branch3]
parralel branches: (branch1, branch2, branch3)
workflow refactoring: {workflow1} --refactoring step--> {workflow2}

Example
state 1: Tuple[A, B] --step name 1--> state 2: List[X] --step name 2--> [
conditional outcome state 1 --branch 1 step--> branch 1 state,
conditional outcome state 2 --branch 2 step--> branch 2 state
] --step name 3--> final state