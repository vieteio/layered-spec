"""UC7: discover chains in mixed Markdown, then share one expression parser."""

from __future__ import annotations

import re

from pydantic import Field, ValidationError

from .diagnostics import diagnostic
from .markdown_blocks import MarkdownContext
from .models import (
    Diagnostic, DocumentSnapshot, InvalidWorkflowChain, MarkdownBody, RecoveredBlock,
    RelatedLocation, SourceSpan, StrictModel, ValidWorkflowChain, WorkflowChain,
    WorkflowChainResult, WorkflowContent, WorkflowProse,
)
from .workflow_expressions import WorkflowSyntaxFailure, grouping_balance, has_workflow_signal, parse_expression

BULLET = re.compile(r"^(\s*)(?:[-+*]|\d+[.)])\s+")
HEADING = re.compile(r"^\s*#{4,6}\s+(.+?)(?:\s+#+)?\s*$")
NAMED = re.compile(r"^(\s*)(?:(?:[-+*]|\d+[.)])\s+)?(?P<label>`[^`]+`|\*\*[^*]+\*\*|[\w][\w .-]*):[ \t]*(?P<inline>.*)$")


class ChainCandidate(StrictModel):
    body: SourceSpan
    source: SourceSpan
    first_line: int
    end_line: int
    label: str | None = None
    label_source: SourceSpan | None = None


class WorkflowExtraction(StrictModel):
    content: list[WorkflowContent] = Field(default_factory=list)
    diagnostics: list[Diagnostic] = Field(default_factory=list)


