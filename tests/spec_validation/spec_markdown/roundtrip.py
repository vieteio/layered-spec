"""UC9: deterministic preservation, structural round-trip and canonical stability checks."""

from __future__ import annotations

from hashlib import sha256
from typing import Literal

from pydantic import BaseModel, Field, JsonValue

from spec_validation.models import (
    DetailedWorkflowLayer, DocumentSet, DocumentSnapshot, EntityAssembly, EntityKey,
    EntityRef, LayerBase, MarkdownBody, ParsedDocument, RecoveredBlock, StrictModel,
    UnownedRequirementRef, WorkflowChain, StructuredSubsection, WorkflowSubsection, WorkflowProse,
)
from spec_validation.parser import parse_document
from spec_validation.references import DeclarationIndex, Resolver
from .rendering import RenderingError, reconstruct_bytes, reconstruct_markdown, render_fragments, render_markdown


class Difference(StrictModel):
    path: str
    message: str
    expected: JsonValue = None
    actual: JsonValue = None


class RoundTripCheck(StrictModel):
    document_id: str
    check: Literal["preservation", "structural_roundtrip", "canonical_stability"]
    status: Literal["passed", "failed", "blocked"]
    differences: list[Difference] = Field(default_factory=list)


class RoundTripReport(StrictModel):
    checks: list[RoundTripCheck]
    status: Literal["passed", "failed", "incomplete"]


def differences(expected: JsonValue, actual: JsonValue, path: str = "$") -> list[Difference]:
    """Compare every field/item deterministically without sorting semantic lists."""
    found = []
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(expected.keys() | actual.keys()):
            if key not in expected or key not in actual:
                found.append(Difference(path=f"{path}.{key}", message="Field missing on one side", expected=expected.get(key), actual=actual.get(key)))
            else:
                found.extend(differences(expected[key], actual[key], f"{path}.{key}"))
    elif isinstance(expected, list) and isinstance(actual, list):
        for index in range(max(len(expected), len(actual))):
            if index >= len(expected) or index >= len(actual):
                found.append(Difference(path=f"{path}[{index}]", message="Item missing on one side", expected=expected[index] if index < len(expected) else None, actual=actual[index] if index < len(actual) else None))
            else:
                found.extend(differences(expected[index], actual[index], f"{path}[{index}]"))
    elif type(expected) is not type(actual) or expected != actual:
        found.append(Difference(path=path, message="Values differ", expected=expected, actual=actual))
    return found


class Projection:
    def __init__(self, documents: list[ParsedDocument], document_set: DocumentSet, unavailable_documents: set[str] | None = None):
        self.index = DeclarationIndex(documents)
        self.resolver = Resolver(self.index, document_set)
        self.unavailable_documents = unavailable_documents or set()
        self.unavailable_references: set[str] = set()
        self.identities = {
            owner.key: [document.snapshot.document_id, ordinal]
            for document in documents for ordinal, owner in enumerate(document.entities)
        }

    def value(self, value, owner: EntityKey) -> JsonValue:
        # Resolved references compare declaration identities, never spelling or source offsets.
        if isinstance(value, (EntityRef, UnownedRequirementRef)):
            resolved = self.resolver.resolve(value, local_owner=owner) if isinstance(value, EntityRef) else self.resolver.resolve_unowned(value, owner)
            if isinstance(value, EntityRef):
                try:
                    target_document = self.resolver.document_id(value)
                except (ValueError, OSError, RuntimeError, UnicodeDecodeError):
                    # Invalid locators retain lexical identity; ordinary validation owns their errors.
                    target_document = None
                if target_document in self.unavailable_documents:
                    self.unavailable_references.add(target_document)
            if resolved.status == "resolved" and resolved.owner is not None:
                return {"target": self.identities[resolved.owner], "member_kind": resolved.member_kind, "member_id": resolved.member_id}
        if isinstance(value, BaseModel):
            excluded = {"source", "label_source", "key", "declaration_key", "header_spelling", "raw_reference", "spelling", "owner_local", "diagnostic_ids"}
            if isinstance(value, EntityAssembly):
                excluded |= {"value", "workflow_result"}
            if isinstance(value, (LayerBase, WorkflowChain, StructuredSubsection)):
                excluded.add("body")
            if isinstance(value, (DetailedWorkflowLayer, WorkflowSubsection)):
                excluded.add("content")
            result = {name: self.value(getattr(value, name), owner) for name in type(value).model_fields if name not in excluded}
            if isinstance(value, (DetailedWorkflowLayer, WorkflowSubsection)):
                # Compare each serialized owner once; the layer's chains view also includes children.
                result["chains"] = [self.value(chain, owner) for chain in value.content if not isinstance(chain, WorkflowProse)]
            return result
        if isinstance(value, (list, tuple)):
            return [self.value(item, owner) for item in value]
        return value

    def document(self, document: ParsedDocument) -> JsonValue:
        self.unavailable_references.clear()
        return {
            "entities": [self.value(owner, owner.key) for owner in document.entities],
            "verbatim": [piece.markdown for piece in render_fragments(document) if piece.kind == "verbatim"],
        }


def compare_documents(before: list[ParsedDocument], after: list[ParsedDocument], document_set: DocumentSet) -> dict[str, list[Difference]]:
    """UC9: compare the full declared set so cross-file aliases have shared context."""
    left, right = Projection(before, document_set), Projection(after, document_set)
    old = {document.snapshot.document_id: document for document in before}
    new = {document.snapshot.document_id: document for document in after}
    return {
        name: differences(left.document(old[name]), right.document(new[name])) if name in old and name in new
        else [Difference(path="$", message="Document missing on one side")]
        for name in sorted(old.keys() | new.keys())
    }


