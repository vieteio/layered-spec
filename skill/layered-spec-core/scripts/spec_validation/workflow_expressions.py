"""UC7: one source-located expression parser for main and embedded workflows."""

from __future__ import annotations

import re

from .models import (
    DocumentSnapshot, SourceSpan, WorkflowConditional, WorkflowExpression, WorkflowLoop,
    WorkflowParallel, WorkflowScope, WorkflowSequence, WorkflowState, WorkflowTransition,
)
from .syntax import SyntaxFailure


class WorkflowSyntaxFailure(SyntaxFailure):
    def __init__(self, message: str, source: SourceSpan, code: str = "INVALID_WORKFLOW"):
        super().__init__(message, source)
        self.code = code


def quoted_end(text: str, start: int) -> int | None:
    """Return the end of an escaped/quoted atom without interpreting its operators."""
    char = text[start]
    if char == "\\":
        return min(start + 2, len(text))
    if char == "`":
        marker = re.match(r"`+", text[start:])[0]
        end = text.find(marker, start + len(marker))
        return len(text) + 1 if end < 0 else end + len(marker)
    if char in ('"', "'") and (start == 0 or not text[start - 1].isalnum()):
        index = start + 1
        while index < len(text):
            if text[index] == "\\":
                index += 2
            elif text[index] == char:
                return index + 1
            else:
                index += 1
        # An unmatched apostrophe in natural language is ordinary text.
        return None if char == "'" else len(text) + 1
    return None


def has_workflow_signal(text: str) -> bool:
    """Arrow-bearing paragraphs signal syntax; inline code mentions do not."""
    index = 0
    while index < len(text):
        end = quoted_end(text, index)
        if end is not None:
            index = end
        elif text.startswith("--", index):
            return True
        else:
            index += 1
    return False


def grouping_balance(text: str) -> int:
    """Extraction-only balance; the expression parser owns mismatch diagnostics."""
    depth, index, bars = 0, 0, False
    while index < len(text):
        end = quoted_end(text, index)
        if end is not None:
            index = end
            continue
        match text[index]:
            case "[" | "(" | "{":
                depth += 1
            case "]" | ")" | "}":
                depth -= 1
            case "|":
                bars = not bars
        index += 1
    return max(0, depth) + int(bars)


