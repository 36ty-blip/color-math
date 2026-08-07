from __future__ import annotations

from collections.abc import Iterable

from .converters.block import convert_text
from .converters.matrix import convert_matrix_block
from .parsers.math_parser import (
    format_math_structure,
    parse_math_blocks,
    parse_math_body,
)
from .undo import uncolor_fragment, uncolor_text


Check = tuple[str, object, object]


def _run_checks(checks: Iterable[Check]) -> int:
    failed = False
    print("Running installed self-tests...\n")
    for name, actual, expected in checks:
        passed = actual == expected
        print(f"{'OK' if passed else 'FAIL'}  {name}")
        if not passed:
            print(f"Expected: {expected!r}")
            print(f"Got:      {actual!r}\n")
            failed = True
    print("\nAll tests passed." if not failed else "\nSome tests failed.")
    return int(failed)


def run_self_test(update_generated: bool = False) -> int:
    """Run installed smoke checks without reading or writing repository files."""
    if update_generated:
        print(
            "--update-generated is repository-only; run "
            "`python -m tests.self_test --update-generated` from a checkout."
        )
        return 2

    nested = r"$$y(x(g(3)))$$"
    nested_colored = (
        r"$$\textcolor{#7aa2f7}{y}("
        r"\textcolor{#bb9af7}{x}("
        r"\textcolor{#9ece6a}{g}("
        r"\textcolor{#e0af68}{3})))$$"
    )
    prime = r"$$f'(g(3))$$"
    prime_colored = (
        r"$$\textcolor{#7aa2f7}{f'}("
        r"\textcolor{#bb9af7}{g}("
        r"\textcolor{#e0af68}{3}))$$"
    )
    fenced = "```latex\n$$\\sum_{i=1}^n$$\n```"
    nested_fence = (
        "- item\n"
        "  > [!note]\n"
        "  > ~~~~latex\n"
        "  > $$y(x(g(3)))$$\n"
        "  > ~~~~\n"
    )
    commented = "$$f(x)% }\n+g(x)% {\n+h(x)$$"
    commented_colored = (
        "$$\\textcolor{#7aa2f7}{f}(x)% }\n"
        "+\\textcolor{#7aa2f7}{g}(x)% {\n"
        "+\\textcolor{#7aa2f7}{h}(x)$$"
    )
    verb = r"$$\verb|y(x(g(3)))|$$"
    verb_star = r"$$\verb*|y(x(g(3)))|$$"
    scalar_sum = r"$$\sum_{i=1}^{n} x_i$$"
    nested_array = (
        r"$$\mathbf{M}=\left(\begin{array}{cc}a&b\\c&d"
        r"\end{array}\right)$$"
    )
    nested_array_colored = (
        r"$$\textcolor{#7aa2f7}{\mathbf{M}}\textcolor{white}{=}"
        r"\textcolor{#bb9af7}{\left(\begin{array}{cc}a&b\\c&d"
        r"\end{array}\right)}$$"
    )
    grouped_command = r"$$\operatorname*{arg\,max}_{x} f(x)$$"
    grouped_command_colored = (
        r"$$\operatorname*{arg\textcolor{white}{\,}max}_"
        r"{\textcolor{#9ece6a}{x}} \textcolor{#7aa2f7}{f}(x)$$"
    )
    styled = r"$$f(x)+\displaystyle g(x)$$"
    styled_colored = (
        r"$$\textcolor{#7aa2f7}{f}(x)+\displaystyle "
        r"\textcolor{#7aa2f7}{g}(x)$$"
    )
    inline_code = "Prose `$$x=1$$` remains plain."
    prose = "# Original Equations\n\nOrdinary prose stays unchanged.\n"

    return _run_checks(
        (
            ("scoped nested colors", convert_text(nested), nested_colored),
            ("exact undo round trip", uncolor_text(nested_colored), nested),
            (
                "conversion idempotence",
                convert_text(nested_colored),
                nested_colored,
            ),
            ("prime notation", convert_text(prime), prime_colored),
            ("prime round trip", uncolor_text(prime_colored), prime),
            (
                "no invented primes",
                "y'" in convert_text(
                    r"$$\frac{d}{dx}f(y)^n=nf(y)^{n-1}\cdot f'(y)y$$"
                ),
                False,
            ),
            ("prose preservation", convert_text(prose), prose),
            ("fenced code preservation", convert_text(fenced), fenced),
            (
                "comment braces round trip",
                uncolor_text(convert_text(commented)),
                commented,
            ),
            (
                "comment braces idempotence",
                convert_text(commented_colored),
                commented_colored,
            ),
            (
                "nested tilde fence preservation",
                convert_text(nested_fence),
                nested_fence,
            ),
            (
                "nested tilde fence is not parsed",
                parse_math_blocks(nested_fence),
                [],
            ),
            ("verb payload preservation", convert_text(verb), verb),
            ("verb-star payload preservation", convert_text(verb_star), verb_star),
            (
                "verb payload is not inspected",
                format_math_structure(parse_math_body(verb[2:-2])),
                "No nested function calls found.",
            ),
            (
                "scalar sum is not a matrix",
                convert_matrix_block(scalar_sum),
                None,
            ),
            (
                "nested array matrix recognition",
                convert_matrix_block(nested_array),
                nested_array_colored,
            ),
            (
                "operatorname-star stays whole",
                convert_text(grouped_command),
                grouped_command_colored,
            ),
            (
                "style declaration stays unwrapped",
                convert_text(styled),
                styled_colored,
            ),
            ("inline code preservation", convert_text(inline_code), inline_code),
            (
                "text macro preservation",
                convert_text(r"$$f(\text{use x=y literally})$$"),
                r"$$\textcolor{#7aa2f7}{f}(\text{use x=y literally})$$",
            ),
            (
                "malformed script preservation",
                convert_text(r"$$x^{abc$$"),
                r"$$x^{abc$$",
            ),
            (
                "unclosed call preservation",
                convert_text(r"$$y(x$$"),
                r"$$y(x$$",
            ),
            (
                "nested function structure",
                format_math_structure(parse_math_body("y(x(g(3)))")),
                "Function y\n  Function x\n    Function g\n      Constant 3",
            ),
            (
                "legacy and scoped undo",
                uncolor_fragment(r"\textcolor{red}{x+\color{blue}{y}}"),
                "x+y",
            ),
        )
    )
