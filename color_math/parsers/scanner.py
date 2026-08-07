"""Collect generic, source-preserving LaTeX color spans."""

from __future__ import annotations

import re

from ..config import COLORS, SORTED_COLOR_COMMANDS
from ..utils.coloring import command_color
from ..utils.latex_helpers import read_color_command
from ..utils.spans import ColorSpan, apply_color_spans
from .latex_spans import find_all_operator_spans, find_script_argument_spans, read_operand


COMMAND_RE = re.compile(r"\\[A-Za-z]+|\\.")


def collect_operator_spans(
    body: str,
    start: int = 0,
    end: int | None = None,
) -> list[ColorSpan]:
    """Color complete operators, including attached limits and scripts."""
    spans: list[ColorSpan] = []
    for operator in find_all_operator_spans(body, start, end):
        command = COMMAND_RE.match(body, operator.start, operator.end)
        if command is not None:
            spans.append(
                ColorSpan(
                    operator.start,
                    operator.end,
                    command_color(command.group(0)),
                    priority=30,
                )
            )
    return spans


def collect_scanner_spans(body: str) -> list[ColorSpan]:
    """Find generic operators and script arguments without rewriting LaTeX."""
    scripts = find_script_argument_spans(body)
    operators = find_all_operator_spans(body)
    spans = [
        ColorSpan(
            item.start,
            item.end,
            COLORS["chain" if item.kind == "subscript" else "upper"],
            priority=10,
        )
        for item in scripts
    ]
    spans.extend(collect_operator_spans(body))
    script_ranges = tuple((item.start, item.end) for item in scripts)
    operator_ranges = tuple((item.start, item.end) for item in operators)

    index = 0
    while index < len(body):
        if body[index] == "%":
            line_end = index + 1
            while line_end < len(body) and body[line_end] not in "\r\n":
                line_end += 1
            if (
                line_end < len(body)
                and body[line_end] == "\r"
                and line_end + 1 < len(body)
                and body[line_end + 1] == "\n"
            ):
                line_end += 2
            elif line_end < len(body):
                line_end += 1
            index = line_end
            continue

        existing = read_color_command(body, index)
        if existing is not None:
            index = existing[1]
            continue

        operand = read_operand(body, index)
        if operand is not None and operand.kind == "opaque":
            index = operand.end
            continue

        containing_operator = next(
            (
                (start, end)
                for start, end in operator_ranges
                if start <= index < end
            ),
            None,
        )
        if containing_operator is not None:
            index = containing_operator[1]
            continue

        containing_script = next(
            (
                (start, end)
                for start, end in script_ranges
                if start <= index < end
            ),
            None,
        )
        if containing_script is not None:
            index = containing_script[1]
            continue

        command_match = COMMAND_RE.match(body, index)
        if command_match is not None:
            command = command_match.group(0)
            if command in SORTED_COLOR_COMMANDS:
                spans.append(
                    ColorSpan(
                        index,
                        command_match.end(),
                        command_color(command),
                    )
                )
            index = command_match.end()
            if index < len(body) and body[index] == "*":
                index += 1
            continue

        command = next(
            (
                candidate
                for candidate in SORTED_COLOR_COMMANDS
                if not candidate.startswith("\\")
                and body.startswith(candidate, index)
            ),
            None,
        )
        if command is not None:
            spans.append(
                ColorSpan(index, index + len(command), command_color(command))
            )
            index += len(command)
            continue

        index += 1

    return spans


def color_latex_body_with_scanner(body: str) -> str:
    """Color generic LaTeX tokens by inserting scoped wrappers."""
    return apply_color_spans(body, collect_scanner_spans(body))
