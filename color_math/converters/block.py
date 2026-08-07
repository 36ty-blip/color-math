# converters/block.py

from __future__ import annotations
import re
from collections.abc import Callable

from ..parsers.markdown_scanner import scan_markdown
from .align import convert_align_block
from .derivative import convert_derivative_line
from .equation import convert_equation_line
from .generic import color_latex_body, color_generic_math_line
from .integral import convert_integral_line
from .limit import convert_limit_line
from .matrix import convert_matrix_block


MATH_BLOCK_RE = re.compile(
    r"^(?P<prefix>\s*\#+\s*)?\$\$(?P<body>.*)\$\$(?P<suffix>\s*)$",
    re.DOTALL,
)
Converter = Callable[[str], str | None]

LINE_CONVERTERS: tuple[Converter, ...] = (
    convert_derivative_line,
    convert_integral_line,
    convert_limit_line,
    convert_equation_line,
)

BLOCK_CONVERTERS: tuple[Converter, ...] = (
    convert_matrix_block,
    convert_align_block,
)


def try_converters(text: str, converters: tuple[Converter, ...]) -> str | None:
    for converter in converters:
        converted = converter(text)

        if converted is not None:
            return converted

    return None


def convert_math_block(block: str) -> str:
    """
    Convert a multiline math block.

    Specialized converters insert wrappers into the original source. Generic
    coloring is used only when no semantic formatter recognizes the block.
    """

    match = MATH_BLOCK_RE.match(block)

    if not match:
        return block

    prefix = match.group("prefix") or ""
    body = match.group("body")
    suffix = match.group("suffix")

    line_match = try_converters(block, LINE_CONVERTERS)

    if line_match is not None:
        return line_match

    block_match = try_converters(block, BLOCK_CONVERTERS)

    if block_match is not None:
        return block_match

    # fallback to generic coloring
    return f"{prefix}$${color_latex_body(body)}$${suffix}"


def convert_line(line: str) -> str:
    """
    Convert a single line.

    Checks specialized converters first,
    otherwise generic math coloring.
    """

    converted = try_converters(line, LINE_CONVERTERS)

    if converted is not None:
        return converted

    return color_generic_math_line(line)


def convert_text(text: str) -> str:
    """
    Convert an entire document.

    Handles:
      - inline math lines
      - multiline $$ ... $$ math blocks
      - normal text passthrough
    """

    math_blocks = scan_markdown(text).math_blocks
    if not math_blocks:
        return text

    converted: list[str] = []
    index = 0
    for span in math_blocks:
        converted.append(text[index:span.start])
        converted.append(convert_math_block(text[span.start:span.end]))
        index = span.end
    converted.append(text[index:])
    return "".join(converted)
