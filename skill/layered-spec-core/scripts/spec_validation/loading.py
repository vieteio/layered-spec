"""UC1: bounded filesystem input to immutable document snapshots."""

from __future__ import annotations

import os
from hashlib import sha256
from pathlib import Path
from time import perf_counter

from .diagnostics import diagnostic
from .models import DocumentSet, DocumentSnapshot, InputLocation, RelatedLocation, ValidationOptions


def canonical_document_id(path: Path, root: Path) -> str:
    relative = path.resolve().relative_to(root.resolve())
    return os.path.normcase(relative.as_posix()).replace("\\", "/")


def load_document_set(paths: list[str | Path], options: ValidationOptions) -> DocumentSet:
    """UC1: load every declared input independently, preserving expected failures."""
    started = perf_counter()
    root = options.workspace_root.resolve()
    if not root.is_dir():
        raise ValueError("workspace_root must be an existing directory")
    if not paths:
        raise ValueError("at least one planning document is required")
    result = DocumentSet(documents=[], options=options, input_paths=[str(p) for p in paths])
    seen: dict[str, InputLocation] = {}
    consumed = 0

    # State: raw requested paths -> canonical identities and independent bounded snapshots.
    for ordinal, requested in enumerate(paths):
        location = InputLocation(document_id=str(requested), input_ordinal=ordinal)
        try:
            candidate = Path(requested)
            path = (candidate if candidate.is_absolute() else root / candidate).resolve()
            document_id = canonical_document_id(path, root)
            if path.suffix.lower() != ".md":
                raise ValueError("planning inputs must be .md files")
        except (ValueError, OSError, RuntimeError) as error:
            result.failed_inputs.append(diagnostic("INVALID_REFERENCE_PATH", str(error), location, phase="input"))
            continue
        if document_id in seen:
            result.failed_inputs.append(diagnostic(
                "DUPLICATE_DOCUMENT", f"Duplicate input identity: {document_id}", location, phase="input",
                related=[RelatedLocation(message="First input", location=seen[document_id])],
            ))
            continue
        seen[document_id] = location
        try:
            allowance = min(options.max_file_bytes, max(0, options.max_total_bytes - consumed))
            with path.open("rb") as stream:
                contents = stream.read(allowance + 1)
            consumed += len(contents)
            if len(contents) > allowance:
                result.failed_inputs.append(diagnostic(
                    "INPUT_LIMIT_EXCEEDED", f"Input exceeds file/remaining total byte limit ({allowance} bytes): {document_id}",
                    location, phase="input",
                ))
                continue
            source = contents.decode("utf-8-sig")
        except UnicodeDecodeError:
            result.failed_inputs.append(diagnostic("INVALID_ENCODING", f"Input is not UTF-8: {document_id}", location, phase="input"))
            continue
        except OSError as error:
            result.failed_inputs.append(diagnostic("INPUT_UNREADABLE", f"Cannot read {document_id}: {error.strerror}", location, phase="input"))
            continue
        snapshot = DocumentSnapshot.from_text(document_id, source).model_copy(update={
            "utf8_bom": contents.startswith(b"\xef\xbb\xbf"),
            "display_path": str(requested), "content_sha256": sha256(contents).hexdigest(),
            "byte_count": len(contents), "input_ordinal": ordinal,
        })
        result.documents.append(snapshot)
    result.load_duration_ms = (perf_counter() - started) * 1000
    return result
