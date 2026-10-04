"""UC4: resolve spelling aliases to snapshot-local declarations and exact members."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

from .diagnostics import diagnostic
from .loading import canonical_document_id
from .models import (
    Diagnostic, DocumentSet, EntityAssembly, EntityKey, EntityRef, InvariantCheckpoint,
    InvariantDerivation, RationaleNote, UnownedRequirementRef, MemberSelector, ParsedDocument,
    RelatedLocation, Requirement, SourceSpan, StrictModel, ValidEntry, WorkflowAnchor,
)
from .syntax import REQUIREMENT_ID, quote_selector


class Resolution(StrictModel):
    status: str
    owner: EntityKey | None = None
    member_kind: str | None = None
    member_id: str | None = None
    source: SourceSpan
    diagnostic_ids: list[str]


class DeclarationIndex:
    """Multi-value aliases preserve duplicates; declaration identity never uses a title."""

    def __init__(self, documents: list[ParsedDocument]):
        self.documents = {document.snapshot.document_id: document for document in documents}
        self.owners: dict[EntityKey, EntityAssembly] = {}
        self.aliases: dict[tuple[str, str, str], list[EntityKey]] = defaultdict(list)
        self.members: dict[tuple[EntityKey, str, str], list[SourceSpan]] = defaultdict(list)
        self.diagnostics: list[Diagnostic] = []
        for document in documents:
            for owner in document.entities:
                self.owners[owner.key] = owner
                match owner.entity_kind:
                    case "use_case":
                        self.aliases[(owner.key.document_id, "use_case_title", owner.title)].append(owner.key)
                        if owner.number:
                            self.aliases[(owner.key.document_id, "use_case_number", owner.number)].append(owner.key)
                    case "story":
                        self.aliases[(owner.key.document_id, "story_id", owner.entity_id)].append(owner.key)
                    case "story_state":
                        self.aliases[(owner.key.document_id, "story_state", owner.entity_id)].append(owner.key)
                for layer in owner.layers:
                    for result in layer.all_entries:
                        if not isinstance(result, ValidEntry):
                            continue
                        entry = result.value
                        match entry:
                            case Requirement():
                                kind, identifier = "requirement", entry.requirement_id
                            case InvariantCheckpoint():
                                kind, identifier = "invariant", entry.invariant_id
                            case InvariantDerivation():
                                kind, identifier = "derivation", entry.derivation_id
                            case RationaleNote(rationale_id=identifier) if identifier is not None:
                                kind = "rationale"
                            case WorkflowAnchor():
                                kind = "step" if entry.anchor_id.startswith("step") else "state"
                                identifier = entry.anchor_id
                            case _:
                                continue
                        self.members[(owner.key, kind, identifier)].append(entry.source)
        # State: collected multi-value aliases -> precise duplicate diagnostics without choosing winners.
        for (_, kind, value), owners in self.aliases.items():
            if len(owners) > 1:
                code = {"use_case_number": "DUPLICATE_USE_CASE_NUMBER", "use_case_title": "DUPLICATE_USE_CASE_TITLE"}.get(kind, "DUPLICATE_ENTITY")
                self.diagnostics.append(diagnostic(
                    code, f"Repeated {kind}: {value}", self.owners[owners[0]].source, phase="model",
                    related=[RelatedLocation(message="Other declaration", location=self.owners[key].source) for key in owners[1:]],
                ))
        for (_, kind, identifier), spans in self.members.items():
            if len(spans) > 1:
                self.diagnostics.append(diagnostic(
                    "DUPLICATE_REQUIREMENT" if kind == "requirement" else "DUPLICATE_ANCHOR" if kind in ("step", "state") else "DUPLICATE_" + kind.upper(),
                    f"Repeated {kind}: {identifier}", spans[0], phase="model",
                    related=[RelatedLocation(message="Other declaration", location=span) for span in spans[1:]],
                ))

    def member_available(self, owner: EntityKey, kind: str) -> bool:
        entity = self.owners[owner]
        if entity.unknown_structure:
            return False
        names = {"invariant": "Invariants", "derivation": "Invariants", "rationale": "Invariants", "step": "Workflow anchors", "state": "Workflow anchors"}
        if kind == "requirement":
            return all(layer.complete for layer in entity.layers)
        return all(layer.complete for layer in entity.layers if layer.name == names[kind])

    def format_owner(self, key: EntityKey) -> str:
        entity = self.owners[key]
        if entity.entity_kind == "story":
            return entity.entity_id
        if entity.number and len(self.aliases[(key.document_id, "use_case_number", entity.number)]) == 1:
            return "UC" + entity.number
        if len(self.aliases[(key.document_id, "use_case_title", entity.title)]) == 1:
            return "use-case " + quote_selector(entity.title, title=True)
        raise ValueError("No unique selector for this owner")

    def format_requirement(self, key: EntityKey, identifier: str, *, from_document: str | None = None) -> str:
        owner = self.format_owner(key)
        if owner.startswith("UC") and REQUIREMENT_ID.fullmatch(identifier):
            result = owner + "/" + identifier
        else:
            if owner.startswith("UC"):
                owner = "use-case " + owner[2:]
            result = owner + "/requirement " + quote_selector(identifier)
        if from_document is not None and key.document_id != from_document:
            import posixpath
            from urllib.parse import quote

            relative = posixpath.relpath(key.document_id, posixpath.dirname(from_document) or ".")
            result = quote(relative, safe="/.-_") + "#" + result
        return result


class Resolver:
    def __init__(self, index: DeclarationIndex, document_set: DocumentSet):
        self.index = index
        self.document_set = document_set
        self.diagnostics: list[Diagnostic] = []
        self.reference_count = 0

    def fail(self, code: str, message: str, source: SourceSpan, *, related: list[SourceSpan] | None = None, causes: list[str] | None = None) -> Resolution:
        item = diagnostic(
            code, message, source, phase="reference", caused_by=causes,
            related=[RelatedLocation(message="Related declaration", location=span) for span in related or []],
        )
        self.diagnostics.append(item)
        return Resolution(status=code.lower(), source=source, diagnostic_ids=[item.diagnostic_id])

    def document_id(self, ref: EntityRef) -> str:
        if ref.document_path is None:
            return ref.source.document_id
        spelling = ref.document_path
        if re.search(r"%(?![0-9a-fA-F]{2})", spelling):
            raise ValueError("Invalid percent escape in reference path")
        if any(char in spelling for char in " \\:"):
            raise ValueError("Use percent-encoded relative Markdown paths with / separators")
        decoded = unquote(spelling, errors="strict")
        path = PurePosixPath(decoded)
        if path.is_absolute() or "\\" in decoded or ":" in decoded or "\x00" in decoded or path.suffix.lower() != ".md":
            raise ValueError("Reference path must be a relative .md file beneath the workspace root")
        root = self.document_set.options.workspace_root.resolve()
        source_directory = root / PurePosixPath(ref.source.document_id).parent
        return canonical_document_id(source_directory / decoded, root)

    def resolve(self, ref: EntityRef, *, owning_entity: EntityKey | None = None, local_owner: EntityKey | None = None) -> Resolution:
        """UC4: resolve document, then selected owner, then optional member."""
        self.reference_count += 1
        if ref.owner_local:
            if local_owner is None or ref.member_selector is None:
                raise ValueError("Owner-local member resolution requires its exact enclosing declaration")
            return self.resolve_member(local_owner, ref.member_selector, ref.source)
        try:
            document_id = self.document_id(ref)
        except (ValueError, OSError, RuntimeError, UnicodeDecodeError) as error:
            return self.fail("INVALID_REFERENCE_PATH", str(error), ref.source)
        if document_id not in self.index.documents:
            return self.fail("MISSING_DOCUMENT", f"Referenced document is not readable in the declared input set: {document_id}", ref.source)
        selected = ref.owner_selector
        keys = self.index.aliases.get((document_id, selected.kind, selected.value), [])
        if len(keys) > 1:
            return self.fail("AMBIGUOUS_REFERENCE", f"Ambiguous {selected.kind}: {selected.value}", ref.source, related=[self.index.owners[key].source for key in keys])
        if not keys:
            document = self.index.documents[document_id]
            if not document.parse_complete:
                return self.fail("TARGET_INVALID", f"Cannot establish missing owner {selected.value} in a damaged document", ref.source, causes=[d.diagnostic_id for d in document.diagnostics if d.severity == "error"])
            return self.fail("MISSING_OWNER", f"No {selected.kind} {selected.value!r} in {document_id}", ref.source)
        owner = keys[0]
        if owning_entity is not None and owner != owning_entity:
            return self.fail("INVALID_SOURCE_OWNER", "Uses source anchor must belong to its declaring entity", ref.source)
        if ref.member_selector is None:
            return Resolution(status="resolved", owner=owner, source=ref.source, diagnostic_ids=[])
        return self.resolve_member(owner, ref.member_selector, ref.source)

    def resolve_member(self, owner: EntityKey, selected: MemberSelector, source: SourceSpan | None = None) -> Resolution:
        source = source or selected.source
        spans = self.index.members.get((owner, selected.kind, selected.value), [])
        if len(spans) > 1:
            return self.fail("AMBIGUOUS_REFERENCE", f"Ambiguous {selected.kind}: {selected.value}", source, related=spans)
        if not spans:
            if not self.index.member_available(owner, selected.kind):
                entity = self.index.owners[owner]
                causes = entity.diagnostic_ids + [cause for layer in entity.layers for cause in layer.diagnostic_ids]
                return self.fail("TARGET_INVALID", f"Cannot establish missing {selected.kind} {selected.value!r} in a damaged owner", source, causes=causes)
            return self.fail("MISSING_MEMBER", f"No {selected.kind} {selected.value!r} in the referenced owner", source, related=[self.index.owners[owner].source])
        return Resolution(status="resolved", owner=owner, member_kind=selected.kind, member_id=selected.value, source=source, diagnostic_ids=[])

    def resolve_unowned(self, ref: UnownedRequirementRef, caller: EntityKey) -> Resolution:
        """Compatibility shorthand is local to a known numbered use-case group."""
        self.reference_count += 1
        entity = self.index.owners[caller]
        if not entity.number:
            return self.fail("AMBIGUOUS_REFERENCE", "Owner-omitted requirement has no known local numbered group", ref.source)
        group = entity.number.split(".")[0]
        candidates = [key for key, owner in self.index.owners.items() if key.document_id == caller.document_id and owner.number and owner.number.split(".")[0] == group and (key, "requirement", ref.requirement_selector.value) in self.index.members]
        if len(candidates) != 1:
            return self.fail("AMBIGUOUS_REFERENCE", "Qualify the owner of this local requirement reference", ref.source, related=[self.index.owners[key].source for key in candidates])
        if not self.index.documents[caller.document_id].parse_complete:
            return self.fail("TARGET_INVALID", "Damaged local group cannot establish unique requirement ownership", ref.source)
        return self.resolve_member(candidates[0], ref.requirement_selector, ref.source)
