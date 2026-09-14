"""Located, deterministic diagnostics shared by independent validation passes."""

from __future__ import annotations

from hashlib import sha256

from .models import Diagnostic, InputLocation, RelatedLocation, SourceSpan


def diagnostic(
    code: str, message: str, location: SourceSpan | InputLocation,
    *, phase: str = "parse", severity: str = "error", related: list[RelatedLocation] | None = None,
    caused_by: list[str] | None = None, suggestion: str | None = None,
    precision: str | None = None,
) -> Diagnostic:
    identity = f"{phase}|{code}|{location.model_dump_json()}|{message}"
    return Diagnostic(
        diagnostic_id=sha256(identity.encode()).hexdigest()[:20], code=code,
        message=message, primary_location=location, phase=phase, severity=severity,
        related_locations=related or [], caused_by=caused_by or [], suggested_action=suggestion,
        location_precision=precision or ("input" if isinstance(location, InputLocation) else "token"),
    )