class ExpressionParser:
    def __init__(self, snapshot: DocumentSnapshot, start: int, end: int, max_depth: int):
        self.snapshot, self.base = snapshot, start
        self.text = snapshot.source_text[start:end]
        self.cursor = 0
        self.max_depth = max_depth

    def span(self, start: int, end: int | None = None) -> SourceSpan:
        return self.snapshot.span(self.base + start, self.base + (self.cursor if end is None else end))

    def fail(self, message: str, start: int | None = None, code: str = "INVALID_WORKFLOW") -> None:
        start = self.cursor if start is None else start
        raise WorkflowSyntaxFailure(message, self.span(start, min(len(self.text), start + 1)), code)

    def whitespace(self) -> None:
        while self.cursor < len(self.text) and self.text[self.cursor].isspace():
            self.cursor += 1

    def quoted_atom_end(self) -> int | None:
        end = quoted_end(self.text, self.cursor)
        if end is not None and end > len(self.text):
            self.fail("Unclosed quoted text or inline code in workflow")
        return end

    def parse(self) -> WorkflowExpression:
        self.whitespace()
        expression = self.expression(set(), 0)
        self.whitespace()
        if self.cursor != len(self.text):
            self.fail("Unexpected content after workflow expression")
        pending = [expression]
        while pending:
            node = pending.pop()
            match node:
                case WorkflowSequence():
                    return expression
                case WorkflowParallel() | WorkflowConditional():
                    pending.extend(node.branches)
                case WorkflowLoop() | WorkflowScope():
                    pending.append(node.body)
        self.fail("A workflow chain requires at least one named transition", 0)

    def expression(self, stops: set[str], depth: int) -> WorkflowExpression:
        self.whitespace()
        start = self.cursor
        if depth > self.max_depth:
            self.fail("Workflow nesting exceeds configured limit", code="WORKFLOW_NESTING_LIMIT_EXCEEDED")
        operands = [self.operand(stops, depth)]
        transitions = []
        while True:
            self.whitespace()
            if self.cursor == len(self.text) or self.text[self.cursor] in stops:
                break
            if not self.text.startswith("--", self.cursor):
                self.fail("Expected a named --transition--> between workflow operands")
            transitions.append(self.transition())
            operands.append(self.operand(stops, depth))
        if not transitions:
            return operands[0]
        return WorkflowSequence(operands=operands, transitions=transitions, source=self.span(start))

    def transition(self) -> WorkflowTransition:
        start = self.cursor
        self.cursor += 2
        label_start = self.cursor
        while self.cursor < len(self.text):
            if self.text.startswith("-->", self.cursor):
                label = self.text[label_start:self.cursor].strip()
                if not label:
                    self.fail("Transition label must not be empty", start)
                self.cursor += 3
                return WorkflowTransition(label=label, source=self.span(start))
            end = self.quoted_atom_end()
            self.cursor = end if end is not None else self.cursor + 1
        self.fail("Unclosed transition; expected -->", start)

    def operand(self, stops: set[str], depth: int) -> WorkflowExpression:
        self.whitespace()
        start = self.cursor
        if start == len(self.text) or self.text[start] in stops or self.text.startswith("--", start):
            self.fail("Expected a workflow state or grouped expression")
        match self.text[start]:
            case "[" | "(":
                return self.group(depth)
            case "{":
                self.cursor += 1
                body = self.expression({"}"}, depth + 1)
                self.close("}")
                return WorkflowScope(body=body, source=self.span(start))
            case "|":
                self.cursor += 1
                condition_start = self.cursor
                while self.cursor < len(self.text) and self.text[self.cursor] != ":":
                    if self.text[self.cursor] == "|":
                        self.fail("Loop requires condition: body", start)
                    end = self.quoted_atom_end()
                    self.cursor = end if end is not None else self.cursor + 1
                if self.cursor == len(self.text):
                    self.fail("Loop requires condition: body", start)
                condition = self.text[condition_start:self.cursor].strip()
                if not condition:
                    self.fail("Loop condition must not be empty", start)
                self.cursor += 1
                body = self.expression({"|"}, depth + 1)
                self.close("|")
                return WorkflowLoop(condition=condition, body=body, source=self.span(start))
            case "]" | ")" | "}":
                self.fail("Unexpected closing workflow delimiter")
            case _:
                return self.state(stops)

    def close(self, closer: str) -> None:
        self.whitespace()
        if self.cursor == len(self.text) or self.text[self.cursor] != closer:
            self.fail(f"Expected closing {closer}")
        self.cursor += 1

    def group(self, depth: int) -> WorkflowExpression:
        start = self.cursor
        opener = self.text[self.cursor]
        closer = "]" if opener == "[" else ")"
        self.cursor += 1
        branches = [self.expression({",", closer}, depth + 1)]
        while self.cursor < len(self.text) and self.text[self.cursor] == ",":
            self.cursor += 1
            branches.append(self.expression({",", closer}, depth + 1))
        self.close(closer)
        model = WorkflowConditional if opener == "[" else WorkflowParallel
        return model(branches=branches, source=self.span(start))

    def state(self, stops: set[str]) -> WorkflowState:
        start = self.cursor
        nested: list[str] = []
        colon = None
        pairs = {"(": ")", "[": "]", "{": "}"}
        # State: operand text -> one descriptive atom; internal function/type syntax is opaque.
        while self.cursor < len(self.text):
            char = self.text[self.cursor]
            end = self.quoted_atom_end()
            if end is not None:
                self.cursor = end
                continue
            if not nested and (char in stops or self.text.startswith("--", self.cursor)):
                break
            if char in pairs:
                nested.append(pairs[char])
            elif char in ")]}":
                if not nested or nested.pop() != char:
                    self.fail("Unmatched delimiter in workflow state")
            elif char == "|" and not nested:
                self.fail("Quote a literal | inside a workflow state")
            elif char == ":" and not nested and colon is None:
                colon = self.cursor
            self.cursor += 1
        if nested:
            self.fail("Unclosed function/type delimiter in workflow state", start)
        end = self.cursor
        while end > start and self.text[end - 1].isspace():
            end -= 1
        raw = self.text[start:end]
        name = self.text[start:colon].strip() if colon is not None else raw
        annotation = self.text[colon + 1:end].strip() if colon is not None else None
        if not name or annotation == "":
            self.fail("Workflow state and any declared type must be nonempty", start)
        return WorkflowState(text=raw, name=name, type_annotation=annotation, source=self.span(start, end))


def parse_expression(snapshot: DocumentSnapshot, source: SourceSpan, max_depth: int = 128) -> WorkflowExpression:
    return ExpressionParser(snapshot, source.start_offset, source.end_offset, max_depth).parse()
