"""UC8: source-backed Markdown rendering with explicit ownership and no raw-layer fallback."""

from __future__ import annotations

import re
from typing import Literal

from spec_validation.models import (
    EntityRef, ForwardRealization, InvariantCheckpoint, InvariantDerivation,
    MemberSelector, ParsedDocument, RationaleNote, ReferenceField, Requirement, ReverseRealization,
    SourceSpan, StrictModel, UnownedRequirementRef, UseMapping, ValidEntry,
    ValidWorkflowChain, WorkflowAnchor, WorkflowChain, WorkflowConditional,
    WorkflowExpression, WorkflowLoop, WorkflowParallel, WorkflowScope,
    WorkflowSequence, WorkflowState, DetailedWorkflowLayer, MarkdownSubsection,
)
from spec_validation.syntax import quote_selector


class RenderingError(ValueError):
    """The source ownership or parsed structure cannot support the requested rendering."""


class RenderFragment(StrictModel):
    source: SourceSpan
    kind: Literal["generated", "verbatim"]
    markdown: str


def reconstruct_markdown(document: ParsedDocument) -> str:
    """UC8: reconstruct the exact text from the recovered top-level partition."""
    cursor = 0
    fragments = []
    # Opaque annotations overlap regions; only ownership blocks form the root partition.
    for block in sorted((b for b in document.blocks if b.block_kind in ("region", "prose")), key=lambda b: b.source.start_offset):
        if block.source.document_id != document.snapshot.document_id or block.source.start_offset != cursor:
            raise RenderingError("Recovered blocks do not form a contiguous document partition")
        if len(block.raw_markdown) != block.source.end_offset - cursor:
            raise RenderingError("Recovered block text does not match its source extent")
        fragments.append(block.raw_markdown)
        cursor = block.source.end_offset
    if cursor != len(document.snapshot.source_text):
        raise RenderingError("Recovered blocks do not cover the complete source")
    return "".join(fragments)


def reconstruct_bytes(document: ParsedDocument) -> bytes:
    prefix = b"\xef\xbb\xbf" if document.snapshot.utf8_bom else b""
    return prefix + reconstruct_markdown(document).encode("utf-8")


