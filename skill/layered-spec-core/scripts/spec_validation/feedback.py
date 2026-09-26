"""UC6: report freshness and bounded feedback; never edits source or calls a model."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .models import Diagnostic, DocumentSet, EntityRef, SnapshotIdentity, SourceSpan, StrictModel, ValidationReport
from .reporting import fingerprint, input_fingerprint, options_fingerprint


class DeclarationSelectorChange(StrictModel):
    old_reference: EntityRef
    new_reference: EntityRef
    before_location: SourceSpan
    after_location: SourceSpan | None = None


class LocatedResolvedReference(StrictModel):
    reference: EntityRef
    target_location: SourceSpan


class ReferenceUpdateIntent(StrictModel):
    before_snapshots: list[SnapshotIdentity]
    changes: list[DeclarationSelectorChange] = Field(min_length=1)
    incoming_references: list[LocatedResolvedReference]
    reference_search_scope: list[str] = Field(min_length=1)
    discovery_complete: bool


class RepairAttempt(StrictModel):
    input_fingerprint: str
    diagnostic_fingerprint: str


class FeedbackState(StrictModel):
    repair_attempt_limit: int = Field(default=3, gt=0)
    attempts: list[RepairAttempt] = Field(default_factory=list)


def report_is_current(report: ValidationReport, document_set: DocumentSet) -> bool:
    """UC6: hashes/options of freshly loaded inputs determine whether a report can be reused."""
    return report.input_set_fingerprint == input_fingerprint(document_set) and report.options_fingerprint == options_fingerprint(document_set)


def record_repair_attempt(state: FeedbackState, report: ValidationReport) -> Literal["passed", "retry", "unresolved"]:
    """UC6: count completed edit-and-validation batches, stopping on repetition or limit."""
    semantic = fingerprint([(item.code, item.message, item.primary_location.model_dump(mode="json")) for item in report.diagnostics])
    state.attempts.append(RepairAttempt(input_fingerprint=report.input_set_fingerprint, diagnostic_fingerprint=semantic))
    if report.status == "passed":
        return "passed"
    if len(state.attempts) >= 2 and state.attempts[-1] == state.attempts[-2]:
        return "unresolved"
    return "unresolved" if len(state.attempts) >= state.repair_attempt_limit else "retry"


class ReferenceRewrite(StrictModel):
    before_source: SourceSpan
    after_reference: EntityRef


class ReferenceUpdateResult(StrictModel):
    complete: bool
    diagnostics: list[Diagnostic]


def verify_reference_updates(
    before: DocumentSet, after: DocumentSet, intent: ReferenceUpdateIntent, rewrites: list[ReferenceRewrite],
) -> ReferenceUpdateResult:
    """UC6/R6.4: verify explicit declaration continuity, including reused selectors.

    The preparing agent owns discovery and supplies old/new locations. This check
    certifies only that declared scope; it never guesses a rename or edits Markdown.
    """
    from .diagnostics import diagnostic
    from .parser import parse_document
    from .references import DeclarationIndex, Resolver
    from .reporting import ordered_diagnostics
    from .syntax import SyntaxFailure, reference

    old_index = DeclarationIndex([parse_document(doc, before.options) for doc in before.documents])
    new_index = DeclarationIndex([parse_document(doc, after.options) for doc in after.documents])
    old_resolver, new_resolver = Resolver(old_index, before), Resolver(new_index, after)
    issues: list[Diagnostic] = []

    def issue(code: str, message: str, source: SourceSpan) -> None:
        issues.append(diagnostic(code, message, source, phase="reference"))

    def identity(resolution):
        return resolution.owner, resolution.member_kind, resolution.member_id

    def target_span(resolution, index):
        if resolution.status != "resolved":
            return None
        if resolution.member_id is not None:
            return index.members[identity(resolution)][0]
        return index.owners[resolution.owner].source

    def same_start(first, second) -> bool:
        return first is not None and second is not None and (first.document_id, first.start_offset) == (second.document_id, second.start_offset)

    # State: captured inventory -> verified before-snapshot and scope preconditions.
    expected_snapshots = sorted((doc.document_id, doc.content_sha256, doc.byte_count) for doc in before.documents)
    captured_snapshots = sorted((doc.document_id, doc.content_sha256, doc.byte_count) for doc in intent.before_snapshots)
    location = intent.changes[0].before_location
    if captured_snapshots != expected_snapshots:
        issue("STALE_REFERENCE_INTENT", "Reference intent does not match the supplied before snapshots", location)
    declared_scope = set(intent.reference_search_scope)
    if not intent.discovery_complete or before.failed_inputs or after.failed_inputs or not declared_scope <= set(old_index.documents) or not declared_scope <= set(new_index.documents):
        issue("REFERENCE_UPDATE_INCOMPLETE", "Incoming-reference discovery or its declared document set is incomplete", location)

    # State: explicit old/new selectors -> verified declaration mappings, never positional inference.
    changes = []
    for change in intent.changes:
        old = old_resolver.resolve(change.old_reference)
        new = new_resolver.resolve(change.new_reference)
        if not same_start(target_span(old, old_index), change.before_location) or not same_start(target_span(new, new_index), change.after_location):
            issue("INVALID_DECLARATION_MAPPING", "Selectors must resolve to the explicitly supplied before and after declaration locations", change.before_location)
            continue
        changes.append((old, new))

    # State: captured incoming references -> exact after-text resolution against intended targets.
    for incoming in intent.incoming_references:
        captured = incoming.reference
        old_document = old_index.documents.get(captured.source.document_id)
        if old_document is None or old_document.snapshot.source_text[captured.source.start_offset:captured.source.end_offset] != captured.raw_reference:
            issue("STALE_REFERENCE_INTENT", "Before-reference source span does not match the before snapshot", captured.source)
            continue
        old = old_resolver.resolve(incoming.reference)
        if not same_start(target_span(old, old_index), incoming.target_location):
            issue("INVALID_REFERENCE_INTENT", "Captured target does not match the before reference", incoming.reference.source)
            continue
        candidates = [(old_change, new_change) for old_change, new_change in changes if old_change.owner == old.owner and (old_change.member_id is None or identity(old_change) == identity(old))]
        # A specific member rename takes precedence over its simultaneous owner rename.
        specific = [pair for pair in candidates if pair[0].member_id is not None]
        candidates = specific or candidates
        updates = [rewrite for rewrite in rewrites if rewrite.before_source == incoming.reference.source]
        if len(candidates) != 1 or len(updates) != 1:
            issue("REFERENCE_UPDATE_INCOMPLETE", "Each affected incoming reference needs one declaration mapping and one explicit after reference (including unchanged spellings)", incoming.reference.source)
            continue
        old_change, new_change = candidates[0]
        updated = updates[0].after_reference
        snapshot = new_index.documents.get(updated.source.document_id)
        if snapshot is None or snapshot.snapshot.source_text[updated.source.start_offset:updated.source.end_offset] != updated.raw_reference:
            issue("STALE_REFERENCE_INTENT", "After-reference source span does not match the after snapshot", updated.source)
            continue
        try:
            reparsed = reference(updated.raw_reference, updated.source.start_offset, snapshot.snapshot)
        except SyntaxFailure as error:
            issue("INVALID_REFERENCE_INTENT", str(error), updated.source)
            continue
        actual = new_resolver.resolve(reparsed)
        expected = identity(new_change) if old_change.member_id is not None else (new_change.owner, old.member_kind, old.member_id)
        if actual.status == "resolved" and identity(actual) != expected:
            issue("REFERENCE_TARGET_CHANGED", "After reference resolves to a different declaration than the explicit rename mapping", updated.source)
    issues = ordered_diagnostics(issues + old_resolver.diagnostics + new_resolver.diagnostics)
    return ReferenceUpdateResult(complete=not issues, diagnostics=issues)
