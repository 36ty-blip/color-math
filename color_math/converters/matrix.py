"""Lossless semantic coloring for matrix and indexed tensor expressions."""

from __future__ import annotations

import re

from ..config import COLORS
from ..parsers.latex_spans import OperandSpan, find_operand_spans, read_operand
from ..parsers.scanner import collect_operator_spans
from ..utils.latex_helpers import contains_color_wrapper
from ..utils.spans import ColorSpan, apply_color_spans
from .semantic import first_equality, parse_math_block, relation_spans


MATRIX_COMMAND_RE = re.compile(
    r"\\(?:mathbf|mathcal|nabla|det|tr|Tr|trace|Vert|lVert)"
    r"(?![A-Za-z])|\\\|(?![A-Za-z])|"
    r"\\operatorname\s*\{\s*tr\s*\}"
)
MATRIX_ENV_RE = re.compile(
    r"\\begin\s*\{\s*"
    r"(?:Bmatrix|Vmatrix|array|bmatrix|matrix|pmatrix|smallmatrix|vmatrix)"
    r"\s*\}"
)
NUMBER_RE = re.compile(r"[+-]?\d+(?:\.\d+)?")


def _structural_source(body: str) -> str:
    """Mask comments and opaque macros before semantic classification."""
    visible = list(body)
    index = 0
    while index < len(body):
        if body[index] == "%":
            end = index + 1
            while end < len(body) and body[end] not in "\r\n":
                visible[end] = " "
                end += 1
            visible[index] = " "
            index = end
            continue
        operand = read_operand(body, index)
        if operand is not None and operand.kind == "opaque":
            for position in range(operand.start, operand.end):
                if visible[position] not in "\r\n":
                    visible[position] = " "
            index = operand.end
            continue
        index += 1
    return "".join(visible)


def _is_matrix_expression(body: str) -> bool:
    structural = _structural_source(body)
    operands = find_operand_spans(structural)
    return (
        MATRIX_COMMAND_RE.search(structural) is not None
        or MATRIX_ENV_RE.search(structural) is not None
        or any(
            operand.kind == "matrix"
            or (operand.kind == "symbol" and "_" in operand.text(structural))
            for operand in operands
        )
    )


def _operand_color_spans(
    body: str,
    operands: tuple[OperandSpan, ...],
    names: tuple[str, ...],
) -> list[ColorSpan]:
    spans: list[ColorSpan] = []
    semantic_index = 0
    for operand in operands:
        value = re.sub(r"\s+", "", operand.text(body))
        if NUMBER_RE.fullmatch(value):
            name = "orange"
        else:
            name = names[min(semantic_index, len(names) - 1)]
            semantic_index += 1
        spans.append(
            ColorSpan(
                operand.start,
                operand.end,
                COLORS[name],
                priority=20,
            )
        )
    return spans


def _operator_spans(body: str) -> list[ColorSpan]:
    return collect_operator_spans(body)


def convert_matrix_block(source: str) -> str | None:
    """Color complete matrix/tensor operands without reconstructing LaTeX."""
    block = parse_math_block(source)
    if block is None or not _is_matrix_expression(block.body):
        return None
    if contains_color_wrapper(block.body):
        return source

    equality = first_equality(block.body)
    if equality is None:
        return None

    lhs = find_operand_spans(block.body, 0, equality[0])
    rhs = find_operand_spans(block.body, equality[1])
    if not lhs or not rhs:
        return None

    lhs_first = re.sub(r"\s+", "", lhs[0].text(block.body))
    if len(lhs) == 1:
        lhs_colors = (
            ("upper",)
            if lhs_first.startswith((r"\det", r"\operatorname{tr}"))
            else ("main",)
        )
    elif lhs_first.startswith((r"\frac{\partial}", r"\nabla")):
        lhs_colors = ("upper", "main")
    else:
        lhs_colors = ("upper", "chain", "orange")

    lhs_text = re.sub(r"\s+", "", block.body[:equality[0]])
    if lhs_first.startswith(r"\frac{\partial}"):
        rhs_colors = ("chain", "main")
    elif len(lhs) > 1 and len(rhs) == 1:
        rhs_colors = ("main",)
    elif lhs_text.startswith((r"\det", r"\operatorname{tr}")):
        rhs_colors = ("main", "chain")
    elif r"\otimes" in block.body:
        rhs_colors = ("upper", "chain", "orange")
    else:
        rhs_colors = ("upper", "chain")

    spans = relation_spans(block.body)
    spans.extend(_operand_color_spans(block.body, lhs, lhs_colors))
    spans.extend(_operand_color_spans(block.body, rhs, rhs_colors))
    spans.extend(_operator_spans(block.body))
    return block.render(apply_color_spans(block.body, spans))
