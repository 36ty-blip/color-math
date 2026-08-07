from __future__ import annotations

from .parsers.markdown_scanner import scan_markdown
from .utils.latex_helpers import (
    COMMAND_RE,
    read_color_wrapper,
    read_comment_end,
    read_verb_end,
)


def uncolor_fragment(text: str) -> str:
    r"""Remove nested ``\textcolor`` and legacy ``\color`` wrappers."""
    output: list[str] = []
    index = 0

    while index < len(text):
        if text[index] == "%":
            end = read_comment_end(text, index)
            output.append(text[index:end])
            index = end
            continue

        if text[index] == "\\":
            wrapper = read_color_wrapper(text, index)
            if wrapper is not None:
                value, index = wrapper
                output.append(uncolor_fragment(value))
                continue

            verb = read_verb_end(text, index)
            if verb is not None:
                end, _ = verb
                output.append(text[index:end])
                index = end
                continue

            command = COMMAND_RE.match(text, index)
            if command is not None:
                output.append(command.group(0))
                index = command.end()
                continue

        output.append(text[index])
        index += 1

    return "".join(output)


def uncolor_text(text: str) -> str:
    r"""Remove wrappers in display math; leave all other Markdown untouched."""
    math_blocks = scan_markdown(text).math_blocks
    if not math_blocks:
        return text

    output: list[str] = []
    index = 0
    for span in math_blocks:
        output.append(text[index:span.start])
        output.append(uncolor_fragment(text[span.start:span.end]))
        index = span.end
    output.append(text[index:])
    return "".join(output)
