"""Shared plain-label grammar and registered layer names."""

from __future__ import annotations

import re

from .syntax import NUMBER

STANDARD_LAYERS = (
    "Execution Logic", "Implementation Logic", "Implementation Logic Proposal", "Implementation Plan",
    "Events And Endpoints", "Files And Functions", "Types", "Tables", "Data", "Detailed Workflow",
    "Invariants", "Logic", "Logic Details", "Observed Existing Logic", "Input Validation And Contracts",
    "Tests", "Validation", "Use Case Questions", "Requirements", "Realized by", "Realizes", "Uses",
    "Requirement representations", "Description", "UI", "User expectations", "E2E tests", "Workflow anchors",
)
LAYER_NAMES = {name.casefold(): name for name in STANDARD_LAYERS}
INVARIANT_SECTIONS = ("Outline", "Rationale", "Definitions", "State invariants", "Derivations")


def canonical_layer_name(name: str) -> str | None:
    if name.startswith("Extension/") and name.removeprefix("Extension/").strip():
        return name
    return LAYER_NAMES.get(name.strip().casefold())


# Source indentation stays intact: malformed R markers are entry recovery points,
# while only standalone column-zero labels can become outer layer candidates.
CONVENTIONAL_REQUIREMENT = re.compile(rf"^[ \t]*(R{NUMBER})(?:[ \t]+([A-Za-z][A-Za-z0-9_-]*))?:[ \t]*(.*)$")


def layer_candidate(line: str) -> str | None:
    if line.startswith("Requirement:") or CONVENTIONAL_REQUIREMENT.fullmatch(line):
        return None
    matched = re.fullmatch(r"([^:\r\n]+):[ \t]*", line)
    if matched is None:
        return None
    name = matched[1]
    if name[0].isspace():
        return None
    return name if name[0].isupper() or canonical_layer_name(name) is not None else None
