"""UC2/UC3: recovering planning boundaries and independent typed entries."""

from __future__ import annotations

import re
from difflib import get_close_matches
from time import perf_counter

from pydantic import ValidationError

from .diagnostics import diagnostic
from .grammar import CONVENTIONAL_REQUIREMENT, INVARIANT_SECTIONS, LAYER_NAMES, canonical_layer_name, layer_candidate
from .markdown_blocks import markdown_context
from .models import (
    AnchorsLayer, DetailedWorkflowLayer, DocumentSnapshot, EntityAssembly, EntityKey, EntityRef, ExtensionLayer,
    ForwardLayer, ForwardRealization, InvalidEntry, InvariantCheckpoint, InvariantDerivation,
    InvariantsLayer, LayerBase, UnownedRequirementRef, MarkdownBody, MarkdownLayer,
    MarkdownSubsection, RationaleSubsection, StateInvariantsSubsection, DerivationsSubsection,
    StructuredSubsection, TypedSubsection, WorkflowSubsection,
    MemberSelector, OwnerSelector, ParsedDocument, RecoveredBlock, ReferenceField,
    RationaleNote, Requirement, RequirementsLayer, ReverseLayer, ReverseRealization, SourceSpan, StoryState,
    UnknownLayer, UseCase, UseMapping, UserStory, UsesLayer, ValidEntry, ValidationOptions,
    WorkflowAnchor, ValidWorkflowChain,
)
from .syntax import NUMBER, SyntaxFailure, TextSlice, member, reference, selector, split_parts, trim, unwrap
from .workflow_blocks import WorkflowExtractor

HEADING = re.compile(r"^(#{1,6})(?:[ \t]+(.*?)|)[ \t]*$")
REGIONS = {"use cases": "use_case", "user stories": "story", "states": "story_state"}
STRUCTURAL_LAYERS = {
    "Requirements": RequirementsLayer, "Realized by": ForwardLayer, "Realizes": ReverseLayer,
    "Uses": UsesLayer, "Invariants": InvariantsLayer, "Workflow anchors": AnchorsLayer,
    "Detailed Workflow": DetailedWorkflowLayer,
}


def _heading(line: str) -> tuple[int, str] | None:
    matched = HEADING.fullmatch(line.rstrip("\r\n"))
    if not matched:
        return None
    title = re.sub(r"[ \t]+#+[ \t]*$", "", matched[2] or "").strip()
    return len(matched[1]), title