class WorkflowExtractor:
    def __init__(self, snapshot: DocumentSnapshot, context: MarkdownContext, max_depth: int):
        self.snapshot, self.context, self.max_depth = snapshot, context, max_depth
        self.lines = snapshot.lines()
        self.fences = {block.start_line: block for block in context.literals if block.kind == "fence"}
        self.quoted_or_html = set()
        for block in context.literals:
            if block.kind in ("blockquote_open", "html_block"):
                self.quoted_or_html.update(range(block.start_line, block.end_line))

    def offset(self, line: int) -> int:
        return self.snapshot.line_span(line, line).start_offset

    def text(self, source: SourceSpan) -> str:
        return self.snapshot.source_text[source.start_offset:source.end_offset]

    def trimmed_span(self, start: int, end: int, *, unwrap_code: bool = False) -> SourceSpan:
        text = self.snapshot.source_text
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if unwrap_code and start < end and text[start] == "`":
            marker = re.match(r"`+", text[start:end])[0]
            closing = text.find(marker, start + len(marker), end)
            if closing == end - len(marker):
                start += len(marker)
                end -= len(marker)
        return self.snapshot.span(start, end)

    def named(self, line: int):
        raw = self.lines[line].rstrip("\r\n")
        heading = HEADING.fullmatch(raw)
        if heading:
            return heading[1], self.snapshot.span(self.offset(line) + heading.start(1), self.offset(line) + heading.end(1)), ""
        named = NAMED.fullmatch(raw)
        # State: local label candidate -> accepted wrapper/indentation, never an outer label.
        if named:
            marked = named["label"].startswith(("`", "**"))
            local = marked or BULLET.match(raw) is not None or named[1] == "  "
            if not local or (named["inline"] and not marked):
                return None
            label = named["label"].strip("`*")
            return label, self.snapshot.span(self.offset(line) + named.start("label"), self.offset(line) + named.end("label")), named["inline"]
        return None

    def paragraph_end(self, start: int, end: int, body_offset: int, excluded: set[int]) -> int:
        baseline = len(self.lines[start]) - len(self.lines[start].lstrip())
        cursor = start + 1
        # State: paragraph prefix -> balanced multi-paragraph chain, bounded before parsing.
        while cursor < end:
            raw = self.lines[cursor]
            if cursor in excluded or cursor in self.fences or cursor in self.quoted_or_html or cursor in self.context.opaque:
                break
            # A named sibling is independently recoverable even after an unclosed group.
            if self.named(cursor) is not None:
                break
            if re.match(r"^\s*#{1,6}(?:\s|$)", raw):
                break
            if BULLET.match(raw) and len(raw) - len(raw.lstrip()) <= baseline:
                break
            if not raw.strip():
                lookahead = cursor + 1
                while lookahead < end and not self.lines[lookahead].strip():
                    lookahead += 1
                current = self.snapshot.source_text[body_offset:self.offset(cursor)]
                balance = grouping_balance(current)
                if lookahead == end:
                    break
                following = self.lines[lookahead].lstrip()
                continuation = following.startswith(("--", "]", ")", "}", "|")) or current.rstrip().endswith("-->")
                if balance == 0 and not continuation:
                    break
                next_indent = len(self.lines[lookahead]) - len(following)
                if balance > 0 and next_indent <= baseline and has_workflow_signal(following) and not continuation:
                    break
            cursor += 1
        return cursor

    def candidate(self, line: int, end: int, excluded: set[int], *, main: bool = False) -> ChainCandidate | None:
        if line in self.context.opaque or line in self.quoted_or_html or line in excluded:
            return None
        original = line
        label = label_source = None
        inline_start = None
        name = None if main else self.named(line)
        if name:
            label, label_source, inline = name
            if inline:
                inline_start = self.offset(line) + self.lines[line].index(inline, label_source.end_offset - self.offset(line))
            else:
                line += 1
                while line < end and not self.lines[line].strip():
                    line += 1
                if line == end or self.named(line) is not None:
                    return None
        if line in self.quoted_or_html or line in excluded or line in self.context.opaque:
            return None
        fence = self.fences.get(line)
        if fence:
            if fence.info not in ("text", "workflow") or fence.end_line > end or any(i in self.context.opaque for i in range(line, fence.end_line)):
                return None
            body = self.trimmed_span(self.offset(line + 1), self.offset(fence.end_line - 1))
            if not main and fence.info != "workflow" and not has_workflow_signal(self.text(body)):
                return None
            return ChainCandidate(body=body, source=self.snapshot.line_span(original, fence.end_line), first_line=original, end_line=fence.end_line, label=label, label_source=label_source)
        if line in self.context.protected:
            return None
        raw = self.lines[line]
        bullet = BULLET.match(raw) if not main else None
        offset = inline_start if inline_start is not None else self.offset(line) + (bullet.end() if bullet else 0)
        stop = self.paragraph_end(line, end, offset, excluded)
        body = self.trimmed_span(offset, self.offset(stop), unwrap_code=True)
        if not main and not has_workflow_signal(self.text(body)):
            return None
        return ChainCandidate(body=body, source=self.snapshot.line_span(original, stop), first_line=original, end_line=stop, label=label, label_source=label_source)

    def parse_candidate(self, candidate: ChainCandidate) -> tuple[WorkflowChainResult, list[Diagnostic]]:
        try:
            expression = parse_expression(self.snapshot, candidate.body, self.max_depth)
            chain = WorkflowChain(label=candidate.label, label_source=candidate.label_source, body=MarkdownBody(markdown=self.text(candidate.body), source=candidate.body), expression=expression, source=candidate.source)
            return ValidWorkflowChain(value=chain), []
        except WorkflowSyntaxFailure as error:
            issues = [diagnostic(error.code, str(error), error.source)]
        except ValidationError as error:
            issues = [diagnostic("INVALID_WORKFLOW", detail["msg"], candidate.body, precision="block", phase="model") for detail in error.errors()]
        raw = RecoveredBlock(block_kind="workflow", source=candidate.source, raw_markdown=self.text(candidate.source), diagnostic_ids=[item.diagnostic_id for item in issues])
        return InvalidWorkflowChain(label=candidate.label, raw_block=raw, diagnostic_ids=raw.diagnostic_ids), issues

    def main(self, start: int, end: int) -> tuple[WorkflowChainResult | None, list[Diagnostic]]:
        first = next((i for i in range(start, end) if self.lines[i].strip()), None)
        if first is None or re.match(r"^\s*#", self.lines[first]):
            return None, []
        candidate = self.candidate(first, end, set(), main=True)
        return self.parse_candidate(candidate) if candidate is not None else (None, [])

    def detailed(self, start: int, end: int, excluded: set[int], *, labels: dict[str, SourceSpan] | None = None) -> WorkflowExtraction:
        result = WorkflowExtraction()
        cursor = start
        prose_start = self.offset(start)
        if labels is None:
            labels = {}
        # State: mixed Markdown -> ordered prose/valid/invalid chain fragments; never discard a sibling.
        while cursor < end:
            candidate = self.candidate(cursor, end, excluded) if self.lines[cursor].strip() else None
            if candidate is None:
                fence = self.fences.get(cursor)
                if fence:
                    cursor = fence.end_line
                elif self.lines[cursor].strip() and cursor not in self.context.protected and cursor not in self.context.opaque and cursor not in excluded:
                    # Preserve a non-workflow paragraph as one block; its later physical
                    # lines can contain inline examples without declaring a new chain.
                    cursor = self.paragraph_end(cursor, end, self.offset(cursor), excluded)
                else:
                    cursor += 1
                continue
            if prose_start < candidate.source.start_offset:
                source = self.snapshot.span(prose_start, candidate.source.start_offset)
                result.content.append(WorkflowProse(body=MarkdownBody(markdown=self.text(source), source=source)))
            parsed, issues = self.parse_candidate(candidate)
            result.content.append(parsed)
            result.diagnostics.extend(issues)
            if candidate.label is not None:
                if candidate.label in labels:
                    result.diagnostics.append(diagnostic("DUPLICATE_WORKFLOW_LABEL", f"Repeated local workflow label: {candidate.label}", candidate.label_source, related=[RelatedLocation(message="First workflow label", location=labels[candidate.label])]))
                else:
                    labels[candidate.label] = candidate.label_source
            cursor, prose_start = candidate.end_line, candidate.source.end_offset
        if prose_start < self.offset(end):
            source = self.snapshot.span(prose_start, self.offset(end))
            result.content.append(WorkflowProse(body=MarkdownBody(markdown=self.text(source), source=source)))
        return result