def source_differences(document: ParsedDocument) -> list[Difference]:
    """Audit retained bodies against their source spans, including nested malformed blocks."""
    found = []
    pending = [("$.blocks", document.blocks), ("$.entities", document.entities)]
    while pending:
        path, value = pending.pop()
        if isinstance(value, (MarkdownBody, RecoveredBlock)):
            span = value.source
            raw = value.markdown if isinstance(value, MarkdownBody) else value.raw_markdown
            if span.document_id != document.snapshot.document_id or not 0 <= span.start_offset <= span.end_offset <= len(document.snapshot.source_text):
                found.append(Difference(path=path, message="Invalid retained source span"))
            else:
                found.extend(differences(document.snapshot.source_text[span.start_offset:span.end_offset], raw, path))
        if isinstance(value, BaseModel):
            excluded = {"value"} if isinstance(value, EntityAssembly) else set()
            pending.extend((f"{path}.{name}", getattr(value, name)) for name in reversed(list(type(value).model_fields)) if name not in excluded)
        elif isinstance(value, (list, tuple)):
            pending.extend((f"{path}[{index}]", value[index]) for index in reversed(range(len(value))))
    return found


def check_roundtrip(document_set: DocumentSet, documents: list[ParsedDocument] | None = None) -> RoundTripReport:
    """UC9: run independent checks, blocking only checks with unavailable prerequisites."""
    documents = documents if documents is not None else [parse_document(snapshot, document_set.options) for snapshot in document_set.documents]
    names = [document.snapshot.document_id for document in documents]
    expected = [snapshot.document_id for snapshot in document_set.documents]
    if len(set(names)) != len(names) or sorted(names) != sorted(expected):
        raise ValueError("Parsed documents must match the declared unique document set")
    checks: list[RoundTripCheck] = []
    generated: dict[str, str] = {}
    reparsed: list[ParsedDocument] = []
    eligible: list[ParsedDocument] = []
    for failed in document_set.failed_inputs:
        for kind in ("preservation", "structural_roundtrip", "canonical_stability"):
            checks.append(RoundTripCheck(document_id=failed.primary_location.document_id, check=kind, status="blocked", differences=[Difference(path="$", message=failed.message)]))
    # Preservation does not depend on structural validity; canonical rendering does.
    for document in documents:
        name = document.snapshot.document_id
        try:
            text = reconstruct_markdown(document)
            encoded = reconstruct_bytes(document)
            found = differences(document.snapshot.source_text, text, "$.source_text")
            found += differences(document.snapshot.content_sha256, sha256(encoded).hexdigest(), "$.content_sha256")
            found += differences(document.snapshot.byte_count, len(encoded), "$.byte_count")
        except RenderingError as error:
            found = [Difference(path="$", message=str(error))]
        found += source_differences(document)
        checks.append(RoundTripCheck(document_id=name, check="preservation", status="failed" if found else "passed", differences=found))
        parsed = None
        try:
            generated[name] = render_markdown(document)
            parsed = parse_document(DocumentSnapshot.from_text(name, generated[name]), document_set.options)
            render_fragments(parsed)  # Establish that reparsed structure is usable for comparison.
        except RenderingError as error:
            status = "failed" if name in generated else "blocked"
            failed_document = parsed if parsed is not None else document
            syntax_errors = [issue for issue in failed_document.diagnostics if issue.severity == "error"]
            found = [Difference(path="$", message=str(error))] + [
                Difference(path=f"$.parse[{index}]", message=f"{issue.code}: {issue.message}", actual=issue.primary_location.model_dump(mode="json"))
                for index, issue in enumerate(syntax_errors)
            ]
            checks.append(RoundTripCheck(document_id=name, check="structural_roundtrip", status=status, differences=found))
            checks.append(RoundTripCheck(document_id=name, check="canonical_stability", status="blocked", differences=[Difference(path="$", message="Canonical reparse is unavailable")]))
            continue
        eligible.append(document)
        reparsed.append(parsed)
    # Missing generated context blocks dependent reference comparisons; never reuse original
    # peers as if they had successfully rendered and reparsed.
    after_names = {document.snapshot.document_id for document in reparsed}
    before_projection = Projection(documents, document_set, set(names) - after_names)
    after_projection = Projection(reparsed, document_set)
    for before, after in zip(eligible, reparsed, strict=True):
        name = before.snapshot.document_id
        found = differences(before_projection.document(before), after_projection.document(after))
        unavailable = sorted(before_projection.unavailable_references)
        if unavailable:
            found.insert(0, Difference(path="$.references", message="Generated reference context is unavailable", actual=unavailable))
        structural_status = "blocked" if unavailable else "failed" if found else "passed"
        checks.append(RoundTripCheck(document_id=name, check="structural_roundtrip", status=structural_status, differences=found))
        try:
            second = render_markdown(after)
            found = differences(generated[name], second, "$.canonical_markdown")
            status = "failed" if found else "passed"
        except RenderingError as error:
            found, status = [Difference(path="$", message=str(error))], "failed"
        checks.append(RoundTripCheck(document_id=name, check="canonical_stability", status=status, differences=found))
    rank = {"preservation": 0, "structural_roundtrip": 1, "canonical_stability": 2}
    checks.sort(key=lambda check: (check.document_id, rank[check.check]))
    status = "failed" if any(c.status == "failed" for c in checks) else "incomplete" if not checks or any(c.status == "blocked" for c in checks) else "passed"
    return RoundTripReport(checks=checks, status=status)
