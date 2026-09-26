"""UC4: independent cross-reference, reciprocity, and realization-cycle checks."""

from __future__ import annotations

from collections import defaultdict
from time import perf_counter

from .diagnostics import diagnostic
from .models import (
    CheckResult, Diagnostic, DocumentSet, EntityKey, EntityRef, ForwardRealization,
    InvariantDerivation, RationaleNote, UnownedRequirementRef, MemberSelector, ParsedDocument,
    ReferenceField, RelatedLocation, ReverseRealization, SourceSpan, StrictModel,
    UseMapping, ValidEntry,
)
from .references import DeclarationIndex, Resolution, Resolver


class RealizationEdge(StrictModel):
    source_owner: EntityKey
    requirement_id: str
    target_owner: EntityKey
    target_requirement_id: str | None = None
    direction: str
    source: SourceSpan

    @property
    def reciprocity_key(self) -> tuple[EntityKey, str, EntityKey]:
        return self.source_owner, self.requirement_id, self.target_owner


class GraphResult(StrictModel):
    diagnostics: list[Diagnostic]
    checks: list[CheckResult]
    edges: list[RealizationEdge]
    reference_count: int
    duration_ms: float


def strongly_connected_components(graph: dict[EntityKey, set[EntityKey]]) -> list[list[EntityKey]]:
    """UC4: iterative Kosaraju traversal, linear in nodes and edges."""
    def order(key: EntityKey) -> tuple[str, int]:
        return key.document_id, key.declaration_start_offset

    visited: set[EntityKey] = set()
    finish: list[EntityKey] = []
    reverse: dict[EntityKey, set[EntityKey]] = {key: set() for key in graph}
    for parent, children in graph.items():
        for child in children:
            reverse.setdefault(child, set()).add(parent)
    for root in sorted(graph, key=order):
        stack = [(root, False)]
        while stack:
            node, exiting = stack.pop()
            if exiting:
                finish.append(node)
            elif node not in visited:
                visited.add(node)
                stack.append((node, True))
                stack.extend((child, False) for child in sorted(graph[node], key=order, reverse=True) if child not in visited)
    components = []
    visited.clear()
    for root in reversed(finish):
        if root in visited:
            continue
        component = []
        stack = [root]
        visited.add(root)
        while stack:
            node = stack.pop()
            component.append(node)
            for child in sorted(reverse[node], key=order, reverse=True):
                if child not in visited:
                    visited.add(child)
                    stack.append(child)
        components.append(component)
    return components


def _cycle_path(component: list[EntityKey], graph: dict[EntityKey, set[EntityKey]]) -> list[EntityKey]:
    allowed = set(component)
    trail: list[EntityKey] = []
    active: dict[EntityKey, int] = {}
    visited: set[EntityKey] = set()
    stack = [(component[0], iter(sorted(graph[component[0]], key=lambda key: (key.document_id, key.declaration_start_offset))))]
    trail.append(component[0])
    active[component[0]] = 0
    visited.add(component[0])
    while stack:
        node, children = stack[-1]
        child = next(children, None)
        if child is None:
            stack.pop()
            active.pop(node)
            trail.pop()
        elif child in allowed:
            if child in active:
                return trail[active[child]:] + [child]
            if child not in visited:
                visited.add(child)
                active[child] = len(trail)
                trail.append(child)
                stack.append((child, iter(sorted(graph[child], key=lambda key: (key.document_id, key.declaration_start_offset)))))
    raise RuntimeError("Nontrivial SCC did not contain a cycle")


