"""Typed contracts for planning-spec workflows UC1 through UC6."""

from __future__ import annotations

import re
from bisect import bisect_right
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator, model_validator

from . import __version__

NUMBER_PATTERN = r"[1-9]\d*(?:\.[1-9]\d*)*"
UseCaseNumber = Annotated[StrictStr, Field(pattern=rf"^{NUMBER_PATTERN}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FrozenModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ValidationOptions(FrozenModel):
    workspace_root: Path
    ruleset: Literal["structure_and_references"] = "structure_and_references"
    max_file_bytes: int = Field(default=10_485_760, gt=0, strict=True)
    max_total_bytes: int = Field(default=104_857_600, gt=0, strict=True)
    max_nesting_depth: int = Field(default=128, gt=0, le=256, strict=True)


class SourceSpan(FrozenModel):
    document_id: str
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    start_line: int = Field(ge=1)
    start_column: int = Field(ge=1)
    end_line: int = Field(ge=1)
    end_column: int = Field(ge=1)

    @model_validator(mode="after")
    def ordered_span(self) -> SourceSpan:
        if self.end_offset < self.start_offset:
            raise ValueError("source span ends before its start")
        return self


class InputLocation(FrozenModel):
    document_id: str
    input_ordinal: int = 0


class RelatedLocation(StrictModel):
    message: str
    location: SourceSpan | InputLocation


class Diagnostic(StrictModel):
    diagnostic_id: str
    code: str
    severity: Literal["error", "warning", "info"] = "error"
    phase: Literal["input", "parse", "model", "reference", "graph", "tool"]
    message: str
    primary_location: SourceSpan | InputLocation
    location_precision: Literal["token", "block", "input"] = "token"
    related_locations: list[RelatedLocation] = Field(default_factory=list)
    entity_id: str | None = None
    owner_title: str | None = None
    layer_name: str | None = None
    suggested_action: str | None = None
    caused_by: list[str] = Field(default_factory=list)


class DocumentSnapshot(FrozenModel):
    document_id: str
    display_path: str
    source_text: str
    utf8_bom: bool = False
    content_sha256: str
    byte_count: int
    line_start_offsets: tuple[int, ...]
    input_ordinal: int = 0

    @classmethod
    def from_text(cls, document_id: str, text: str) -> DocumentSnapshot:
        """Create an in-memory snapshot for library callers and tests (UC1)."""
        from hashlib import sha256

        encoded = text.encode("utf-8")
        return cls(
            document_id=document_id, display_path=document_id, source_text=text,
            content_sha256=sha256(encoded).hexdigest(), byte_count=len(encoded),
            line_start_offsets=(0, *(m.end() for m in re.finditer(r"\r\n|\r|\n", text))),
        )

    def span(self, start: int, end: int | None = None) -> SourceSpan:
        end = start if end is None else end
        if not 0 <= start <= end <= len(self.source_text):
            raise ValueError("source offsets outside snapshot")
        first = bisect_right(self.line_start_offsets, start) - 1
        last = bisect_right(self.line_start_offsets, end) - 1
        return SourceSpan(
            document_id=self.document_id, start_offset=start, end_offset=end,
            start_line=first + 1, start_column=start - self.line_start_offsets[first] + 1,
            end_line=last + 1, end_column=end - self.line_start_offsets[last] + 1,
        )

    def line_span(self, start: int, end: int) -> SourceSpan:
        offsets = self.line_start_offsets
        first = offsets[start] if start < len(offsets) else len(self.source_text)
        last = offsets[end] if end < len(offsets) else len(self.source_text)
        return self.span(first, last)

    def lines(self) -> list[str]:
        offsets = (*self.line_start_offsets, len(self.source_text))
        return [self.source_text[a:b] for a, b in zip(offsets, offsets[1:])]


class DocumentSet(StrictModel):
    documents: list[DocumentSnapshot]
    options: ValidationOptions
    input_paths: list[str] = Field(default_factory=list)
    failed_inputs: list[Diagnostic] = Field(default_factory=list)
    load_duration_ms: float = 0


class MarkdownBody(StrictModel):
    markdown: str
    source: SourceSpan


class RecoveredBlock(StrictModel):
    block_kind: Literal["region", "entity", "workflow", "layer", "entry", "prose", "opaque"]
    source: SourceSpan
    raw_markdown: str
    trust: Literal["exact", "uncertain"] = "exact"
    children: list[RecoveredBlock] = Field(default_factory=list)
    diagnostic_ids: list[str] = Field(default_factory=list)


class WorkflowState(StrictModel):
    kind: Literal["state"] = "state"
    text: StrictStr = Field(min_length=1)
    name: StrictStr = Field(min_length=1)
    type_annotation: StrictStr | None = None
    source: SourceSpan


class WorkflowTransition(StrictModel):
    label: StrictStr = Field(min_length=1)
    source: SourceSpan


class WorkflowSequence(StrictModel):
    kind: Literal["sequence"] = "sequence"
    operands: list["WorkflowExpression"] = Field(min_length=2)
    transitions: list[WorkflowTransition] = Field(min_length=1)
    source: SourceSpan

    @model_validator(mode="after")
    def connected_sequence(self) -> WorkflowSequence:
        if len(self.transitions) != len(self.operands) - 1:
            raise ValueError("A sequence requires one transition between each pair of operands")
        return self


class WorkflowParallel(StrictModel):
    kind: Literal["parallel"] = "parallel"
    branches: list["WorkflowExpression"] = Field(min_length=1)
    source: SourceSpan


class WorkflowConditional(StrictModel):
    kind: Literal["conditional"] = "conditional"
    branches: list["WorkflowExpression"] = Field(min_length=1)
    source: SourceSpan


class WorkflowLoop(StrictModel):
    kind: Literal["loop"] = "loop"
    condition: StrictStr = Field(min_length=1)
    body: "WorkflowExpression"
    source: SourceSpan


class WorkflowScope(StrictModel):
    kind: Literal["scope"] = "scope"
    body: "WorkflowExpression"
    source: SourceSpan


WorkflowExpression = Annotated[
    WorkflowState | WorkflowSequence | WorkflowParallel | WorkflowConditional | WorkflowLoop | WorkflowScope,
    Field(discriminator="kind"),
]
for workflow_model in (WorkflowSequence, WorkflowParallel, WorkflowConditional, WorkflowLoop, WorkflowScope):
    workflow_model.model_rebuild()


class WorkflowChain(StrictModel):
    label: StrictStr | None = None
    label_source: SourceSpan | None = None
    body: MarkdownBody
    expression: WorkflowExpression
    source: SourceSpan


class ValidWorkflowChain(StrictModel):
    content_kind: Literal["chain"] = "chain"
    value: WorkflowChain


class InvalidWorkflowChain(StrictModel):
    content_kind: Literal["invalid_chain"] = "invalid_chain"
    label: str | None = None
    raw_block: RecoveredBlock
    diagnostic_ids: list[str]


class WorkflowProse(StrictModel):
    content_kind: Literal["prose"] = "prose"
    body: MarkdownBody


WorkflowChainResult = Annotated[ValidWorkflowChain | InvalidWorkflowChain, Field(discriminator="content_kind")]
WorkflowContent = Annotated[WorkflowProse | ValidWorkflowChain | InvalidWorkflowChain, Field(discriminator="content_kind")]


class EntityKey(FrozenModel):
    document_id: str
    declaration_start_offset: int


class OwnerSelector(FrozenModel):
    kind: Literal["use_case_number", "use_case_title", "story_id"]
    value: StrictStr = Field(min_length=1)
    source: SourceSpan

    @model_validator(mode="after")
    def valid_selector(self) -> OwnerSelector:
        pattern = {"use_case_number": NUMBER_PATTERN, "story_id": "S" + NUMBER_PATTERN}.get(self.kind)
        if not self.value.strip() or pattern is not None and re.fullmatch(pattern, self.value) is None:
            raise ValueError("Invalid owner selector for its declared kind")
        return self


class MemberSelector(FrozenModel):
    kind: Literal["requirement", "invariant", "derivation", "rationale", "step", "state"]
    value: StrictStr = Field(min_length=1)
    source: SourceSpan

    @model_validator(mode="after")
    def valid_selector(self) -> MemberSelector:
        pattern = {"invariant": "I" + NUMBER_PATTERN, "derivation": "D" + NUMBER_PATTERN, "rationale": "N" + NUMBER_PATTERN, "step": r"step[1-9]\d*", "state": r"state[1-9]\d*"}.get(self.kind)
        if not self.value.strip() or pattern is not None and re.fullmatch(pattern, self.value) is None:
            raise ValueError("Invalid member selector for its declared kind")
        return self


class EntityRef(StrictModel):
    document_path: str | None = None
    owner_selector: OwnerSelector
    member_selector: MemberSelector | None = None
    spelling: Literal["compact", "explicit", "mixed"] = "compact"
    raw_reference: str
    source: SourceSpan
    owner_local: bool = False # Internal normalization of an explicitly owner-local invariant member.


class UnownedRequirementRef(StrictModel):
    requirement_selector: MemberSelector
    source: SourceSpan
    raw_reference: str


class Requirement(StrictModel):
    entry_kind: Literal["requirement"] = "requirement"
    requirement_id: StrictStr = Field(min_length=1)
    form: str | None = None
    definition: MarkdownBody
    defining_layer_name: str
    source: SourceSpan


class ForwardRealization(StrictModel):
    entry_kind: Literal["forward"] = "forward"
    source_requirements: list[MemberSelector] = Field(min_length=1)
    targets: list[EntityRef] = Field(min_length=1)
    source: SourceSpan


class ReverseRealization(StrictModel):
    entry_kind: Literal["reverse"] = "reverse"
    sources: list[EntityRef | UnownedRequirementRef] = Field(min_length=1)
    source: SourceSpan


class UseMapping(StrictModel):
    entry_kind: Literal["uses"] = "uses"
    source_selector: EntityRef | StrictStr
    selector_kind: Literal["anchor", "label", "story_state"]
    targets: list[EntityRef] = Field(min_length=1)
    source: SourceSpan


class WorkflowAnchor(StrictModel):
    entry_kind: Literal["anchor"] = "anchor"
    anchor_id: StrictStr = Field(pattern=r"^(?:step|state)[1-9]\d*$")
    label: StrictStr = Field(min_length=1)
    source: SourceSpan


class InvariantCheckpoint(StrictModel):
    entry_kind: Literal["invariant"] = "invariant"
    invariant_id: StrictStr = Field(pattern=rf"^I{NUMBER_PATTERN}$")
    state_label: StrictStr = Field(min_length=1)
    assertion: MarkdownBody
    source: SourceSpan


class InvariantDerivation(StrictModel):
    entry_kind: Literal["derivation"] = "derivation"
    derivation_id: StrictStr = Field(pattern=rf"^D{NUMBER_PATTERN}$")
    source_invariants: list[EntityRef] = Field(min_length=1)
    target_invariants: list[EntityRef] = Field(min_length=1)
    transition_label: StrictStr = Field(min_length=1)
    justification: MarkdownBody
    source: SourceSpan


class RationaleNote(StrictModel):
    """UC3/R3.5: supplied rationale, kept separate from accepted derivations."""

    entry_kind: Literal["rationale"] = "rationale"
    rationale_id: Annotated[StrictStr, Field(pattern=rf"^N{NUMBER_PATTERN}$")] | None = None
    note: MarkdownBody
    assessment: Literal["supported", "qualified", "unsupported", "rejected"]
    qualification: MarkdownBody | None = None
    reason: MarkdownBody | None = None
    replacement: MarkdownBody | None = None
    used_by: list[EntityRef] = Field(default_factory=list)
    source: SourceSpan

    @field_validator("note", "qualification", "reason", "replacement")
    @classmethod
    def nonempty_body(cls, value: MarkdownBody | None) -> MarkdownBody | None:
        if value is not None and not value.markdown.strip():
            raise ValueError("A supplied rationale text field must not be empty")
        return value

    @field_validator("used_by")
    @classmethod
    def derivation_targets(cls, value: list[EntityRef]) -> list[EntityRef]:
        if any(ref.member_selector is None or ref.member_selector.kind != "derivation" for ref in value):
            raise ValueError("used by requires derivation members")
        return value


class ReferenceField(StrictModel):
    entry_kind: Literal["reference_field"] = "reference_field"
    field_name: str
    references: list[EntityRef | MemberSelector] = Field(min_length=1)
    source: SourceSpan


TypedEntry = Annotated[
    Requirement | ForwardRealization | ReverseRealization | UseMapping
    | WorkflowAnchor | InvariantCheckpoint | InvariantDerivation | RationaleNote | ReferenceField,
    Field(discriminator="entry_kind"),
]


class ValidEntry(StrictModel):
    status: Literal["valid"] = "valid"
    value: TypedEntry


class InvalidEntry(StrictModel):
    status: Literal["invalid", "blocked"] = "invalid"
    raw_block: RecoveredBlock
    diagnostic_ids: list[str]


EntryResult = Annotated[ValidEntry | InvalidEntry, Field(discriminator="status")]


class MarkdownSubsection(StrictModel):
    kind: Literal["markdown"] = "markdown"
    name: StrictStr = Field(min_length=1)
    body: MarkdownBody
    source: SourceSpan


class StructuredSubsection(StrictModel):
    name: StrictStr = Field(min_length=1)
    body: MarkdownBody
    source: SourceSpan
    entries: list[EntryResult] = Field(default_factory=list)
    complete: bool = True
    diagnostic_ids: list[str] = Field(default_factory=list)


class TypedSubsection(StructuredSubsection):
    kind: Literal["structured"] = "structured"


class WorkflowSubsection(StructuredSubsection):
    kind: Literal["workflow"] = "workflow"
    content: list[WorkflowContent] = Field(default_factory=list)

    @property
    def chains(self) -> list[WorkflowChainResult]:
        return [item for item in self.content if isinstance(item, (ValidWorkflowChain, InvalidWorkflowChain))]


class RationaleSubsection(StructuredSubsection):
    kind: Literal["rationale"] = "rationale"
    name: Literal["Rationale"] = "Rationale"


class StateInvariantsSubsection(StructuredSubsection):
    kind: Literal["state_invariants"] = "state_invariants"
    name: Literal["State invariants"] = "State invariants"


class DerivationsSubsection(StructuredSubsection):
    kind: Literal["derivations"] = "derivations"
    name: Literal["Derivations"] = "Derivations"


LayerSubsection = Annotated[
    MarkdownSubsection | TypedSubsection | WorkflowSubsection
    | RationaleSubsection | StateInvariantsSubsection | DerivationsSubsection,
    Field(discriminator="kind"),
]


class LayerBase(StrictModel):
    name: str
    source: SourceSpan
    body: MarkdownBody
    entries: list[EntryResult] = Field(default_factory=list)
    subsections: list[LayerSubsection] = Field(default_factory=list)
    complete: bool = True
    diagnostic_ids: list[str] = Field(default_factory=list)

    @property
    def all_entries(self) -> list[EntryResult]:
        """Source-ordered entries with one serialized owner per occurrence."""
        entries = [*self.entries, *(
            entry for section in self.subsections if isinstance(section, StructuredSubsection)
            for entry in section.entries
        )]
        return sorted(entries, key=lambda entry: (
            entry.value.source if isinstance(entry, ValidEntry) else entry.raw_block.source
        ).start_offset)


class RequirementsLayer(LayerBase):
    kind: Literal["requirements"] = "requirements"


class ForwardLayer(LayerBase):
    kind: Literal["realized_by"] = "realized_by"


class ReverseLayer(LayerBase):
    kind: Literal["realizes"] = "realizes"


class UsesLayer(LayerBase):
    kind: Literal["uses"] = "uses"


class InvariantsLayer(LayerBase):
    kind: Literal["invariants"] = "invariants"


class DetailedWorkflowLayer(LayerBase):
    kind: Literal["detailed_workflow"] = "detailed_workflow"
    content: list[WorkflowContent] = Field(default_factory=list)

    @property
    def chains(self) -> list[WorkflowChainResult]:
        chains = [item for item in self.content if isinstance(item, (ValidWorkflowChain, InvalidWorkflowChain))]
        chains.extend(chain for section in self.subsections if isinstance(section, WorkflowSubsection) for chain in section.chains)
        return sorted(chains, key=lambda chain: (
            chain.value.source if isinstance(chain, ValidWorkflowChain) else chain.raw_block.source
        ).start_offset)


class AnchorsLayer(LayerBase):
    kind: Literal["workflow_anchors"] = "workflow_anchors"


class MarkdownLayer(LayerBase):
    kind: Literal["markdown"] = "markdown"


class ExtensionLayer(LayerBase):
    kind: Literal["extension"] = "extension"


class UnknownLayer(LayerBase):
    kind: Literal["unknown"] = "unknown"


Layer = Annotated[
    RequirementsLayer | ForwardLayer | ReverseLayer | UsesLayer | InvariantsLayer
    | AnchorsLayer | DetailedWorkflowLayer | MarkdownLayer | ExtensionLayer | UnknownLayer,
    Field(discriminator="kind"),
]


class UseCase(StrictModel):
    entity_kind: Literal["use_case"] = "use_case"
    declaration_key: EntityKey
    number: UseCaseNumber | None
    title: StrictStr = Field(min_length=1)
    header_spelling: Literal["numbered", "uc_prefixed", "unnumbered", "quoted_title"]
    workflow: WorkflowChain
    layers: list[Layer]
    source: SourceSpan


class UserStory(StrictModel):
    entity_kind: Literal["story"] = "story"
    declaration_key: EntityKey
    entity_id: StrictStr = Field(pattern=rf"^S{NUMBER_PATTERN}$")
    title: StrictStr = Field(min_length=1)
    workflow: WorkflowChain
    layers: list[Layer]
    source: SourceSpan


class StoryState(StrictModel):
    entity_kind: Literal["story_state"] = "story_state"
    declaration_key: EntityKey
    state_key: str
    title: StrictStr = Field(min_length=1)
    layers: list[Layer]
    source: SourceSpan


class EntityAssembly(StrictModel):
    """An exact header and independently usable layers, even with invalid children."""

    key: EntityKey
    entity_kind: Literal["use_case", "story", "story_state"]
    title: str
    number: str | None = None
    entity_id: str | None = None
    header_spelling: str = "unnumbered"
    workflow: WorkflowChain | None = None
    workflow_result: WorkflowChainResult | None = None
    layers: list[Layer] = Field(default_factory=list)
    source: SourceSpan
    complete: bool = True
    unknown_structure: bool = False
    diagnostic_ids: list[str] = Field(default_factory=list)
    value: UseCase | UserStory | StoryState | None = None


class ParsedDocument(StrictModel):
    snapshot: DocumentSnapshot
    blocks: list[RecoveredBlock] = Field(default_factory=list)
    entities: list[EntityAssembly] = Field(default_factory=list)
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    parse_complete: bool = True
    duration_ms: float = 0


class CheckResult(StrictModel):
    check: str
    scope: SourceSpan | InputLocation
    status: Literal["passed", "failed", "blocked", "not_applicable"]
    diagnostic_ids: list[str] = Field(default_factory=list)


class SnapshotIdentity(FrozenModel):
    document_id: str
    content_sha256: str
    byte_count: int


class DocumentSummary(StrictModel):
    document_id: str
    entities: int
    valid_entities: int
    structure_complete: bool
    opaque_spans: list[SourceSpan]


class ValidationMetrics(StrictModel):
    files: int = 0
    bytes: int = 0
    entities: int = 0
    errors: int = 0
    warnings: int = 0
    blocked_checks: int = 0
    references: int = 0
    normalized_edges: int = 0
    workflow_chains: int = 0
    invalid_workflow_chains: int = 0
    load_duration_ms: float = 0
    parse_duration_ms: float = 0
    graph_duration_ms: float = 0
    total_duration_ms: float = 0


class ValidationReport(StrictModel):
    report_schema_version: Literal[1] = 1
    tool_version: str = __version__
    status: Literal["passed", "failed", "incomplete", "tool_error"]
    ruleset: Literal["structure_and_references"] = "structure_and_references"
    input_snapshots: list[SnapshotIdentity]
    input_set_fingerprint: str
    options_fingerprint: str
    documents: list[DocumentSummary]
    diagnostics: list[Diagnostic]
    checks: list[CheckResult]
    analysis_complete: bool
    excluded_checks: list[str]
    metrics: ValidationMetrics


class ValidationResult(StrictModel):
    report: ValidationReport
    documents: list[ParsedDocument]