def quoted(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_member(value: MemberSelector) -> str:
    if value.kind == "requirement" and not re.fullmatch(r"R[1-9]\d*(?:\.[1-9]\d*)*", value.value):
        return "requirement " + quote_selector(value.value)
    return value.value


def render_reference(value: EntityRef | UnownedRequirementRef | MemberSelector) -> str:
    match value:
        case MemberSelector():
            return render_member(value)
        case UnownedRequirementRef():
            return render_member(value.requirement_selector)
        case EntityRef():
            if value.owner_local:
                if value.member_selector is None:
                    raise RenderingError("An owner-local reference requires a member")
                return render_member(value.member_selector)
            selector = value.owner_selector
            match selector.kind:
                case "use_case_number":
                    owner = "UC" + selector.value
                case "story_id":
                    owner = selector.value
                case "use_case_title":
                    owner = "use-case " + quoted(selector.value)
            prefix = value.document_path + "#" if value.document_path else ""
            suffix = "/" + render_member(value.member_selector) if value.member_selector else ""
            return prefix + owner + suffix
    raise RenderingError(f"Unsupported reference model: {type(value).__name__}")


def render_expression(value: WorkflowExpression) -> str:
    match value:
        case WorkflowState():
            return value.text
        case WorkflowSequence():
            result = render_expression(value.operands[0])
            for transition, operand in zip(value.transitions, value.operands[1:], strict=True):
                result += f" --{transition.label}--> " + render_expression(operand)
            return result
        case WorkflowParallel() | WorkflowConditional():
            opening, closing = ("(", ")") if isinstance(value, WorkflowParallel) else ("[", "]")
            return opening + ", ".join(render_expression(branch) for branch in value.branches) + closing
        case WorkflowLoop():
            return "| " + value.condition + ": " + render_expression(value.body) + " |"
        case WorkflowScope():
            return "{" + render_expression(value.body) + "}"
    raise RenderingError(f"Unsupported workflow model: {type(value).__name__}")


def render_chain(chain: WorkflowChain) -> str:
    expression = render_expression(chain.expression)
    fence = "`" * max(3, 1 + max((len(m[0]) for m in re.finditer(r"`+", expression)), default=0))
    heading = f"#### {chain.label} ###\n\n" if chain.label is not None else ""
    return heading + fence + "workflow\n" + expression + "\n" + fence + "\n"


def render_fragments(document: ParsedDocument) -> list[RenderFragment]:
    """UC8: regenerate typed syntax and preserve each uncovered source interval once."""
    if not document.parse_complete or any(d.severity == "error" for d in document.diagnostics) or any(not e.complete for e in document.entities):
        raise RenderingError("Canonical rendering requires complete, structurally valid parsed content")
    snapshot = document.snapshot
    replacements: list[RenderFragment] = []

    def add(source: SourceSpan, markdown: str):
        if source.document_id != snapshot.document_id or not 0 <= source.start_offset < source.end_offset <= len(snapshot.source_text):
            raise RenderingError("Rendered field has invalid source ownership")
        replacements.append(RenderFragment(source=source, kind="generated", markdown=markdown))

    def refs(values):
        return ", ".join(render_reference(value) for value in values)

    # Typed declarations contribute replacements; body prose never substitutes for typed fields.
    for entity in document.entities:
        match entity.entity_kind:
            case "use_case":
                title = f"UC{entity.number} — {entity.title}" if entity.number else quoted(entity.title)
            case "story":
                title = f"{entity.entity_id} — {entity.title}"
            case "story_state":
                title = f"State {entity.entity_id} — {entity.title}"
        add(entity.source, "### " + title + " ###\n")
        if entity.workflow:
            add(entity.workflow.source, render_chain(entity.workflow))
        for layer in entity.layers:
            if not layer.complete:
                raise RenderingError("Cannot render an incomplete layer canonically")
            add(layer.source, layer.name + ":\n")
            for section in layer.subsections:
                if isinstance(section, MarkdownSubsection):
                    add(snapshot.span(section.source.start_offset, section.body.source.end_offset), "- " + section.name + ":\n" + section.body.markdown)
                else:
                    if not section.complete:
                        raise RenderingError("Cannot render an incomplete subsection")
                    add(section.source, "- " + section.name + ":\n")

            def group_indent(source: SourceSpan) -> str:
                return "  " if any(section.body.source.start_offset <= source.start_offset < section.body.source.end_offset for section in layer.subsections) else ""

            for result in layer.all_entries:
                if not isinstance(result, ValidEntry):
                    raise RenderingError("Cannot render an invalid entry canonically")
                entry = result.value
                indentation = group_indent(entry.source)
                match entry:
                    case Requirement():
                        if entry.form:
                            prefix = indentation + f"  {entry.requirement_id} {entry.form}: "
                        else:
                            prefix = indentation + "Requirement: " + quoted(entry.requirement_id) + "\n"
                        add(snapshot.span(entry.source.start_offset, entry.definition.source.end_offset), prefix + entry.definition.markdown)
                    case ForwardRealization():
                        add(entry.source, indentation + "- " + refs(entry.source_requirements) + " -> " + refs(entry.targets) + "\n")
                    case ReverseRealization():
                        add(entry.source, indentation + "- " + refs(entry.sources) + "\n")
                    case UseMapping():
                        match entry.selector_kind:
                            case "label":
                                source = quoted(entry.source_selector)
                            case "story_state":
                                source = "State/" + entry.source_selector
                            case "anchor":
                                source = render_reference(entry.source_selector)
                        add(entry.source, indentation + "- " + source + " -> " + refs(entry.targets) + "\n")
                    case WorkflowAnchor():
                        add(entry.source, indentation + f"- {entry.anchor_id}: {entry.label}\n")
                    case ReferenceField():
                        raw = snapshot.source_text[entry.source.start_offset:entry.source.end_offset]
                        prefix = re.match(r"^(\s*(?:-\s+)?)(?:requirements|source):", raw)
                        if prefix is None:
                            raise RenderingError("Reference field has no source-level field boundary")
                        add(entry.source, prefix[1] + entry.field_name + ": " + refs(entry.references) + "\n")
                    case InvariantCheckpoint():
                        add(entry.source, f"  - `{entry.invariant_id}` at `{entry.state_label}`: " + entry.assertion.markdown)
                    case RationaleNote():
                        add(entry.source, render_rationale(entry))
                    case InvariantDerivation():
                        header = snapshot.line_span(entry.source.start_line - 1, entry.source.start_line)
                        add(header, f"  - `{entry.derivation_id}: {refs(entry.source_invariants)} -> {refs(entry.target_invariants)}`\n")
                        raw = snapshot.source_text[entry.source.start_offset:entry.source.end_offset]
                        transition = re.search(r"(?m)^    - workflow transition:[^\r\n]*", raw)
                        if transition is None:
                            raise RenderingError("Derivation has no located workflow transition")
                        add(snapshot.span(entry.source.start_offset + transition.start(), entry.source.start_offset + transition.end()), "    - workflow transition: `" + entry.transition_label + "`")
                        add(entry.justification.source, entry.justification.markdown)
                    case _:
                        raise RenderingError(f"Unsupported typed entry: {type(entry).__name__}")
            if isinstance(layer, DetailedWorkflowLayer):
                for chain in layer.chains:
                    if not isinstance(chain, ValidWorkflowChain):
                        raise RenderingError("Cannot render a malformed workflow canonically")
                    indentation = group_indent(chain.value.source)
                    add(chain.value.source, "".join(indentation + line if line.strip() else line for line in render_chain(chain.value).splitlines(keepends=True)))

    # Located replacements -> a complete, ordered partition with explicit verbatim gaps.
    fragments: list[RenderFragment] = []
    cursor = 0
    for replacement in sorted(replacements, key=lambda item: item.source.start_offset):
        start = replacement.source.start_offset
        if start < cursor:
            raise RenderingError("Typed render spans overlap")
        if cursor < start:
            fragments.append(RenderFragment(source=snapshot.span(cursor, start), kind="verbatim", markdown=snapshot.source_text[cursor:start]))
        fragments.append(replacement)
        cursor = replacement.source.end_offset
    if cursor < len(snapshot.source_text):
        fragments.append(RenderFragment(source=snapshot.span(cursor, len(snapshot.source_text)), kind="verbatim", markdown=snapshot.source_text[cursor:]))
    return fragments


def render_rationale(note: RationaleNote) -> str:
    """UC8/R8.4: regenerate note fields while preserving each Markdown body exactly."""
    opening = f"  - `{note.rationale_id}`:\n    - note:" if note.rationale_id else "  - note:"
    result = opening + note.note.markdown + "\n"
    result += f"    - assessment: {note.assessment}\n"
    for name in ("qualification", "reason", "replacement"):
        body = getattr(note, name)
        if body is not None:
            result += f"    - {name}:" + body.markdown + "\n"
    if note.used_by:
        result += "    - used by: " + ", ".join(render_reference(ref) for ref in note.used_by) + "\n"
    return result + "\n"


def render_markdown(document: ParsedDocument) -> str:
    return "".join(fragment.markdown for fragment in render_fragments(document))