def validate_graph(documents: list[ParsedDocument], document_set: DocumentSet) -> GraphResult:
    """UC4: normalize exact declarations, then run all independent graph checks."""
    started = perf_counter()
    index = DeclarationIndex(documents)
    resolver = Resolver(index, document_set)
    issues = list(index.diagnostics)
    checks: list[CheckResult] = []
    edges: list[RealizationEdge] = []

    def record_reference(result: Resolution) -> bool:
        passed = result.status == "resolved"
        checks.append(CheckResult(check="reference", scope=result.source, status="passed" if passed else "failed", diagnostic_ids=result.diagnostic_ids))
        return passed

    def block(scope: SourceSpan, causes: list[str], message: str) -> None:
        item = diagnostic("CHECK_BLOCKED", message, scope, phase="graph", caused_by=sorted(set(causes)))
        issues.append(item)
        checks.append(CheckResult(check="realization", scope=scope, status="blocked", diagnostic_ids=[item.diagnostic_id]))

    # State: partial models -> resolved declarations; unrelated failed entries never abort traversal.
    for key, owner in index.owners.items():
        if owner.unknown_structure:
            block(owner.source, owner.diagnostic_ids, "Unknown owner structure blocks complete graph coverage")
        for layer in owner.layers:
            if not layer.complete:
                block(layer.source, layer.diagnostic_ids, f"Invalid {layer.name} entries block complete reference coverage")
            for parsed in layer.all_entries:
                if not isinstance(parsed, ValidEntry):
                    continue
                entry = parsed.value
                match entry:
                    case ForwardRealization():
                        sources = [resolver.resolve_member(key, selected) for selected in entry.source_requirements]
                        targets = [resolver.resolve(ref) for ref in entry.targets]
                        for resolved in sources + targets:
                            record_reference(resolved)
                        for source in sources:
                            for target in targets:
                                if source.status == target.status == "resolved":
                                    edges.append(RealizationEdge(source_owner=key, requirement_id=source.member_id, target_owner=target.owner, target_requirement_id=target.member_id, direction="forward", source=entry.source))
                                else:
                                    block(entry.source, source.diagnostic_ids + target.diagnostic_ids, "Cannot check reciprocity before both endpoints resolve")
                    case ReverseRealization():
                        for ref in entry.sources:
                            resolved = resolver.resolve_unowned(ref, key) if isinstance(ref, UnownedRequirementRef) else resolver.resolve(ref)
                            if record_reference(resolved):
                                edges.append(RealizationEdge(source_owner=resolved.owner, requirement_id=resolved.member_id, target_owner=key, direction="reverse", source=entry.source))
                            else:
                                block(entry.source, resolved.diagnostic_ids, "Cannot check reverse reciprocity before the upstream requirement resolves")
                    case UseMapping():
                        for target in entry.targets:
                            record_reference(resolver.resolve(target))
                        if isinstance(entry.source_selector, EntityRef):
                            record_reference(resolver.resolve(entry.source_selector, owning_entity=key))
                        else:
                            checks.append(CheckResult(check="uses_source_semantics", scope=entry.source, status="not_applicable"))
                    case InvariantDerivation():
                        for ref in entry.source_invariants + entry.target_invariants:
                            record_reference(resolver.resolve(ref, local_owner=key))
                    case RationaleNote():
                        # Typed notes -> independent assessment obligations and derivation resolutions.
                        missing_field = None
                        match entry.assessment:
                            case "qualified" if entry.qualification is None:
                                missing_field = "qualification"
                            case "unsupported" | "rejected" if entry.reason is None:
                                missing_field = "reason"
                        if missing_field:
                            issues.append(diagnostic("RATIONALE_FIELD_REQUIRED", f"{entry.assessment} rationale requires {missing_field}", entry.source, phase="model"))
                        if entry.used_by and entry.rationale_id is None:
                            issues.append(diagnostic("RATIONALE_ID_REQUIRED", "Rationale with used by requires an N identifier", entry.source, phase="model"))
                        if entry.used_by and entry.assessment in {"unsupported", "rejected"}:
                            issues.append(diagnostic("RATIONALE_USAGE_NOT_ALLOWED", f"{entry.assessment} rationale cannot support derivations through used by", entry.source, phase="model"))
                        for ref in entry.used_by:
                            record_reference(resolver.resolve(ref, local_owner=key))
                    case ReferenceField():
                        for ref in entry.references:
                            if isinstance(ref, MemberSelector):
                                record_reference(resolver.resolve_member(key, ref))
                            else:
                                record_reference(resolver.resolve(ref))

    by_direction: dict[str, dict[tuple, list[RealizationEdge]]] = {"forward": defaultdict(list), "reverse": defaultdict(list)}
    unique_edges: dict[tuple, list[RealizationEdge]] = defaultdict(list)
    for edge in edges:
        by_direction[edge.direction][edge.reciprocity_key].append(edge)
        unique_edges[(edge.direction, edge.reciprocity_key, edge.target_requirement_id)].append(edge)
    for occurrences in unique_edges.values():
        if len(occurrences) > 1:
            issues.append(diagnostic(
                "DUPLICATE_REALIZATION", "Repeated realization declaration (including spelling aliases)", occurrences[0].source, phase="graph",
                related=[RelatedLocation(message="Repeated declaration", location=edge.source) for edge in occurrences[1:]],
            ))

    # State: resolved assertions -> eligible reciprocal set differences, never treating damaged layers as empty.
    for direction, known in by_direction.items():
        opposite = "reverse" if direction == "forward" else "forward"
        for relation, declarations in known.items():
            edge = declarations[0]
            if relation in by_direction[opposite]:
                checks.append(CheckResult(check="reciprocity", scope=edge.source, status="passed"))
                continue
            counterpart_key = edge.target_owner if direction == "forward" else edge.source_owner
            counterpart = index.owners[counterpart_key]
            name = "Realizes" if direction == "forward" else "Realized by"
            counterpart_layers = [layer for layer in counterpart.layers if layer.name == name]
            unavailable = counterpart.unknown_structure or len(counterpart_layers) > 1 or any(not layer.complete for layer in counterpart_layers)
            if unavailable:
                causes = counterpart.diagnostic_ids + [cause for layer in counterpart_layers for cause in layer.diagnostic_ids]
                block(edge.source, causes, f"Cannot establish missing {name} in an unavailable counterpart layer")
                continue
            try:
                source_name = index.format_requirement(edge.source_owner, edge.requirement_id, from_document=counterpart_key.document_id)
            except ValueError:
                block(edge.source, [], "The upstream owner has no unique number/title selector; resolve duplicate declarations before adding a counterpart")
                continue
            code = "REALIZATION_REVERSE_MISSING" if direction == "forward" else "REALIZATION_FORWARD_MISSING"
            item = diagnostic(
                code, f"Missing {name} counterpart for {source_name}", edge.source, phase="graph",
                related=[RelatedLocation(message=f"Counterpart owner needs {name}", location=counterpart.source)],
                suggestion="If this relationship is intended, add its counterpart; otherwise correct the original declaration.",
            )
            issues.append(item)
            checks.append(CheckResult(check="reciprocity", scope=edge.source, status="failed", diagnostic_ids=[item.diagnostic_id]))

    graph: dict[EntityKey, set[EntityKey]] = {key: set() for key in index.owners}
    edge_spans: dict[tuple[EntityKey, EntityKey], SourceSpan] = {}
    for edge in edges:
        graph[edge.source_owner].add(edge.target_owner)
        edge_spans[(edge.source_owner, edge.target_owner)] = edge.source
    for source, targets in graph.items():
        if source in targets:
            issues.append(diagnostic("SELF_REALIZATION", "A use case cannot realize its own requirement through a separate mapping", edge_spans[(source, source)], phase="graph"))
    for component in strongly_connected_components(graph):
        if len(component) < 2:
            continue
        cycle = _cycle_path(component, graph)
        spans = [edge_spans[pair] for pair in zip(cycle, cycle[1:])]
        # Titles need not be unique; source locations identify the exact cycle nodes.
        path = " -> ".join(f"{key.document_id}:{index.owners[key].title}" for key in cycle)
        issues.append(diagnostic("REALIZATION_CYCLE", f"Realization cycle: {path}", spans[0], phase="graph", related=[RelatedLocation(message="Cycle edge", location=span) for span in spans[1:]]))
    issues.extend(resolver.diagnostics)
    return GraphResult(diagnostics=issues, checks=checks, edges=edges, reference_count=resolver.reference_count, duration_ms=(perf_counter() - started) * 1000)