class PlanningParser:
    def __init__(self, snapshot: DocumentSnapshot, options: ValidationOptions):
        self.snapshot = snapshot
        self.options = options
        self.lines = snapshot.lines()
        self.context = markdown_context(snapshot, options.max_nesting_depth)
        self.result = ParsedDocument(snapshot=snapshot, diagnostics=list(self.context.diagnostics))
        self.result.parse_complete = not self.context.opaque

    def block(self, kind: str, start: int, end: int, *, uncertain: bool = False) -> RecoveredBlock:
        source = self.snapshot.line_span(start, end)
        return RecoveredBlock(
            block_kind=kind, source=source,
            raw_markdown=self.snapshot.source_text[source.start_offset:source.end_offset],
            trust="uncertain" if uncertain else "exact",
        )

    def body(self, start: int, end: int) -> MarkdownBody:
        source = self.snapshot.line_span(start, end)
        return MarkdownBody(markdown=self.snapshot.source_text[source.start_offset:source.end_offset], source=source)

    def error(self, code: str, message: str, source: SourceSpan, *, phase: str = "parse", suggestion: str | None = None) -> str:
        item = diagnostic(code, message, source, phase=phase, suggestion=suggestion)
        self.result.diagnostics.append(item)
        return item.diagnostic_id

    def parse(self) -> ParsedDocument:
        """UC2: discover structured containers, preserving all surrounding Markdown."""
        started = perf_counter()
        # State: outside-region Markdown -> explicit container ranges, leaving prose untouched.
        headings = [
            (index, parsed) for index, line in enumerate(self.lines)
            if self.context.boundary_allowed(index) and (parsed := _heading(line)) and parsed[0] <= 2
        ]
        seen_regions: set[str] = set()
        cursor = 0
        for position, (start, (_, title)) in enumerate(headings):
            if title.casefold() not in REGIONS or _heading(self.lines[start])[0] != 2:
                continue
            if cursor < start:
                self.result.blocks.append(self.block("prose", cursor, start))
            end = headings[position + 1][0] if position + 1 < len(headings) else len(self.lines)
            kind = REGIONS[title.casefold()]
            region = self.block("region", start, end)
            if kind in seen_regions:
                region.diagnostic_ids.append(self.error("DUPLICATE_REGION", f"Repeated structured container: {title}", region.source))
            seen_regions.add(kind)
            entity_starts = [i for i in range(start + 1, end) if self.context.boundary_allowed(i) and (h := _heading(self.lines[i])) and h[0] == 3]
            if not entity_starts:
                region.diagnostic_ids.append(self.error("EMPTY_STRUCTURED_REGION", f"No entity declarations in {title}", region.source))
            for ordinal, entity_start in enumerate(entity_starts):
                entity_end = entity_starts[ordinal + 1] if ordinal + 1 < len(entity_starts) else end
                entity_block = self.block("entity", entity_start, entity_end)
                region.children.append(entity_block)
                self.parse_entity(kind, entity_start, entity_end, entity_block)
            self.result.blocks.append(region)
            cursor = end
        if cursor < len(self.lines):
            self.result.blocks.append(self.block("prose", cursor, len(self.lines)))
        if not seen_regions:
            self.error("MISSING_STRUCTURED_REGION", "No recognized Use cases, User stories, or States container", self.snapshot.span(0))
            self.result.parse_complete = False
        # State: tokenizer quarantines -> explicit opaque blocks consumable by report coverage accounting.
        opaque = sorted(self.context.opaque)
        if opaque:
            start = previous = opaque[0]
            for index in opaque[1:] + [opaque[-1] + 2]:
                if index != previous + 1:
                    self.result.blocks.append(self.block("opaque", start, previous + 1, uncertain=True))
                    start = index
                previous = index
        self.result.duration_ms = (perf_counter() - started) * 1000
        return self.result

    def parse_entity(self, kind: str, start: int, end: int, block: RecoveredBlock) -> None:
        header = _heading(self.lines[start])[1]
        source = self.snapshot.line_span(start, start + 1)
        number = entity_id = None
        spelling = "unnumbered"
        title = header
        try:
            match kind:
                case "use_case":
                    compact = re.fullmatch(rf"UC({NUMBER})\s+—\s+(.+)", header)
                    numbered = re.fullmatch(rf"({NUMBER})\.?\s+(.+)", header)
                    if header.startswith('"'):
                        title, _ = selector(header, source.start_offset + self.lines[start].find(header), self.snapshot)
                        spelling = "quoted_title"
                    elif compact or numbered:
                        matched = compact or numbered
                        number, title = matched[1], matched[2].strip()
                        spelling = "uc_prefixed" if compact else "numbered"
                case "story":
                    matched = re.fullmatch(rf"(S{NUMBER})\s+—\s+(.+)", header)
                    if matched is None:
                        old = re.fullmatch(rf"({NUMBER})\.?\s+(.+)", header)
                        if old:
                            entity_id, title = "S" + old[1], old[2]
                    elif matched:
                        entity_id, title = matched[1], matched[2]
                    if entity_id is None:
                        raise SyntaxFailure("Story heading must be S<number> — Title", source)
                case "story_state":
                    matched = re.fullmatch(r"State ([a-z][a-z0-9_-]*)\s+—\s+(.+)", header)
                    if not matched:
                        raise SyntaxFailure("State heading must be State <key> — Title", source)
                    entity_id, title = matched[1], matched[2]
            if not title.strip():
                raise SyntaxFailure("Entity title must not be empty", source)
        except SyntaxFailure as error:
            block.block_kind, block.trust = "opaque", "uncertain"
            block.diagnostic_ids.append(self.error("INVALID_ENTITY_HEADER", str(error), error.source))
            self.result.parse_complete = False
            return
        assembly = EntityAssembly(
            key=EntityKey(document_id=self.snapshot.document_id, declaration_start_offset=source.start_offset),
            entity_kind=kind, title=title, number=number, entity_id=entity_id,
            header_spelling=spelling, source=source,
        )
        self.result.entities.append(assembly)

        # State: exact source/context -> outer boundaries, before any body interpretation.
        layers: list[tuple[int, str, bool]] = []
        for line_number in range(start + 1, end):
            if not self.context.boundary_allowed(line_number):
                continue
            raw = self.lines[line_number].rstrip("\r\n")
            if raw.startswith("Layer:"):
                layers.append((line_number, raw[len("Layer:"):].strip(), True))
                continue
            name = layer_candidate(raw)
            if name is not None:
                layers.append((line_number, name, False))
        first_layer = layers[0][0] if layers else end
        if kind != "story_state":
            workflow_result, issues = WorkflowExtractor(self.snapshot, self.context, self.options.max_nesting_depth).main(start + 1, first_layer)
            assembly.workflow_result = workflow_result
            self.result.diagnostics.extend(issues)
            assembly.diagnostic_ids.extend(item.diagnostic_id for item in issues)
            if isinstance(workflow_result, ValidWorkflowChain):
                assembly.workflow = workflow_result.value
            elif workflow_result is None:
                assembly.diagnostic_ids.append(self.error("MISSING_WORKFLOW", "Expected a first nonempty workflow paragraph or fenced text workflow", source))
            if assembly.workflow is None:
                assembly.complete = False
        first_body_line = next((i for i in range(start + 1, end) if self.lines[i].strip()), None)
        for ordinal, (line_number, name, obsolete) in enumerate(layers):
            layer_end = layers[ordinal + 1][0] if ordinal + 1 < len(layers) else end
            layer_block = self.block("layer", line_number, layer_end)
            block.children.append(layer_block)
            missing_separator = line_number != first_body_line and bool(self.lines[line_number - 1].strip())
            layer = self.parse_layer(assembly, name, line_number, layer_end, obsolete, missing_separator)
            assembly.layers.append(layer)
            layer_block.diagnostic_ids.extend(layer.diagnostic_ids)
            if not layer.complete:
                assembly.complete = False
        if any(i in self.context.opaque for i in range(start, end)):
            assembly.complete = False
            assembly.unknown_structure = True
        names: set[str] = set()
        for layer in assembly.layers:
            if layer.name in names:
                assembly.diagnostic_ids.append(self.error("DUPLICATE_LAYER", f"Repeated layer {layer.name}", layer.source, phase="model"))
                assembly.complete = False
            names.add(layer.name)
        required = {"story": ("Uses", "E2E tests"), "story_state": ("Description",)}.get(kind, ())
        for name in required:
            if not any(layer.name == name and layer.body.markdown.strip() for layer in assembly.layers):
                assembly.diagnostic_ids.append(self.error("MISSING_REQUIRED_LAYER", f"{kind} requires a nonempty {name} layer", source, phase="model"))
                assembly.complete = False
        if assembly.complete:
            shared = dict(declaration_key=assembly.key, title=title, layers=assembly.layers, source=source)
            match kind:
                case "use_case":
                    assembly.value = UseCase(**shared, number=number, header_spelling=spelling, workflow=assembly.workflow)
                case "story":
                    assembly.value = UserStory(**shared, entity_id=entity_id, workflow=assembly.workflow)
                case "story_state":
                    assembly.value = StoryState(**shared, state_key=entity_id)
        block.diagnostic_ids.extend(assembly.diagnostic_ids)

    def invalid(self, layer: LayerBase | StructuredSubsection, start: int, end: int, errors: list[tuple[str, SourceSpan]], code: str = "MALFORMED_MAPPING") -> None:
        ids = [self.error(code, message, span) for message, span in errors]
        raw = self.block("entry", start, end)
        raw.diagnostic_ids = ids
        layer.entries.append(InvalidEntry(raw_block=raw, diagnostic_ids=ids))
        layer.complete = False
        layer.diagnostic_ids.extend(ids)

    def parse_layer(self, owner: EntityAssembly, name: str, start: int, end: int, obsolete: bool, missing_separator: bool) -> LayerBase:
        known = canonical_layer_name(name)
        source = self.snapshot.line_span(start, start + 1)
        arguments = dict(name=known or name, source=source, body=self.body(start + 1, end))
        # State: a candidate boundary -> typed or quarantined layer with all boundary errors.
        invalid_name = obsolete or known is None
        layer_type = UnknownLayer if invalid_name else STRUCTURAL_LAYERS.get(
            known, ExtensionLayer if known.startswith("Extension/") else MarkdownLayer,
        )
        layer = layer_type(**arguments)
        if missing_separator:
            layer.diagnostic_ids.append(self.error(
                "MISSING_LAYER_SEPARATOR", "A layer label must be preceded by a blank line", source,
                suggestion="Insert a blank line before this layer label",
            ))
        if obsolete:
            layer.diagnostic_ids.append(self.error(
                "OBSOLETE_LAYER_SYNTAX", "Layer: prefixes are no longer supported", source,
                suggestion=f"Use a standalone {known or name}: label at column zero",
            ))
        if not obsolete and name and not name[0].isupper():
            layer.diagnostic_ids.append(self.error(
                "INVALID_LAYER_CAPITALIZATION", "A layer name must start with a capital letter", source,
                suggestion=f"Use {known}:",
            ))
        if known is None and not obsolete:
            misplaced_invariant = name in INVARIANT_SECTIONS and any(
                previous.name == "Invariants" for previous in owner.layers
            )
            suggestions = get_close_matches(name.casefold(), LAYER_NAMES, n=1)
            suggestion = f"Use {LAYER_NAMES[suggestions[0]]}:" if suggestions else "Use a registered layer name or Extension/<name>:"
            if misplaced_invariant:
                suggestion = "Use an indented list subsection inside Invariants"
            layer.diagnostic_ids.append(self.error(
                "INVALID_INVARIANT_NESTING" if misplaced_invariant else "UNKNOWN_LAYER",
                f"Unrecognized or misplaced layer {name!r}", source, suggestion=suggestion,
            ))
        layer.complete = not layer.diagnostic_ids
        if invalid_name:
            owner.unknown_structure = True
            return layer
        if owner.entity_kind != "use_case" and known in ("Requirements", "Realized by", "Realizes"):
            layer.complete = False
            layer.diagnostic_ids.append(self.error("INVALID_LAYER_OWNER", f"{known} belongs to a use case", source, phase="model"))
            return layer
        if known == "Invariants":
            subsection_boundaries = [line for line, _ in self.subsection_headers(start + 1, end)]
            requirement_lines = self.requirements(owner, layer, start + 1, end, subsection_boundaries)
            self.invariants(owner, layer, start + 1, end, requirement_lines)
        else:
            self.layer_subsections(owner, layer, start + 1, end)
        if known in STRUCTURAL_LAYERS and known not in ("Invariants", "Detailed Workflow") and not layer.all_entries and not layer.diagnostic_ids:
            layer.complete = False
            layer.diagnostic_ids.append(self.error("EMPTY_LAYER", f"{known} has no recognized entries", source, phase="model"))
        if any(i in self.context.opaque for i in range(start, end)):
            layer.complete = False
        return layer

    def layer_subsections(self, owner: EntityAssembly, layer: LayerBase, start: int, end: int) -> None:
        """UC3/R3.7: shared boundaries -> independently parsed parent-layer content."""
        extractor = WorkflowExtractor(self.snapshot, self.context, self.options.max_nesting_depth)
        headers = []
        for line, name in self.subsection_headers(start, end):
            # Existing declarations reserve their syntax before general subsection dispatch.
            match layer.name:
                case "Workflow anchors":
                    declaration = re.fullmatch(r"(?:step|state)\d+", name) is not None
                case "Realized by" | "Realizes":
                    declaration = re.match(r'`?(?:R\d|UC\d|use-case |requirement )', name) is not None
                case "Uses":
                    declaration = re.match(r'`?(?:"|State/|step\d|state\d|S\d|UC\d|use-case )', name) is not None
                case "Detailed Workflow":
                    declaration = extractor.candidate(line, end, set()) is not None
                case _:
                    declaration = False
            if declaration:
                continue
            headers.append((line, name))
        labels: dict[str, SourceSpan] = {}
        cursor = start
        for ordinal, (begin, name) in enumerate(headers):
            self.layer_content(owner, layer, cursor, begin, labels=labels)
            next_header = headers[ordinal + 1][0] if ordinal + 1 < len(headers) else end
            # A direct requirement resumes layer ownership; nested declarations stay grouped.
            stop = next((line for line in range(begin + 1, next_header)
                         if self.context.boundary_allowed(line) and not self.lines[line][:1].isspace()
                         and (self.lines[line].startswith("Requirement:") or CONVENTIONAL_REQUIREMENT.fullmatch(self.lines[line].rstrip("\r\n")))), next_header)
            section_source = self.snapshot.line_span(begin, begin + 1)
            section_body = self.body(begin + 1, stop)
            parsed = type(layer)(name=layer.name, source=section_source, body=section_body)
            self.layer_content(owner, parsed, begin + 1, stop, indentation=2, labels=labels)
            arguments = dict(name=name, source=section_source, body=section_body)
            if isinstance(parsed, DetailedWorkflowLayer):
                section = WorkflowSubsection(**arguments, entries=parsed.entries, content=parsed.content, complete=parsed.complete, diagnostic_ids=parsed.diagnostic_ids)
            elif parsed.entries or parsed.diagnostic_ids:
                section = TypedSubsection(**arguments, entries=parsed.entries, complete=parsed.complete, diagnostic_ids=parsed.diagnostic_ids)
            else:
                section = MarkdownSubsection(**arguments)
            layer.subsections.append(section)
            layer.complete = layer.complete and parsed.complete
            layer.diagnostic_ids.extend(parsed.diagnostic_ids)
            cursor = stop
        self.layer_content(owner, layer, cursor, end, labels=labels)

    def layer_content(self, owner: EntityAssembly, layer: LayerBase, start: int, end: int, *, indentation: int = 0, labels: dict[str, SourceSpan] | None = None) -> None:
        requirement_lines = self.requirements(owner, layer, start, end, indentation=indentation)
        match layer.name:
            case "Realized by" | "Realizes" | "Uses" | "Workflow anchors":
                self.mapping_rows(owner, layer, start, end, requirement_lines, indentation=indentation)
            case "Detailed Workflow":
                workflows = WorkflowExtractor(self.snapshot, self.context, self.options.max_nesting_depth).detailed(start, end, requirement_lines, labels=labels)
                layer.content.extend(workflows.content)
                self.result.diagnostics.extend(workflows.diagnostics)
                layer.diagnostic_ids.extend(item.diagnostic_id for item in workflows.diagnostics)
                if workflows.diagnostics:
                    layer.complete = False
            case "Tests" | "E2E tests" | "Requirement representations":
                self.reference_fields(owner, layer, start, end, requirement_lines)
        if any(line in self.context.opaque for line in range(start, end)):
            layer.complete = False

    def requirements(self, owner: EntityAssembly, layer: LayerBase, start: int, end: int, boundaries: list[int] | None = None, *, indentation: int = 0) -> set[int]:
        def declaration_allowed(line: int) -> bool:
            if not indentation:
                return self.context.boundary_allowed(line)
            return (self.context.content_allowed(line) and self.context.list_levels.get(line, 0) <= 1
                    and self.lines[line].startswith(" " * indentation))

        heads = [i for i in range(start, end) if declaration_allowed(i) and (
            self.lines[i][indentation:].startswith("Requirement:") or CONVENTIONAL_REQUIREMENT.fullmatch(self.lines[i].rstrip("\r\n"))
        )]
        occupied: set[int] = set()
        for ordinal, line_number in enumerate(heads):
            last = heads[ordinal + 1] if ordinal + 1 < len(heads) else end
            last = next((line for line in boundaries or [] if line_number < line < last), last)
            occupied.update(range(line_number, last))
            raw = self.lines[line_number][indentation:].rstrip("\r\n")
            source = self.snapshot.line_span(line_number, line_number + 1)
            try:
                if owner.entity_kind != "use_case":
                    raise SyntaxFailure("Identified requirements belong to a use case", source)
                form = None
                conventional = CONVENTIONAL_REQUIREMENT.fullmatch(raw)
                if conventional:
                    marker_indent = raw[:conventional.start(1)]
                    if marker_indent not in ("", "  ") or (not indentation and not marker_indent and not conventional[3].strip()):
                        raise SyntaxFailure(
                            "Indent the marker by two spaces or add an inline definition at column zero", source,
                        )
                    identifier, form = conventional[1], conventional[2]
                    definition_start = source.start_offset + indentation + conventional.start(3)
                else:
                    identifier, _ = selector(raw[len("Requirement:"):], source.start_offset + indentation + len("Requirement:"), self.snapshot)
                    definition_start = self.snapshot.line_span(line_number + 1, line_number + 1).start_offset
                definition_end = self.snapshot.line_span(last, last).start_offset
                definition = self.snapshot.source_text[definition_start:definition_end]
                if not definition.strip():
                    raise SyntaxFailure("Requirement definition must not be empty", source)
                layer.entries.append(ValidEntry(value=Requirement(
                    requirement_id=identifier, form=form, defining_layer_name=layer.name, source=source,
                    definition=MarkdownBody(markdown=definition, source=self.snapshot.span(definition_start, definition_end)),
                )))
            except SyntaxFailure as error:
                self.invalid(layer, line_number, last, [(str(error), error.source)], "INVALID_REQUIREMENT_DECLARATION")
        return occupied

    def parse_members(self, part: TextSlice, errors: list[tuple[str, SourceSpan]]) -> list[MemberSelector]:
        parsed: list[MemberSelector] = []
        for item in split_parts(part.text, ",", part.offset, self.snapshot):
            try:
                value = member(item.text, item.offset, self.snapshot)
                if value.kind != "requirement":
                    raise SyntaxFailure("Expected a requirement selector", value.source)
                parsed.append(value)
            except SyntaxFailure as error:
                errors.append((str(error), error.source))
        return parsed

    def parse_targets(self, part: TextSlice, errors: list[tuple[str, SourceSpan]], *, reverse: bool = False) -> list[EntityRef | UnownedRequirementRef]:
        parsed = []
        for item in split_parts(part.text, ",", part.offset, self.snapshot):
            try:
                lexical = unwrap(item.text, item.offset, self.snapshot)
                if reverse and re.fullmatch(rf"R{NUMBER}", lexical.text):
                    local = member(lexical.text, lexical.offset, self.snapshot)
                    parsed.append(UnownedRequirementRef(requirement_selector=local, source=local.source, raw_reference=item.text))
                    continue
                value = reference(item.text, item.offset, self.snapshot)
                if value.owner_selector.kind == "story_id" or value.member_selector and value.member_selector.kind != "requirement":
                    raise SyntaxFailure("Realization/Uses targets must be use cases with optional requirements", value.source)
                if reverse and value.member_selector is None:
                    raise SyntaxFailure("Realizes requires an owner-qualified requirement", value.source)
                parsed.append(value)
            except SyntaxFailure as error:
                errors.append((str(error), error.source))
        return parsed

    def mapping_rows(self, owner: EntityAssembly, layer: LayerBase, start: int, end: int, excluded: set[int], *, indentation: int = 0) -> None:
        for line_number in range(start, end):
            if line_number in excluded or not self.context.content_allowed(line_number) or self.context.list_levels.get(line_number, 0) > (3 if indentation else 1):
                continue
            if not self.lines[line_number].startswith(" " * indentation):
                continue
            raw = self.lines[line_number][indentation:].rstrip("\r\n")
            row = re.fullmatch(r" {0,3}-[ \t]+(.*)", raw)
            if not row:
                if re.match(r"^(?:UC\d|use-case |R\d|requirement |-[ \t]*$)", raw):
                    self.invalid(layer, line_number, line_number + 1, [("Expected a complete bullet mapping row", self.snapshot.line_span(line_number, line_number + 1))])
                continue
            offset = self.snapshot.line_start_offsets[line_number] + indentation + row.start(1)
            source = self.snapshot.line_span(line_number, line_number + 1)
            errors: list[tuple[str, SourceSpan]] = []
            try:
                content = unwrap(row[1], offset, self.snapshot) if layer.name == "Uses" and row[1].strip().startswith("`") and row[1].strip().endswith("`") else trim(row[1], offset)
                match layer.name:
                    case "Realized by":
                        sides = split_parts(content.text, "->", content.offset, self.snapshot)
                        if len(sides) != 2:
                            raise SyntaxFailure("Expected exactly one mapping arrow", source)
                        sources = self.parse_members(sides[0], errors)
                        targets = self.parse_targets(sides[1], errors)
                        if not errors:
                            layer.entries.append(ValidEntry(value=ForwardRealization(source_requirements=sources, targets=targets, source=source)))
                    case "Realizes":
                        sources = self.parse_targets(content, errors, reverse=True)
                        if not errors:
                            layer.entries.append(ValidEntry(value=ReverseRealization(sources=sources, source=source)))
                    case "Uses":
                        sides = split_parts(content.text, "->", content.offset, self.snapshot)
                        if len(sides) != 2:
                            raise SyntaxFailure("Expected exactly one Uses arrow", source)
                        targets = self.parse_targets(sides[1], errors)
                        left = unwrap(sides[0].text, sides[0].offset, self.snapshot)
                        if left.text.startswith('"'):
                            selected, _ = selector(left.text, left.offset, self.snapshot)
                            selected_kind = "label"
                        elif left.text.startswith("State/"):
                            selected, selected_kind = left.text.removeprefix("State/"), "story_state"
                            if owner.entity_kind != "story_state" or owner.entity_id != selected:
                                raise SyntaxFailure("State-owned Uses must name its owning State/<key>", source)
                        else:
                            selected = reference(left.text, left.offset, self.snapshot)
                            selected_kind = "anchor"
                            if selected.member_selector is None or selected.member_selector.kind not in ("step", "state"):
                                raise SyntaxFailure("Uses source must be a declared step/state anchor or quoted label", selected.source)
                        if not errors:
                            layer.entries.append(ValidEntry(value=UseMapping(source_selector=selected, selector_kind=selected_kind, targets=targets, source=source)))
                    case "Workflow anchors":
                        matched = re.fullmatch(r"((?:step|state)[1-9]\d*):[ \t]*(.*)", content.text)
                        if not matched:
                            raise SyntaxFailure("Expected step<number>: label or state<number>: label", source)
                        layer.entries.append(ValidEntry(value=WorkflowAnchor(anchor_id=matched[1], label=matched[2].strip(), source=source)))
            except SyntaxFailure as error:
                errors.append((str(error), error.source))
            except ValidationError as error:
                errors.extend((f"{'.'.join(map(str, detail['loc']))}: {detail['msg']}", source) for detail in error.errors())
            if errors:
                self.invalid(layer, line_number, line_number + 1, errors)

    def owned_member_ref(self, owner: EntityAssembly, text: str, offset: int) -> EntityRef:
        try:
            local = member(text, offset, self.snapshot)
        except SyntaxFailure:
            return reference(text, offset, self.snapshot)
        kind = "story_id" if owner.entity_kind == "story" else "use_case_number" if owner.number else "use_case_title"
        value = owner.entity_id if kind == "story_id" else owner.number if kind == "use_case_number" else owner.title
        return EntityRef(owner_selector=OwnerSelector(kind=kind, value=value, source=local.source), member_selector=local, source=local.source, raw_reference=text, owner_local=True)

    def subsection_headers(self, start: int, end: int) -> list[tuple[int, str]]:
        """UC3/R3.6: discover subsection boundaries independently of recognized names."""
        headers = []
        for line in range(start, end):
            if not self.context.content_allowed(line):
                continue
            matched = re.fullmatch(r"- ([^\r\n]+):[ \t]*", self.lines[line].rstrip("\r\n"))
            if matched and matched[1].strip():
                headers.append((line, matched[1].strip()))
        return headers

    def invariant_nesting(self, section: LayerBase | StructuredSubsection, start: int, end: int, excluded: set[int]) -> None:
        """Check typed-entry nesting only where a structural owner is established."""
        for i in range(start, end):
            if i in excluded or not self.context.content_allowed(i):
                continue
            raw = self.lines[i].rstrip("\r\n")
            subsection_name = re.sub(r"^-\s*", "", raw.strip()).rstrip(":").strip()
            misplaced_section = not raw.startswith("      ") and subsection_name in INVARIANT_SECTIONS
            misplaced_entry = re.match(r"^ {0,5}-\s+`?[IDN]\d", raw) and not raw.startswith("  - ")
            if misplaced_section or misplaced_entry:
                self.invalid(section, i, i + 1, [("Invariant subsections and entries must use their declared list indentation", self.snapshot.line_span(i, i + 1))], "INVALID_INVARIANT_NESTING")

    def invariants(self, owner: EntityAssembly, layer: InvariantsLayer, start: int, end: int, excluded: set[int]) -> None:
        """UC3/R3.6: bounded subsections -> ordered general or independently typed models."""
        headers = [(line, name) for line, name in self.subsection_headers(start, end) if line not in excluded]
        self.invariant_nesting(layer, start, headers[0][0] if headers else end, excluded)
        standards = [name for _, name in headers if name in INVARIANT_SECTIONS]
        if len(set(standards)) != len(standards):
            self.invalid(layer, start, end, [("Repeated standard invariant subsection", layer.source)], "DUPLICATE_INVARIANT_SECTION")
        for ordinal, (begin, name) in enumerate(headers):
            next_header = headers[ordinal + 1][0] if ordinal + 1 < len(headers) else end
            stop = next((line for line in range(begin + 1, next_header) if line in excluded), next_header)
            section_type = {
                "Rationale": RationaleSubsection, "State invariants": StateInvariantsSubsection,
                "Derivations": DerivationsSubsection,
            }.get(name, MarkdownSubsection)
            section = section_type(name=name, source=self.snapshot.line_span(begin, begin + 1), body=self.body(begin + 1, stop))
            layer.subsections.append(section)
            if isinstance(section, MarkdownSubsection):
                continue
            self.invariant_nesting(section, begin + 1, stop, excluded)
            entry_starts = [i for i in range(begin + 1, stop) if i not in excluded and self.context.content_allowed(i) and re.match(r"^  - ", self.lines[i])]
            if not entry_starts:
                self.invalid(section, begin, stop, [(f"{name} requires entries indented two spaces beneath its subsection", self.snapshot.line_span(begin, stop))], "INVALID_INVARIANT_STRUCTURE")
            if name == "Rationale" and entry_starts:
                preamble = [i for i in range(begin + 1, entry_starts[0]) if i not in excluded and self.lines[i].strip()]
                if preamble:
                    self.invalid(section, begin + 1, entry_starts[0], [("Rationale text must belong to a note entry", self.snapshot.line_span(preamble[0], preamble[-1] + 1))], "INVALID_RATIONALE_STRUCTURE")
            for entry_ordinal, i in enumerate(entry_starts):
                last = entry_starts[entry_ordinal + 1] if entry_ordinal + 1 < len(entry_starts) else stop
                raw = self.lines[i].rstrip("\r\n")
                source = self.snapshot.line_span(i, last)
                try:
                    if name == "Rationale":
                        # A layer-level requirement owns its source independently of the note.
                        note_end = next((line for line in range(i + 1, last) if line in excluded), last)
                        self.rationale(owner, section, i, note_end, excluded)
                        continue
                    if name == "State invariants":
                        matched = re.fullmatch(rf"  - `(I{NUMBER})` at `([^`]+)`:[ \t]*(.+)", raw)
                        if not matched:
                            raise SyntaxFailure("Expected - `I<number>` at `state`: assertion beneath State invariants", source)
                        assertion_start = self.snapshot.line_start_offsets[i] + matched.start(3)
                        assertion = self.snapshot.source_text[assertion_start:source.end_offset]
                        section.entries.append(ValidEntry(value=InvariantCheckpoint(
                            invariant_id=matched[1], state_label=matched[2],
                            assertion=MarkdownBody(markdown=assertion, source=self.snapshot.span(assertion_start, source.end_offset)), source=source,
                        )))
                    else:
                        header = re.fullmatch(rf"  - `(D{NUMBER}): (.+)`[ \t]*", raw)
                        if not header:
                            raise SyntaxFailure("Expected - `D<number>: I... -> I...` beneath Derivations", source)
                        offset = self.snapshot.line_start_offsets[i] + header.start(2)
                        sides = split_parts(header[2], "->", offset, self.snapshot)
                        if len(sides) != 2:
                            raise SyntaxFailure("Derivation requires source and target invariant lists", source)
                        sources = [self.owned_member_ref(owner, part.text, part.offset) for part in split_parts(sides[0].text, ",", sides[0].offset, self.snapshot)]
                        targets = [self.owned_member_ref(owner, part.text, part.offset) for part in split_parts(sides[1].text, ",", sides[1].offset, self.snapshot)]
                        if any(ref.member_selector is None or ref.member_selector.kind != "invariant" for ref in sources + targets):
                            raise SyntaxFailure("Derivations reference invariant members", source)
                        transition = next((self.lines[j].split(":", 1)[1].strip().strip("`") for j in range(i + 1, last) if re.match(r"^    - workflow transition:", self.lines[j])), "")
                        proof_line = next((j for j in range(i + 1, last) if re.match(r"^    - (?:justification|proof):", self.lines[j])), None)
                        if not transition or proof_line is None:
                            raise SyntaxFailure("Derivation requires workflow transition and justification/proof", source)
                        proof_offset = self.snapshot.line_start_offsets[proof_line] + self.lines[proof_line].index(":") + 1
                        proof = self.snapshot.source_text[proof_offset:source.end_offset]
                        if not proof.strip():
                            raise SyntaxFailure("Derivation justification must not be empty", source)
                        section.entries.append(ValidEntry(value=InvariantDerivation(
                            derivation_id=header[1], source_invariants=sources, target_invariants=targets,
                            transition_label=transition, justification=MarkdownBody(markdown=proof, source=self.snapshot.span(proof_offset, source.end_offset)), source=source,
                        )))
                except SyntaxFailure as error:
                    self.invalid(section, i, last, [(str(error), error.source)], "INVALID_INVARIANT_STRUCTURE")
                except ValidationError as error:
                    self.invalid(section, i, last, [(f"{'.'.join(map(str, detail['loc']))}: {detail['msg']}", source) for detail in error.errors()], "INVALID_INVARIANT_STRUCTURE")
            if not section.complete:
                layer.complete = False
                layer.diagnostic_ids.extend(section.diagnostic_ids)
        # General Markdown subsections are valid even without typed checkpoints.
        if not headers and layer.complete:
            self.invalid(layer, start, end, [("Invariants requires recognized list subsections", layer.source)], "INVALID_INVARIANT_STRUCTURE")

    def rationale(self, owner: EntityAssembly, layer: RationaleSubsection, start: int, end: int, excluded: set[int]) -> None:
        """UC3/R3.5: bound note fields, retain Markdown, and collect independent errors."""
        source = self.snapshot.line_span(start, end)
        header = self.lines[start].rstrip("\r\n")
        named = re.fullmatch(rf"  - `(N{NUMBER})`:[ \t]*", header)
        anonymous = header.startswith("  - note:")
        if named is None and not anonymous:
            self.invalid(layer, start, end, [("Expected a backticked N-number followed by a colon, or an anonymous - note: entry", source)], "INVALID_RATIONALE_STRUCTURE")
            return

        # Note source -> direct-child field boundaries; literals/deeper lists retain text ownership.
        errors: list[tuple[str, SourceSpan]] = []
        field_starts = [start] if anonymous else []
        for line in range(start + 1, end):
            if line in excluded or not self.context.content_allowed(line):
                continue
            raw = self.lines[line].rstrip("\r\n")
            if raw.startswith("    - "):
                field_starts.append(line)
            elif re.match(r"^ {0,5}-\s*(?:note|assessment|qualification|reason|replacement|used by):", raw):
                errors.append(("Rationale fields must be list items indented four spaces", self.snapshot.line_span(line, line + 1)))
        first_field = field_starts[0] if field_starts else end
        if any(self.lines[line].strip() for line in range(start + 1, first_field)):
            errors.append(("Rationale content must belong to a named field", self.snapshot.line_span(start + 1, first_field)))

        # Bounded fields -> exact text bodies and scalar values, without choosing duplicate winners.
        fields: dict[str, MarkdownBody] = {}
        allowed = {"note", "assessment", "qualification", "reason", "replacement", "used by"}
        for ordinal, line in enumerate(field_starts):
            stop = field_starts[ordinal + 1] if ordinal + 1 < len(field_starts) else end
            raw = self.lines[line].rstrip("\r\n")
            matched = re.fullmatch(r"(?:  |    )- ([^:]+):(.*)", raw)
            field_source = self.snapshot.line_span(line, stop)
            if matched is None or matched[1] not in allowed:
                errors.append(("Unknown or malformed rationale field", self.snapshot.line_span(line, line + 1)))
                continue
            name = matched[1]
            if name in fields:
                errors.append((f"Repeated rationale field: {name}", field_source))
                continue
            offset = self.snapshot.line_start_offsets[line] + matched.start(2)
            text = self.snapshot.source_text[offset:field_source.end_offset].rstrip("\r\n")
            body = MarkdownBody(markdown=text, source=self.snapshot.span(offset, offset + len(text)))
            fields[name] = body
            if not text.strip():
                errors.append((f"Rationale {name} must not be empty", body.source))
            if name in {"assessment", "used by"}:
                if any(self.lines[next_line].strip() for next_line in range(line + 1, stop)):
                    errors.append((f"Rationale {name} must occupy one line", field_source))
            else:
                for next_line in range(line + 1, stop):
                    if self.lines[next_line].strip() and not self.lines[next_line].startswith("      "):
                        errors.append(("Rationale Markdown continuation must be indented at least six spaces", self.snapshot.line_span(next_line, next_line + 1)))

        for name in ("note", "assessment"):
            if name not in fields:
                errors.append((f"Rationale requires {name}", source))
        assessment = fields["assessment"].markdown.strip() if "assessment" in fields else None
        if assessment is not None and assessment not in {"supported", "qualified", "unsupported", "rejected"}:
            errors.append(("Rationale assessment must be supported, qualified, unsupported or rejected", fields["assessment"].source))
        refs: list[EntityRef] = []
        if "used by" in fields:
            body = fields["used by"]
            try:
                for part in split_parts(body.markdown, ",", body.source.start_offset, self.snapshot):
                    try:
                        ref = self.owned_member_ref(owner, part.text, part.offset)
                        if ref.member_selector is None or ref.member_selector.kind != "derivation":
                            raise SyntaxFailure("Rationale used by requires derivation members", ref.source)
                        refs.append(ref)
                    except SyntaxFailure as error:
                        errors.append((str(error), error.source))
            except SyntaxFailure as error:
                errors.append((str(error), error.source))
        if errors:
            self.invalid(layer, start, end, errors, "INVALID_RATIONALE_STRUCTURE")
            return
        layer.entries.append(ValidEntry(value=RationaleNote(
            rationale_id=named[1] if named else None, note=fields["note"], assessment=assessment,
            qualification=fields.get("qualification"), reason=fields.get("reason"),
            replacement=fields.get("replacement"), used_by=refs, source=source,
        )))

    def reference_fields(self, owner: EntityAssembly, layer: LayerBase, start: int, end: int, excluded: set[int]) -> None:
        for i in range(start, end):
            if i in excluded or not self.context.content_allowed(i):
                continue
            matched = re.match(r"^\s+(?:-\s+)?(requirements|source):[ \t]*(.*)", self.lines[i].rstrip("\r\n"))
            if not matched or matched[1] == "source" and layer.name != "Requirement representations":
                continue
            errors: list[tuple[str, SourceSpan]] = []
            refs = []
            offset = self.snapshot.line_start_offsets[i] + matched.start(2)
            try:
                for part in split_parts(matched[2], ",", offset, self.snapshot):
                    try:
                        unwrapped = unwrap(part.text, part.offset, self.snapshot)
                        if re.fullmatch(rf"R{NUMBER}", unwrapped.text) or unwrapped.text.startswith("requirement "):
                            refs.append(member(part.text, part.offset, self.snapshot))
                        else:
                            refs.append(reference(part.text, part.offset, self.snapshot))
                    except SyntaxFailure as error:
                        errors.append((str(error), error.source))
                if not errors:
                    layer.entries.append(ValidEntry(value=ReferenceField(field_name=matched[1], references=refs, source=self.snapshot.line_span(i, i + 1))))
            except SyntaxFailure as error:
                errors.append((str(error), error.source))
            if errors:
                self.invalid(layer, i, i + 1, errors, "INVALID_REFERENCE_FIELD")


def parse_document(snapshot: DocumentSnapshot, options: ValidationOptions) -> ParsedDocument:
    """UC2/UC3 public parser: malformed input is data, unexpected exceptions propagate."""
    return PlanningParser(snapshot, options).parse()
