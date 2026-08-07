"""Locate protected Markdown and display-math spans without rewriting text."""

from __future__ import annotations

from dataclasses import dataclass


FENCED_CODE = "fenced_code"
CODE_SPAN = "code_span"
MATH_BLOCK = "math_block"


@dataclass(frozen=True, slots=True)
class MarkdownSpan:
    """Half-open source offsets for a delimited Markdown region."""

    kind: str
    start: int
    content_start: int
    content_end: int
    end: int


@dataclass(frozen=True, slots=True)
class MarkdownScan:
    """Protected code regions and editable ``$$...$$`` regions."""

    protected: tuple[MarkdownSpan, ...]
    math_blocks: tuple[MarkdownSpan, ...]


@dataclass(frozen=True, slots=True)
class _ListItem:
    marker_indent: int
    content_indent: int


@dataclass(frozen=True, slots=True)
class _FenceContainer:
    quote_depth: int
    list_indent: int


def _line_ranges(text: str) -> list[tuple[int, int, int]]:
    """Return ``(start, content_end, line_end)`` without normalizing endings."""
    ranges: list[tuple[int, int, int]] = []
    start = 0

    while start < len(text):
        content_end = start
        while content_end < len(text) and text[content_end] not in "\r\n":
            content_end += 1

        line_end = content_end
        if line_end < len(text):
            if (
                text[line_end] == "\r"
                and line_end + 1 < len(text)
                and text[line_end + 1] == "\n"
            ):
                line_end += 2
            else:
                line_end += 1

        ranges.append((start, content_end, line_end))
        start = line_end

    return ranges


def _opening_fence(line: str) -> tuple[str, int] | None:
    index = 0
    while index < len(line) and index < 3 and line[index] == " ":
        index += 1

    if index >= len(line) or line[index] not in "`~":
        return None

    marker = line[index]
    marker_end = index
    while marker_end < len(line) and line[marker_end] == marker:
        marker_end += 1

    length = marker_end - index
    if length < 3:
        return None

    info = line[marker_end:]
    if marker == "`" and "`" in info:
        return None

    return marker, length


def _is_closing_fence(line: str, marker: str, minimum: int) -> bool:
    index = 0
    while index < len(line) and index < 3 and line[index] == " ":
        index += 1

    marker_end = index
    while marker_end < len(line) and line[marker_end] == marker:
        marker_end += 1

    return (
        marker_end - index >= minimum
        and all(char in " \t" for char in line[marker_end:])
    )


def _strip_blockquotes(line: str) -> tuple[int, int]:
    """Return the number of leading quote containers and their source end."""
    depth = 0
    index = 0

    while True:
        marker = index
        spaces = 0
        while marker < len(line) and spaces < 3 and line[marker] == " ":
            marker += 1
            spaces += 1
        if marker >= len(line) or line[marker] != ">":
            return depth, index

        index = marker + 1
        if index < len(line) and line[index] in " \t":
            index += 1
        depth += 1


def _strip_required_blockquotes(line: str, depth: int) -> int | None:
    index = 0
    for _ in range(depth):
        marker = index
        spaces = 0
        while marker < len(line) and spaces < 3 and line[marker] == " ":
            marker += 1
            spaces += 1
        if marker >= len(line) or line[marker] != ">":
            return None

        index = marker + 1
        if index < len(line) and line[index] in " \t":
            index += 1
    return index


def _read_list_marker(line: str, start: int) -> int | None:
    """Return a list item's content indent, or ``None`` for plain text."""
    if start >= len(line):
        return None

    marker_end = start
    if line[start] in "-+*":
        marker_end += 1
    elif line[start].isdigit():
        while marker_end < len(line) and line[marker_end].isdigit():
            marker_end += 1
        if marker_end - start > 9 or marker_end >= len(line):
            return None
        if line[marker_end] not in ".)":
            return None
        marker_end += 1
    else:
        return None

    if marker_end == len(line):
        return marker_end + 1
    if line[marker_end] != " ":
        return None

    whitespace_end = marker_end
    while whitespace_end < len(line) and line[whitespace_end] == " ":
        whitespace_end += 1
    padding = whitespace_end - marker_end
    return marker_end + (padding if padding <= 4 else 1)


def _list_parent_count(
    stack: list[_ListItem],
    marker_indent: int,
) -> int | None:
    for level in range(len(stack) - 1, -1, -1):
        item = stack[level]
        if marker_indent == item.marker_indent:
            return level
        if item.content_indent <= marker_indent <= item.content_indent + 3:
            return level + 1
    return 0 if marker_indent <= 3 else None


def _list_content_start(line: str, stack: list[_ListItem]) -> int:
    """Strip active list indentation and update the list-container stack."""
    cursor = 0
    parsed_marker = False

    while cursor < len(line):
        marker = cursor
        while marker < len(line) and line[marker] == " ":
            marker += 1

        content_indent = _read_list_marker(line, marker)
        if content_indent is None:
            break

        parent_count = _list_parent_count(stack, marker)
        if parent_count is None:
            break

        stack[:] = stack[:parent_count]
        stack.append(_ListItem(marker, content_indent))
        cursor = min(content_indent, len(line))
        parsed_marker = True

    if parsed_marker:
        return stack[-1].content_indent

    if not line.strip(" \t"):
        return stack[-1].content_indent if stack else 0

    indentation = 0
    while indentation < len(line) and line[indentation] == " ":
        indentation += 1

    for level in range(len(stack) - 1, -1, -1):
        if indentation >= stack[level].content_indent:
            stack[:] = stack[:level + 1]
            return stack[-1].content_indent

    stack.clear()
    return 0


