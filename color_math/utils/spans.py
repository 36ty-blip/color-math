"""Apply source-preserving color wrappers to exact LaTeX ranges."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorSpan:
    """A half-open source range that should receive one color."""

    start: int
    end: int
    color: str
    priority: int = 0


def _crosses(left: ColorSpan, right: ColorSpan) -> bool:
    return (
        left.start < right.start < left.end < right.end
        or right.start < left.start < right.end < left.end
    )


def select_color_spans(source: str, spans: list[ColorSpan]) -> list[ColorSpan]:
    """Keep valid nested/disjoint spans, preferring higher-priority edits."""

    candidates: dict[tuple[int, int], ColorSpan] = {}
    for span in spans:
        if not (0 <= span.start < span.end <= len(source)):
            continue
        key = (span.start, span.end)
        previous = candidates.get(key)
        if previous is None or span.priority > previous.priority:
            candidates[key] = span

    accepted: list[ColorSpan] = []
    for span in sorted(
        candidates.values(),
        key=lambda item: (-item.priority, item.start, -(item.end - item.start)),
    ):
        if any(_crosses(span, other) for other in accepted):
            continue
        accepted.append(span)

    return sorted(accepted, key=lambda item: (item.start, -item.end))


def apply_color_spans(source: str, spans: list[ColorSpan]) -> str:
    """Insert ``\\textcolor`` wrappers without changing the source itself."""

    selected = select_color_spans(source, spans)
    openings: dict[int, list[ColorSpan]] = {}
    closings: dict[int, list[ColorSpan]] = {}
    for span in selected:
        openings.setdefault(span.start, []).append(span)
        closings.setdefault(span.end, []).append(span)

    pieces: list[str] = []
    for index in range(len(source) + 1):
        # Close inner spans first, then open outer spans first.
        for _ in sorted(
            closings.get(index, ()),
            key=lambda item: item.start,
            reverse=True,
        ):
            pieces.append("}")
        for span in sorted(
            openings.get(index, ()),
            key=lambda item: item.end,
            reverse=True,
        ):
            pieces.append(rf"\textcolor{{{span.color}}}{{")
        if index < len(source):
            pieces.append(source[index])

    return "".join(pieces)
