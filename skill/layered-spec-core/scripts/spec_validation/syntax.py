"""Located selector grammar; identity resolution is deliberately a separate pass."""

from __future__ import annotations

import re

from .models import DocumentSnapshot, EntityRef, FrozenModel, MemberSelector, OwnerSelector, SourceSpan

NUMBER = r"[1-9]\d*(?:\.[1-9]\d*)*"
REQUIREMENT_ID = re.compile(rf"R{NUMBER}\Z")


class SyntaxFailure(ValueError):
    def __init__(self, message: str, source: SourceSpan):
        super().__init__(message)
        self.source = source


class TextSlice(FrozenModel):
    text: str
    offset: int


def trim(text: str, offset: int) -> TextSlice:
    left = len(text) - len(text.lstrip())
    return TextSlice(text=text.strip(), offset=offset + left)


def unwrap(text: str, offset: int, snapshot: DocumentSnapshot) -> TextSlice:
    selected = trim(text, offset)
    if selected.text.startswith("`"):
        run = len(selected.text) - len(selected.text.lstrip("`"))
        marker = "`" * run
        if len(selected.text) <= 2 * run or not selected.text.endswith(marker):
            raise SyntaxFailure("Unclosed reference code span", snapshot.span(selected.offset, selected.offset + len(selected.text)))
        closing = selected.text.find(marker, run)
        if closing != len(selected.text) - run:
            return selected
        return trim(selected.text[run:-run], selected.offset + run)
    return selected


def split_parts(text: str, delimiter: str, offset: int, snapshot: DocumentSnapshot) -> list[TextSlice]:
    """UC2/UC4: split only outside quoted selectors and Markdown code spans."""
    parts: list[TextSlice] = []
    cursor = beginning = 0
    quoted = False
    while cursor < len(text):
        char = text[cursor]
        if quoted and char == "\\":
            cursor += 2
            continue
        if char == '"':
            quoted = not quoted
            cursor += 1
            continue
        if not quoted and char == "`":
            end_run = cursor
            while end_run < len(text) and text[end_run] == "`":
                end_run += 1
            marker = text[cursor:end_run]
            closing = text.find(marker, end_run)
            if closing < 0:
                raise SyntaxFailure("Unclosed reference code span", snapshot.span(offset + cursor, offset + len(text)))
            cursor = closing + len(marker)
            continue
        if not quoted and text.startswith(delimiter, cursor):
            parts.append(trim(text[beginning:cursor], offset + beginning))
            cursor += len(delimiter)
            beginning = cursor
            continue
        cursor += 1
    if quoted:
        raise SyntaxFailure("Unclosed quoted selector", snapshot.span(offset + beginning, offset + len(text)))
    parts.append(trim(text[beginning:], offset + beginning))
    if any(not part.text for part in parts):
        raise SyntaxFailure(f"Empty component around {delimiter!r}", snapshot.span(offset, offset + len(text)))
    return parts


def selector(text: str, offset: int, snapshot: DocumentSnapshot) -> tuple[str, bool]:
    part = trim(text, offset)
    source = snapshot.span(part.offset, part.offset + len(part.text))
    if not part.text:
        raise SyntaxFailure("Identifier must not be empty", source)
    if part.text.startswith('"'):
        if len(part.text) < 2 or not part.text.endswith('"'):
            raise SyntaxFailure("Unclosed quoted identifier", source)
        raw = part.text[1:-1]
        decoded: list[str] = []
        index = 0
        while index < len(raw):
            char = raw[index]
            if char == "\\":
                if index + 1 >= len(raw) or raw[index + 1] not in ('"', "\\"):
                    raise SyntaxFailure("Quoted identifiers support only escaped quote and backslash", source)
                index += 1
                char = raw[index]
            elif char == '"':
                raise SyntaxFailure("Escape embedded quotes in identifiers", source)
            decoded.append(char)
            index += 1
        value = "".join(decoded).strip()
        if not value:
            raise SyntaxFailure("Identifier must not be empty", source)
        return value, True
    if any(reserved in part.text for reserved in ('/', ',', '#', ':', '->', '`', '"', '\\')):
        raise SyntaxFailure("Quote identifiers containing reserved delimiters", source)
    return part.text, False