def _opening_container(
    line: str,
    list_stacks: dict[int, list[_ListItem]],
) -> tuple[_FenceContainer, int]:
    # ponytail: space-indented lists and quote-first containers cover the
    # current Obsidian scope; use a CommonMark parser if tab-expanded or
    # list-before-quote nesting becomes necessary.
    quote_depth, quote_end = _strip_blockquotes(line)
    for depth in tuple(list_stacks):
        if depth > quote_depth:
            del list_stacks[depth]

    list_stack = list_stacks.setdefault(quote_depth, [])
    list_indent = _list_content_start(line[quote_end:], list_stack)
    return (
        _FenceContainer(quote_depth, list_indent),
        min(quote_end + list_indent, len(line)),
    )


def _continuation_start(
    line: str,
    container: _FenceContainer,
) -> int | None:
    quote_end = _strip_required_blockquotes(line, container.quote_depth)
    if quote_end is None:
        return None

    remainder = line[quote_end:]
    if not remainder.strip(" \t"):
        return len(line)
    if container.list_indent and not remainder.startswith(
        " " * container.list_indent
    ):
        return None
    return quote_end + container.list_indent


def _find_fenced_code(text: str) -> tuple[MarkdownSpan, ...]:
    lines = _line_ranges(text)
    spans: list[MarkdownSpan] = []
    list_stacks: dict[int, list[_ListItem]] = {}
    line_index = 0

    while line_index < len(lines):
        start, content_end, line_end = lines[line_index]
        line = text[start:content_end]
        container, container_end = _opening_container(line, list_stacks)
        opening = _opening_fence(line[container_end:])
        if opening is None:
            line_index += 1
            continue

        marker, minimum = opening
        closing_index = line_index + 1
        while closing_index < len(lines):
            close_start, close_content_end, close_line_end = lines[closing_index]
            close_line = text[close_start:close_content_end]
            close_container_end = _continuation_start(close_line, container)
            if close_container_end is None:
                spans.append(
                    MarkdownSpan(
                        FENCED_CODE,
                        start,
                        line_end,
                        close_start,
                        close_start,
                    )
                )
                line_index = closing_index
                break
            if _is_closing_fence(
                close_line[close_container_end:],
                marker,
                minimum,
            ):
                spans.append(
                    MarkdownSpan(
                        FENCED_CODE,
                        start,
                        line_end,
                        close_start,
                        close_line_end,
                    )
                )
                line_index = closing_index + 1
                break
            closing_index += 1
        else:
            spans.append(
                MarkdownSpan(
                    FENCED_CODE,
                    start,
                    line_end,
                    len(text),
                    len(text),
                )
            )
            line_index = len(lines)

    return tuple(spans)


def _visible_ranges(
    length: int,
    excluded: tuple[MarkdownSpan, ...],
) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    index = 0

    for span in excluded:
        if index < span.start:
            ranges.append((index, span.start))
        index = max(index, span.end)

    if index < length:
        ranges.append((index, length))

    return ranges


def _is_escaped(text: str, index: int, lower_bound: int) -> bool:
    backslashes = 0
    index -= 1
    while index >= lower_bound and text[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def _delimiter_runs(
    text: str,
    start: int,
    end: int,
    delimiter: str,
) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    index = start

    while index < end:
        run_start = text.find(delimiter, index, end)
        if run_start < 0:
            break

        run_end = run_start + 1
        while run_end < end and text[run_end] == delimiter:
            run_end += 1

        if not _is_escaped(text, run_start, start):
            runs.append((run_start, run_end))
        index = run_end

    return runs


def _pair_runs(
    runs: list[tuple[int, int]],
    kind: str,
    exact_length: int | None = None,
) -> list[MarkdownSpan]:
    if exact_length is not None:
        runs = [run for run in runs if run[1] - run[0] == exact_length]

    next_same: list[int | None] = [None] * len(runs)
    nearest: dict[int, int] = {}
    for index in range(len(runs) - 1, -1, -1):
        length = runs[index][1] - runs[index][0]
        next_same[index] = nearest.get(length)
        nearest[length] = index

    spans: list[MarkdownSpan] = []
    index = 0
    while index < len(runs):
        closing_index = next_same[index]
        if closing_index is None:
            index += 1
            continue

        opening = runs[index]
        closing = runs[closing_index]
        spans.append(
            MarkdownSpan(
                kind,
                opening[0],
                opening[1],
                closing[0],
                closing[1],
            )
        )
        index = closing_index + 1

    return spans


def _find_code_spans(
    text: str,
    fenced: tuple[MarkdownSpan, ...],
) -> tuple[MarkdownSpan, ...]:
    spans: list[MarkdownSpan] = []
    for start, end in _visible_ranges(len(text), fenced):
        spans.extend(
            _pair_runs(
                _delimiter_runs(text, start, end, "`"),
                CODE_SPAN,
            )
        )
    return tuple(spans)


def _find_math_blocks(
    text: str,
    protected: tuple[MarkdownSpan, ...],
) -> tuple[MarkdownSpan, ...]:
    spans: list[MarkdownSpan] = []
    for start, end in _visible_ranges(len(text), protected):
        spans.extend(
            _pair_runs(
                _delimiter_runs(text, start, end, "$"),
                MATH_BLOCK,
                exact_length=2,
            )
        )
    return tuple(spans)


def scan_markdown(text: str) -> MarkdownScan:
    """Return exact protected and display-math offsets in ``text``."""
    fenced = _find_fenced_code(text)
    code_spans = _find_code_spans(text, fenced)
    protected = tuple(sorted((*fenced, *code_spans), key=lambda span: span.start))
    return MarkdownScan(protected, _find_math_blocks(text, protected))
