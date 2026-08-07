"""Lossless structural inspection for the small math subset Color Math uses."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..utils.latex_helpers import read_braced
from .latex_spans import read_operand
from .markdown_scanner import scan_markdown


COMMAND_RE = re.compile(r"\\[A-Za-z]+|\\.")
NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:')*")
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
OPAQUE_MACROS = frozenset({
    "mathbb",
    "mathbf",
    "mathcal",
    "mathit",
    "mathrm",
    "operatorname",
    "text",
    "textbf",
    "textit",
    "textrm",
    "texttt",
    "verb",
})


@dataclass(frozen=True)
class SemanticSpan:
    """A recognized source range, kept without rewriting its LaTeX."""

    kind: str
    value: str
    start: int
    end: int
    depth: int


@dataclass(frozen=True)
class ParsedMath:
    source: str
    normalized: str
    expression: tuple[SemanticSpan, ...]
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def _read_command(text: str, start: int, end: int) -> tuple[str, int] | None:
    match = COMMAND_RE.match(text, start, end)
    if match is None:
        return None
    return match.group(0), match.end()


def _skip_whitespace(text: str, start: int, end: int) -> int:
    while start < end and text[start].isspace():
        start += 1
    return start


def _skip_comment(text: str, start: int, end: int) -> int:
    index = start + 1
    while index < end and text[index] not in "\r\n":
        index += 1
    if index < end and text[index] == "\r" and index + 1 < end and text[index + 1] == "\n":
        return index + 2
    return min(index + 1, end)


def _read_delimiter(text: str, start: int, end: int) -> tuple[str, int] | None:
    if start >= end:
        return None
    if text[start] != "\\":
        return text[start], start + 1
    return _read_command(text, start, end)


def _skip_opaque_argument(text: str, start: int, end: int) -> int:
    start = _skip_whitespace(text, start, end)
    group = read_braced(text, start)
    return group[1] if group is not None and group[1] <= end else start


def _read_left_right_group(
    text: str,
    start: int,
    end: int,
) -> tuple[str, int, int, int] | None:
    command = _read_command(text, start, end)
    if command is None or command[0] != r"\left":
        return None

    delimiter_data = _read_delimiter(
        text,
        _skip_whitespace(text, command[1], end),
        end,
    )
    if delimiter_data is None:
        return None

    opening, content_start = delimiter_data
    depth = 1
    index = content_start

    while index < end:
        if text[index] == "%":
            index = _skip_comment(text, index, end)
            continue
        if text[index] == "{":
            group = read_braced(text, index)
            if group is None or group[1] > end:
                return None
            index = group[1]
            continue

        if text[index] != "\\":
            index += 1
            continue

        nested_command = _read_command(text, index, end)
        if nested_command is None:
            index += 1
            continue

        name, command_end = nested_command
        if name == r"\left":
            delimiter = _read_delimiter(
                text,
                _skip_whitespace(text, command_end, end),
                end,
            )
            if delimiter is not None:
                depth += 1
                index = delimiter[1]
                continue
        elif name == r"\right":
            delimiter = _read_delimiter(
                text,
                _skip_whitespace(text, command_end, end),
                end,
            )
            if delimiter is not None:
                depth -= 1
                if depth == 0:
                    return opening, content_start, index, delimiter[1]
                index = delimiter[1]
                continue
        else:
            operand = read_operand(text, index, end)
            if operand is not None and operand.kind == "opaque":
                index = operand.end
                continue

        if name[1:] in OPAQUE_MACROS:
            opaque_end = _skip_opaque_argument(text, command_end, end)
            if opaque_end != command_end:
                index = opaque_end
                continue

        index = command_end

    return None


def _read_plain_parentheses(
    text: str,
    start: int,
    end: int,
) -> tuple[int, int, int] | None:
    depth = 1
    index = start + 1

    while index < end:
        if text[index] == "%":
            index = _skip_comment(text, index, end)
            continue
        if text[index] == "{":
            group = read_braced(text, index)
            if group is None or group[1] > end:
                return None
            index = group[1]
            continue

        if text[index] == "\\":
            operand = read_operand(text, index, end)
            if operand is not None and operand.kind == "opaque":
                index = operand.end
                continue
            command = _read_command(text, index, end)
            if command is None:
                index += 1
                continue

            name, command_end = command
            if name == r"\left":
                group = _read_left_right_group(text, index, end)
                if group is not None:
                    index = group[3]
                    continue
            elif name[1:] in OPAQUE_MACROS:
                opaque_end = _skip_opaque_argument(text, command_end, end)
                if opaque_end != command_end:
                    index = opaque_end
                    continue

            index = command_end
            continue

        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return start + 1, index, index + 1

        index += 1

    return None


def _read_function_arguments(
    text: str,
    start: int,
    end: int,
) -> tuple[int, int, int] | None:
    if start >= end:
        return None
    if text[start] == "(":
        return _read_plain_parentheses(text, start, end)

    group = _read_left_right_group(text, start, end)
    if group is None or group[0] not in {"(", r"\("}:
        return None
    return group[1:]


def _collect_semantic_spans(
    text: str,
    start: int,
    end: int,
    depth: int,
    spans: list[SemanticSpan],
    errors: list[str],
) -> None:
    index = start
    while index < end:
        if text[index] == "%":
            index = _skip_comment(text, index, end)
            continue
        if text[index] == "\\":
            operand = read_operand(text, index, end)
            if operand is not None and operand.kind == "opaque":
                index = operand.end
                continue
            command = _read_command(text, index, end)
            if command is not None:
                name, command_end = command
                if name[1:] in OPAQUE_MACROS:
                    opaque_end = _skip_opaque_argument(text, command_end, end)
                    if opaque_end != command_end:
                        index = opaque_end
                        continue
                index = command_end
                continue

        name_match = NAME_RE.match(text, index, end)
        if name_match is not None:
            name_end = name_match.end()
            arguments = _read_function_arguments(text, name_end, end)
            if arguments is not None:
                argument_start, argument_end, call_end = arguments
                spans.append(
                    SemanticSpan(
                        "function",
                        name_match.group(0),
                        index,
                        name_end,
                        depth,
                    )
                )
                _collect_semantic_spans(
                    text,
                    argument_start,
                    argument_end,
                    depth + 1,
                    spans,
                    errors,
                )
                index = call_end
                continue

            if name_end < end and text[name_end] == "(":
                errors.append(f"unclosed function call after {name_match.group(0)!r}")
            index = name_end
            continue

        number_match = NUMBER_RE.match(text, index, end) if depth else None
        if number_match is not None:
            spans.append(
                SemanticSpan(
                    "constant",
                    number_match.group(0),
                    index,
                    number_match.end(),
                    depth,
                )
            )
            index = number_match.end()
            continue

        index += 1


def find_semantic_spans(source: str) -> tuple[tuple[SemanticSpan, ...], str | None]:
    """Recognize plain nested calls and constants without rewriting LaTeX."""
    spans: list[SemanticSpan] = []
    errors: list[str] = []
    _collect_semantic_spans(source, 0, len(source), 0, spans, errors)
    return tuple(spans), errors[0] if errors else None


def format_math_structure(parsed: ParsedMath) -> str:
    if not parsed.expression:
        return "No nested function calls found."
    return "\n".join(
        f"{'  ' * span.depth}{span.kind.title()} {span.value}"
        for span in parsed.expression
    )


def parser_available() -> bool:
    """The built-in structural inspector has no optional dependencies."""
    return True


def parse_math_body(body: str) -> ParsedMath:
    spans, error = find_semantic_spans(body)
    return ParsedMath(body, body, spans, error)


def parse_math_blocks(text: str) -> list[ParsedMath]:
    return [
        parse_math_body(text[span.content_start:span.content_end])
        for span in scan_markdown(text).math_blocks
    ]


def describe_math_blocks(text: str) -> str:
    blocks = parse_math_blocks(text)
    if not blocks:
        return "No $$...$$ math blocks found."

    lines: list[str] = []
    for index, parsed in enumerate(blocks, 1):
        lines.append(f"Block {index}: {'OK' if parsed.ok else 'FAIL'}")
        lines.append(format_math_structure(parsed) if parsed.ok else parsed.error or "unknown parse error")
        lines.append("")

    return "\n".join(lines).rstrip()
