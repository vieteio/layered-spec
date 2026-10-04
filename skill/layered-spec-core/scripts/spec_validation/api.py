"""Library orchestration without application, database, or model-service imports."""

from __future__ import annotations

from time import perf_counter

from .models import DocumentSet, ValidationReport, ValidationResult
from .parser import parse_document
from .reporting import build_report
from .validator import validate_graph


def validate_documents(document_set: DocumentSet, *, include_documents: bool = False) -> ValidationReport | ValidationResult:
    """UC1–UC5: independently parse snapshots, validate references, and return every diagnostic."""
    if not document_set.documents and not document_set.failed_inputs:
        raise ValueError("At least one document or recorded input failure is required")
    identities = [snapshot.document_id for snapshot in document_set.documents]
    if len(set(identities)) != len(identities):
        raise ValueError("DocumentSet snapshots must have distinct canonical identities; use load_document_set for path inputs")
    started = perf_counter()
    documents = [parse_document(snapshot, document_set.options) for snapshot in document_set.documents]
    graph = validate_graph(documents, document_set)
    report = build_report(document_set, documents, graph, (perf_counter() - started) * 1000 + document_set.load_duration_ms)
    return ValidationResult(report=report, documents=documents) if include_documents else report
