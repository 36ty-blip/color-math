"""Lossless semantic coloring for chain-rule derivatives."""

from __future__ import annotations

import re

from ..config import COLORS
from ..parsers.latex_spans import (
    find_operand_spans,
    read_command,
    read_group_end,
    read_operand,
    skip_ignorable,
)
from ..parsers.scanner import collect_operator_spans
from ..utils.latex_helpers import contains_color_wrapper
from ..utils.spans import ColorSpan, apply_color_spans
from .semantic import first_equality, parse_math_block, relation_spans, trim_range


NUMERIC_FRACTION_RE = re.compile(
    r"\\(?:dfrac|tfrac|frac)\{[+-]?\d+(?:\.\d+)?\}"
    r"\{[+-]?\d+(?:\.\d+)?\}"
)
PLAIN_COEFFICIENT_RE = re.compile(r"[A-Za-z]")
ADDITIVE_SEPARATOR_RE = re.compile(
    r"[+\-=<>]|\\(?:pm|mp|leq|geq|neq|approx|sim|equiv)(?![A-Za-z])"
)
MULTIPLICATIVE_GAP_RE = re.compile(
    r"(?:\s|[·*]|\\(?:cdot|times|,|:|;|!|quad|qquad)(?![A-Za-z]))*"
)


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def _is_derivative_prefix(value: str) -> bool:
    compact = _compact(value)
    return compact.startswith(
        (r"\frac{d}{d", r"\dfrac{d}{d", r"\tfrac{d}{d")
    )


def _is_prime(value: str) -> bool:
    return bool(re.match(r"(?:[A-Za-z]|\\[A-Za-z]+)'", value.lstrip()))


def _is_numeric(value: str) -> bool:
    compact = _compact(value)
    return bool(
        re.fullmatch(r"[+-]?\d+(?:\.\d+)?", compact)
        or NUMERIC_FRACTION_RE.fullmatch(compact)
    )


def _is_outer_derivative(value: str) -> bool:
    compact = _compact(value)
    return (
        compact.startswith(
            (
                r"\cos",
                r"\sin",
                r"\tan",
                r"\sec",
                r"\ln",
                r"\log",
                r"\sqrt",
                r"\frac",
                r"\dfrac",
                r"\tfrac",
                "e^",
            )
        )
        or _is_prime(compact)
    )


def _has_additive_separator(value: str) -> bool:
    return ADDITIVE_SEPARATOR_RE.search(value) is not None


def _is_multiplicative_gap(value: str) -> bool:
    return MULTIPLICATIVE_GAP_RE.fullmatch(value) is not None


def _fraction_arguments(
    body: str,
    operand_start: int,
    end: int,
) -> tuple[tuple[int, int], ...]:
    command = read_command(body, operand_start, end)
    if command is None or command[0] not in {"frac", "dfrac", "tfrac"}:
        return ()
    ranges: list[tuple[int, int]] = []
    index = command[1]
    for _ in range(2):
        index = skip_ignorable(body, index, end)
        group_end = read_group_end(body, index, end)
        if group_end is None:
            return ()
        ranges.append((index + 1, group_end - 1))
        index = group_end
    return tuple(ranges)


def _rhs_spans(body: str, start: int, end: int | None = None) -> list[ColorSpan]:
    end = len(body) if end is None else end
    operands = list(find_operand_spans(body, start, end))
    spans: list[ColorSpan] = []
    prime_seen = False
    previous_end = start

    for index, operand in enumerate(operands):
        if _has_additive_separator(body[previous_end:operand.start]):
            prime_seen = False
        value = body[operand.start:operand.end]
        compact = _compact(value)
        next_exists = index + 1 < len(operands)

        multiplicative_gap = (
            body[operand.end:operands[index + 1].start]
            if next_exists
            else ""
        )
        is_coefficient = _is_numeric(value) or (
            next_exists
            and PLAIN_COEFFICIENT_RE.fullmatch(compact) is not None
            and _is_multiplicative_gap(multiplicative_gap)
        )
        if is_coefficient:
            color_name = "orange"
        elif _is_prime(value):
            color_name = "chain" if prime_seen else "derivative"
            prime_seen = True
        elif prime_seen:
            color_name = "chain" if operand.kind == "symbol" else "main"
        else:
            color_name = "derivative" if _is_outer_derivative(value) else "main"

        span_start = operand.start
        if _is_numeric(value):
            sign = operand.start - 1
            while sign >= start and body[sign].isspace():
                sign -= 1
            if sign >= start and body[sign] in "+-":
                before = sign - 1
                while before >= start and body[before].isspace():
                    before -= 1
                if before < start or body[before] in "=+-(":
                    span_start = sign

        primed_name = re.match(r"[A-Za-z]+['’]+", value)
        product_group: tuple[int, int] | None = None
        if primed_name is not None:
            group_start = skip_ignorable(
                body,
                operand.start + primed_name.end(),
                operand.end,
            )
            group_end = read_group_end(body, group_start, operand.end)
            if (
                group_end is not None
                and any(token in body[group_start + 1:group_end - 1] for token in "+-")
            ):
                product_group = (group_start, operand.end)

        if product_group is None:
            spans.append(
                ColorSpan(
                    span_start,
                    operand.end,
                    COLORS[color_name],
                    priority=20,
                )
            )
        else:
            spans.extend(
                (
                    ColorSpan(
                        span_start,
                        operand.start + primed_name.end(),
                        COLORS[color_name],
                        priority=20,
                    ),
                    ColorSpan(
                        product_group[0],
                        product_group[1],
                        COLORS["main"],
                        priority=20,
                    ),
                )
            )

        if (
            not _is_numeric(value)
            and value.lstrip().startswith((r"\frac", r"\dfrac", r"\tfrac"))
        ):
            for inner_start, inner_end in _fraction_arguments(
                body,
                operand.start,
                operand.end,
            ):
                inner_semantic = _rhs_spans(body, inner_start, inner_end)
                inner_relations = relation_spans(body, inner_start, inner_end)
                spans.extend(
                    relation
                    for relation in inner_relations
                    if not any(
                        semantic.start <= relation.start
                        and relation.end <= semantic.end
                        for semantic in inner_semantic
                    )
                )
                spans.extend(inner_semantic)

        previous_end = operand.end

    return spans


def convert_derivative_line(source: str) -> str | None:
    """Color a derivative block by inserting wrappers into its exact source."""
    block = parse_math_block(source)
    if block is None:
        return None
    if contains_color_wrapper(block.body):
        return source

    body_start = skip_ignorable(block.body, 0, len(block.body))
    prefix = read_operand(block.body, body_start)
    if prefix is None or not _is_derivative_prefix(prefix.text(block.body)):
        return None

    equality = first_equality(block.body)
    if equality is None or equality[0] <= prefix.end:
        return None

    target_start, target_end = trim_range(
        block.body,
        prefix.end,
        equality[0],
    )
    relations = relation_spans(block.body)
    operators = collect_operator_spans(block.body)
    target: ColorSpan | None = None
    if target_start < target_end:
        target = ColorSpan(
            target_start,
            target_end,
            COLORS["main"],
            priority=20,
        )
    semantic_rhs = _rhs_spans(block.body, equality[1])
    relations = [
        span
        for span in relations
        if not any(
            semantic.start <= span.start and span.end <= semantic.end
            for semantic in semantic_rhs
        )
    ]
    spans = [*relations, *operators, *semantic_rhs]
    if target is not None:
        spans.append(target)
    return block.render(apply_color_spans(block.body, spans))
