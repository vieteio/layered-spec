"""UC5: deterministic reports and text/JSON output shared by all callers."""

from __future__ import annotations

import json
import os
import tempfile
from hashlib import sha256
from pathlib import Path

from . import __version__
from .models import (
    CheckResult, Diagnostic, DocumentSet, DocumentSummary, InputLocation, ParsedDocument,
    DetailedWorkflowLayer, InvalidWorkflowChain, RecoveredBlock, SnapshotIdentity, SourceSpan,
    ValidationMetrics, ValidationReport,
)
from .validator import GraphResult

EXCLUDED_CHECKS = [
    "Workflow expressions outside main and Detailed Workflow bodies",
    "Workflow execution semantics, type compatibility, and natural-language recursive-call target resolution",
    "Requirement satisfaction and eventual implementation coverage",
    "Proof correctness and execution of fenced/formal code",
    "Anchor/quoted-label correspondence to workflow transitions",
    "Test completeness and equivalence of requirement representations",
    "Recursion termination and incoming references outside the declared input set",
    "Unstructured prose references and native Markdown fragment navigation",
]


def fingerprint(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def options_fingerprint(document_set: DocumentSet) -> str:
    return fingerprint({"options": document_set.options.model_dump(mode="json"), "tool_version": __version__, "report_schema_version": 1})


def input_fingerprint(document_set: DocumentSet) -> str:
    return fingerprint({
        "documents": sorted((d.document_id, d.content_sha256) for d in document_set.documents),
        "inputs": sorted(document_set.input_paths),
        "failed": sorted((d.code, d.primary_location.document_id) for d in document_set.failed_inputs),
    })


def ordered_diagnostics(items: list[Diagnostic]) -> list[Diagnostic]:
    unique: dict[str, Diagnostic] = {}
    for item in items:
        if item.diagnostic_id not in unique:
            unique[item.diagnostic_id] = item.model_copy(deep=True)
        else:
            current = unique[item.diagnostic_id]
            current.caused_by = sorted(set(current.caused_by + item.caused_by))
            known_locations = {r.model_dump_json() for r in current.related_locations}
            for related in item.related_locations:
                if related.model_dump_json() not in known_locations:
                    current.related_locations.append(related)
                    known_locations.add(related.model_dump_json())
    phase_order = {phase: index for index, phase in enumerate(("input", "parse", "model", "reference", "graph", "tool"))}

    def sort_key(item: Diagnostic) -> tuple:
        location = item.primary_location
        offset = location.start_offset if isinstance(location, SourceSpan) else -1
        return location.document_id, offset, phase_order[item.phase], item.code, item.message

    return sorted(unique.values(), key=sort_key)


def build_report(document_set: DocumentSet, documents: list[ParsedDocument], graph: GraphResult, total_ms: float) -> ValidationReport:
    """UC5: accumulate independent phase results and derive explicit completeness."""
    diagnostics = ordered_diagnostics(document_set.failed_inputs + [d for doc in documents for d in doc.diagnostics] + graph.diagnostics)
    checks = list(graph.checks)
    summaries = []
    for document in documents:
        errors = [d.diagnostic_id for d in document.diagnostics if d.severity == "error"]
        checks.append(CheckResult(check="structure", scope=document.snapshot.span(0), status="failed" if errors else "passed", diagnostic_ids=errors))
        summaries.append(DocumentSummary(
            document_id=document.snapshot.document_id, entities=len(document.entities),
            valid_entities=sum(entity.value is not None for entity in document.entities),
            structure_complete=document.parse_complete and all(e.complete for e in document.entities),
            opaque_spans=opaque_spans(document.blocks),
        ))
    blocked = sum(check.status == "blocked" for check in checks)
    complete = not document_set.failed_inputs and all(doc.parse_complete for doc in documents) and blocked == 0
    errors = sum(d.severity == "error" for d in diagnostics)
    workflow_results = []
    for document in documents:
        for entity in document.entities:
            if entity.workflow_result is not None:
                workflow_results.append(entity.workflow_result)
            for layer in entity.layers:
                if isinstance(layer, DetailedWorkflowLayer):
                    workflow_results.extend(layer.chains)
    status = "tool_error" if any(d.phase == "tool" for d in diagnostics) else "failed" if errors else "incomplete" if not complete else "passed"
    return ValidationReport(
        status=status,
        input_snapshots=[SnapshotIdentity(document_id=d.document_id, content_sha256=d.content_sha256, byte_count=d.byte_count) for d in sorted(document_set.documents, key=lambda d: d.document_id)],
        input_set_fingerprint=input_fingerprint(document_set), options_fingerprint=options_fingerprint(document_set),
        documents=sorted(summaries, key=lambda d: d.document_id), diagnostics=diagnostics,
        checks=sorted(checks, key=lambda c: (c.scope.document_id, c.scope.start_offset if isinstance(c.scope, SourceSpan) else -1, c.check, c.status)),
        analysis_complete=complete, excluded_checks=list(EXCLUDED_CHECKS),
        metrics=ValidationMetrics(
            files=len(documents), bytes=sum(d.byte_count for d in document_set.documents), entities=sum(len(d.entities) for d in documents),
            errors=errors, warnings=sum(d.severity == "warning" for d in diagnostics), blocked_checks=blocked,
            references=graph.reference_count, normalized_edges=len(graph.edges),
            workflow_chains=len(workflow_results), invalid_workflow_chains=sum(isinstance(result, InvalidWorkflowChain) for result in workflow_results),
            load_duration_ms=document_set.load_duration_ms, parse_duration_ms=sum(doc.duration_ms for doc in documents),
            graph_duration_ms=graph.duration_ms, total_duration_ms=total_ms,
        ),
    )


def opaque_spans(blocks: list[RecoveredBlock]) -> list[SourceSpan]:
    pending = list(blocks)
    spans = []
    while pending:
        block = pending.pop()
        if block.block_kind == "opaque":
            spans.append(block.source)
        pending.extend(block.children)
    return sorted(spans, key=lambda span: span.start_offset)


def render_text(report: ValidationReport) -> str:
    lines = [f"{report.status.upper()}: {report.metrics.errors} errors, {report.metrics.warnings} warnings, {report.metrics.blocked_checks} blocked checks", f"Ruleset: {report.ruleset}; analysis complete: {report.analysis_complete}"]
    for item in report.diagnostics:
        location = item.primary_location
        label = location.document_id
        if isinstance(location, SourceSpan):
            label += f":{location.start_line}:{location.start_column}"
        lines.append(f"{label}: {item.severity} {item.code}: {item.message}")
        for related in item.related_locations:
            target = related.location
            suffix = f":{target.start_line}:{target.start_column}" if isinstance(target, SourceSpan) else ""
            lines.append(f"  {related.message}: {target.document_id}{suffix}")
        if item.caused_by:
            lines.append("  Blocked by diagnostics: " + ", ".join(item.caused_by))
        if item.suggested_action:
            lines.append("  Suggested action: " + item.suggested_action)
    lines.append("Not checked: " + "; ".join(report.excluded_checks))
    return "\n".join(lines) + "\n"


def write_report(path: Path, report: ValidationReport) -> None:
    """UC5: atomically replace only the explicitly requested report file."""
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
            temporary = stream.name
            stream.write(report.model_dump_json(indent=2))
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)
