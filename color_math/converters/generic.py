"""Generic source-preserving LaTeX coloring."""

from __future__ import annotations

import re

from ..config import COLORS
from ..parsers.math_parser import find_semantic_spans
from ..parsers.scanner import collect_scanner_spans
from ..utils.latex_helpers import contains_color_wrapper
from ..utils.spans import ColorSpan, apply_color_spans


MATH_LINE_RE = re.compile(
    r"^(?P<prefix>\s*\#+\s*)?\$\$(?P<body>.*)\$\$(?P<suffix>\s*)$"
)
FUNCTION_COLOR_NAMES = ("main", "derivative", "chain")


def collect_function_spans(body: str) -> list[ColorSpan]:
    """Color nested call names and recognize literal constants."""
    semantic, _ = find_semantic_spans(body)
    spans: list[ColorSpan] = []
    for item in semantic:
        if item.kind == "function":
            color_name = FUNCTION_COLOR_NAMES[min(item.depth, 2)]
        elif item.kind == "constant":
            color_name = "orange"
        else:
            continue
        spans.append(
            ColorSpan(item.start, item.end, COLORS[color_name], priority=20)
        )
    return spans


def color_latex_body(body: str) -> str:
    """Insert scoped colors while preserving every original source character."""
    if contains_color_wrapper(body):
        return body
    return apply_color_spans(
        body,
        [*collect_function_spans(body), *collect_scanner_spans(body)],
    )


def color_generic_math_line(line: str) -> str:
    """Convert a single-line ``$$...$$`` math block."""
    match = MATH_LINE_RE.match(line)
    if match is None:
        return line
    prefix = match.group("prefix") or ""
    suffix = match.group("suffix")
    return f"{prefix}$${color_latex_body(match.group('body'))}$${suffix}"