def member(text: str, offset: int, snapshot: DocumentSnapshot) -> MemberSelector:
    part = unwrap(text, offset, snapshot)
    source = snapshot.span(part.offset, part.offset + len(part.text))
    if part.text.startswith("requirement "):
        value, _ = selector(part.text[len("requirement "):], part.offset + len("requirement "), snapshot)
        return MemberSelector(kind="requirement", value=value, source=source)
    for prefix, kind in (("R", "requirement"), ("I", "invariant"), ("D", "derivation"), ("N", "rationale")):
        if re.fullmatch(prefix + NUMBER, part.text):
            return MemberSelector(kind=kind, value=part.text, source=source)
    matched = re.fullmatch(r"(step|state)([1-9]\d*)", part.text)
    if matched:
        return MemberSelector(kind=matched[1], value=part.text, source=source)
    raise SyntaxFailure("Expected an identified member, e.g. R4.1 or requirement Configuration requirement", source)


def reference(text: str, offset: int, snapshot: DocumentSnapshot) -> EntityRef:
    original = trim(text, offset)
    selected = unwrap(text, offset, snapshot)
    source = snapshot.span(original.offset, original.offset + len(original.text))
    paths = split_parts(selected.text, "#", selected.offset, snapshot)
    if len(paths) > 2:
        raise SyntaxFailure("A reference has at most one document fragment separator", source)
    document_path = paths[0].text if len(paths) == 2 else None
    owner_and_member = paths[-1]
    parts = split_parts(owner_and_member.text, "/", owner_and_member.offset, snapshot)
    if len(parts) > 2:
        raise SyntaxFailure("Quote slashes inside owner or requirement names", source)
    owner = parts[0]
    anchor_match = re.fullmatch(rf"(UC{NUMBER}|S{NUMBER})\.(step[1-9]\d*|state[1-9]\d*)", owner.text)
    anchor = None
    if anchor_match:
        anchor = member(anchor_match[2], owner.offset + anchor_match.start(2), snapshot)
        owner = TextSlice(text=anchor_match[1], offset=owner.offset)
    owner_source = snapshot.span(owner.offset, owner.offset + len(owner.text))

    # State: raw owner spelling -> explicit number/title/story selector, never an inferred identity.
    compact = re.fullmatch(rf"(UC|S)({NUMBER})", owner.text)
    if compact:
        owner_selector = OwnerSelector(
            kind="use_case_number" if compact[1] == "UC" else "story_id",
            value=compact[2] if compact[1] == "UC" else owner.text, source=owner_source,
        )
        spelling = "compact"
    elif owner.text.startswith("use-case "):
        value, quoted = selector(owner.text[len("use-case "):], owner.offset + len("use-case "), snapshot)
        owner_selector = OwnerSelector(
            kind="use_case_number" if not quoted and re.fullmatch(NUMBER, value) else "use_case_title",
            value=value, source=owner_source,
        )
        spelling = "explicit"
    else:
        raise SyntaxFailure("Expected UC<number>, S<number>, or use-case <number-or-title>", owner_source)
    suffix = member(parts[1].text, parts[1].offset, snapshot) if len(parts) == 2 else anchor
    if anchor is not None and len(parts) == 2:
        raise SyntaxFailure("An anchor reference cannot contain another member", source)
    if suffix is not None and len(parts) == 2:
        suffix_explicit = parts[1].text.startswith("requirement ")
        if suffix_explicit != (spelling == "explicit"):
            spelling = "mixed"
    return EntityRef(
        document_path=document_path, owner_selector=owner_selector, member_selector=suffix,
        spelling=spelling, raw_reference=original.text, source=source,
    )


def quote_selector(value: str, *, title: bool = False) -> str:
    reserved = any(mark in value for mark in ('/', ',', '#', ':', '->', '`', '"', '\\'))
    if reserved or title and re.fullmatch(NUMBER, value):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value
