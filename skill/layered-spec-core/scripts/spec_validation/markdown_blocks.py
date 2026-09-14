"""UC2: Markdown token spans and literal protection without rendering source."""

from __future__ import annotations

import re

from markdown_it import MarkdownIt
from markdown_it.rules_block.state_block import StateBlock

from .diagnostics import diagnostic
from pydantic import Field

from .models import Diagnostic, DocumentSnapshot, StrictModel


class MarkdownLiteral(StrictModel):
    kind: str
    start_line: int
    end_line: int
    info: str = ""


class MarkdownContext(StrictModel):
    protected: set[int]
    in_list: set[int]
    opaque: set[int]
    diagnostics: list[Diagnostic]
    token_count: int
    list_levels: dict[int, int]
    literals: list[MarkdownLiteral] = Field(default_factory=list)

    def boundary_allowed(self, line: int) -> bool:
        """Filter Markdown ownership; callers still check source columns and grammar."""
        return line not in self.protected and line not in self.in_list and line not in self.opaque

    def content_allowed(self, line: int) -> bool:
        return line not in self.protected and line not in self.opaque


def markdown_context(snapshot: DocumentSnapshot, max_depth: int) -> MarkdownContext:
    """UC2: protect literals and quarantine unclosed/over-depth regions."""
    lines = snapshot.lines()
    # State: immutable source -> token spans with original line coordinates.
    tokenizer = MarkdownIt("commonmark", {"maxNesting": max_depth + 4})

    def depth_guard(state: StateBlock, start: int, end: int, silent: bool) -> bool:
        # markdown-it's built-in limit consumes the entire remaining document. Quarantine
        # only the current over-depth container so an outer heading can still be parsed.
        if state.level < max_depth:
            return False
        if silent:
            return True
        stop = start + 1
        while stop < end:
            if not state.isEmpty(stop) and state.sCount[stop] < state.blkIndent:
                break
            stop += 1
        token = state.push("planning_depth_limit", "", 0)
        token.map = [start, stop]
        state.line = stop
        return True

    tokenizer.block.ruler.before("code", "planning_depth_guard", depth_guard)
    tokens = tokenizer.parse(snapshot.source_text)
    context = MarkdownContext(protected=set(), in_list=set(), opaque=set(), diagnostics=[], token_count=len(tokens), list_levels={})
    for token in tokens:
        if token.map is None:
            continue
        start, end = token.map
        match token.type:
            case "fence" | "code_block" | "html_block" | "blockquote_open":
                context.protected.update(range(start, end))
                context.literals.append(MarkdownLiteral(kind=token.type, start_line=start, end_line=end, info=token.info.strip()))
            case "list_item_open":
                context.in_list.update(range(start, end))
                for index in range(start, end):
                    context.list_levels[index] = max(context.list_levels.get(index, 0), token.level)
        if token.type == "planning_depth_limit":
            if start not in context.opaque:
                context.diagnostics.append(diagnostic(
                    "NESTING_LIMIT_EXCEEDED", f"Markdown nesting exceeds configured limit {max_depth}",
                    snapshot.line_span(start, end), precision="block",
                ))
            context.opaque.update(range(start, end))
        if token.type == "fence":
            final = re.sub(r"^(?:\s*>\s*)+", "", lines[end - 1]).strip()
            closer = re.fullmatch(re.escape(token.markup[0]) + "{" + str(len(token.markup)) + r",}\s*", final)
            if end <= start + 1 or closer is None:
                context.diagnostics.append(diagnostic(
                    "UNCLOSED_LITERAL_BLOCK", "Unclosed code fence; following apparent declarations are not trustworthy",
                    snapshot.line_span(start, end), precision="block",
                ))
                context.opaque.update(range(start, end))
        if token.type == "html_block" and "<!--" in token.content and "-->" not in token.content:
            context.diagnostics.append(diagnostic(
                "UNCLOSED_LITERAL_BLOCK", "Unclosed HTML comment", snapshot.line_span(start, end), precision="block",
            ))
            context.opaque.update(range(start, end))
    return context
