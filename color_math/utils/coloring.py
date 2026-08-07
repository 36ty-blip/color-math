# utils/coloring.py

from ..config import (
    COLORS,
    BIG_OPERATORS,
    INTEGRALS,
    LIMIT_OPERATORS,
    ARROWS,
    SET_SYMBOLS,
    SPACING_COMMANDS,
    MULTIPLICATION_SYMBOLS,
)


def latex_color(color: str, value: str) -> str:
    """
    Wrap LaTeX text in a color command.

    Example:
        ("red", "x")
        -> "\\textcolor{red}{x}"
    """
    return rf"\textcolor{{{color}}}{{{value}}}"


def command_color(command: str) -> str:
    """
    Determine which color category a LaTeX command belongs to.

    Example:
        "\\sum" -> orange
        "\\rightarrow" -> arrow color
        "\\in" -> set color
    """

    # Big math operators
    if (
        command in BIG_OPERATORS
        or command in INTEGRALS
        or command in LIMIT_OPERATORS
    ):
        return COLORS["orange"]

    # Arrows
    if command in ARROWS:
        return COLORS["arrow"]

    # Set theory symbols
    if command in SET_SYMBOLS:
        return COLORS["set"]

    # Spacing commands
    if command in SPACING_COMMANDS:
        return COLORS["spacing"]

    # Multiplication symbols
    if command in MULTIPLICATION_SYMBOLS:
        return COLORS["dot"]

    # Default relations (=, <, >, etc.)
    return COLORS["relation"]
