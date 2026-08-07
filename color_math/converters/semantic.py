"""Small shared helpers for lossless semantic formatters."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..config import COLORS
from ..parsers.latex_spans import find_top_level_tokens
from ..utils.spans import ColorSpan


MATH_BLOCK_RE = re.compile(
    r"^(?P<prefix>\s*(?:\#+\s*)?)\$\$(?P<body>.*)\$\$(?P<suffix>\s*)$",
    re.DOTALL,
)


@dataclass(frozen=True)
class MathBlock:
    prefix: str
    body: str
    suffix: str

    def render(self, colored_body: str) -> str:
        return f"{self.prefix}$${colored_body}$${self.suffix}"


def parse_math_block(source: str) -> MathBlock | None:
    match = MATH_BLOCK_RE.fullmatch(source)
    if match is None:
        return None
    return MathBlock(
        match.group("prefix"),
        match.group("body"),
        match.group("suffix"),
    )


def trim_range(source: str, start: int, end: int) -> tuple[int, int]:
    while start < end and source[start].isspace():
        start += 1
    while end > start and source[end - 1].isspace():
        end -= 1
    return start, end


def first_equality(source: str) -> tuple[int, int] | None:
    matches = find_top_level_tokens(source, ("=",))
    return matches[0][:2] if matches else None


def relation_spans(
    source: str,
    start: int = 0,
    end: int | None = None,
) -> list[ColorSpan]:
    """Color only top-level structural separators."""
    color_by_token = {
        "=": COLORS["relation"],
        "+": COLORS["relation"],
        "-": COLORS["relation"],
        r"\cdot": COLORS["dot"],
        r"\otimes": COLORS["relation"],
        "·": COLORS["dot"],
        "*": COLORS["dot"],
    }
    return [
        ColorSpan(start, end, color_by_token[token], priority=30)
        for start, end, token in find_top_level_tokens(
            source,
            tuple(color_by_token),
            start,
            end,
        )
    ]
