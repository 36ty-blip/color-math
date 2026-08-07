# latex_helpers.py

import re


COMMAND_RE = re.compile(r"\\[A-Za-z]+|\\.")


def read_comment_end(text: str, start: int) -> int:
    """Return the index after one TeX comment, including its newline."""
    index = start + 1
    while index < len(text) and text[index] not in "\r\n":
        index += 1
    if text.startswith("\r\n", index):
        return index + 2
    return min(index + 1, len(text))


def read_verb_end(text: str, start: int) -> tuple[int, bool] | None:
    r"""Read an exact ``\verb``/``\verb*`` payload without inspecting it."""
    if not text.startswith(r"\verb", start):
        return None
    command_end = start + len(r"\verb")
    if command_end < len(text) and text[command_end].isalpha():
        return None
    if command_end < len(text) and text[command_end] == "*":
        command_end += 1
    if command_end >= len(text) or text[command_end].isspace():
        return len(text), False

    delimiter = text[command_end]
    closing = text.find(delimiter, command_end + 1)
    return (
        (len(text), False)
        if closing < 0
        else (closing + 1, True)
    )


def read_braced(text: str, start: int) -> tuple[str, int] | None:
    """
    Read a balanced {...} group starting at index 'start'.

    Returns:
        (captured_text, end_index)

    Example:
        "{abc}" -> ("{abc}", 5)
    """
    if start >= len(text) or text[start] != "{":
        return None

    depth = 0
    index = start

    while index < len(text):
        char = text[index]

        if char == "%":
            index = read_comment_end(text, index)
            continue

        if char == "\\":
            verb = read_verb_end(text, index)
            if verb is not None:
                index, closed = verb
                if not closed:
                    return None
                continue
            command = COMMAND_RE.match(text, index)
            index = command.end() if command is not None else index + 1
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1], index + 1

        index += 1

    return None


def read_script_argument(text: str, start: int) -> tuple[str, int] | None:
    """
    Read argument after _ or ^

    Handles:
        x^{abc}
        x^n
        x^\\alpha
    """

    if start >= len(text):
        return None

    # Braced argument
    if text[start] == "{":
        return read_braced(text, start)

    if text[start] in "$\r\n":
        return None

    # Latex command
    if text[start] == "\\":
        match = re.match(r"\\[A-Za-z]+|\\.", text[start:])
        if match:
            return match.group(0), start + len(match.group(0))

    # Single character
    return text[start], start + 1


def read_script(text: str, start: int) -> tuple[str, int, bool] | None:
    """
    Read full superscript/subscript.

    Example:
        "^2"
        "_{abc}"
        "^\\alpha"
    """

    marker = text[start]   # _ or ^

    argument_start = start + 1

    if argument_start < len(text) and text[argument_start] == "{":
        argument_data = read_braced(text, argument_start)

        if argument_data is None:
            return text[start:], len(text), False

        argument, end = argument_data
        return f"{marker}{argument}", end, True

    argument_data = read_script_argument(text, argument_start)

    if argument_data is None:
        return None

    argument, end = argument_data

    return f"{marker}{argument}", end, True


def read_color_wrapper(text: str, start: int) -> tuple[str, int] | None:
    """
    Read a scoped color wrapper and return its unbraced value and end index.

    Supports current ``\\textcolor{red}{x}`` output and legacy
    ``\\color{red}{x}`` output. Command names are matched exactly, so macros
    such as ``\\colorbox`` and ``\\colorful`` are left alone.
    """
    command = next(
        (
            candidate
            for candidate in (r"\textcolor", r"\color")
            if text.startswith(candidate, start)
            and (
                start + len(candidate) == len(text)
                or not text[start + len(candidate)].isalpha()
            )
        ),
        None,
    )
    if command is None:
        return None

    index = start + len(command)

    while index < len(text) and text[index].isspace():
        index += 1

    color_data = read_braced(text, index)
    if color_data is None:
        return None

    _, index = color_data

    while index < len(text) and text[index].isspace():
        index += 1

    value_data = read_braced(text, index)
    if value_data is None:
        return None

    value, end = value_data
    return value[1:-1], end


def read_color_command(text: str, start: int) -> tuple[str, int] | None:
    """
    Detect an existing scoped color command.

    Examples:
        \\textcolor{red}{x}
        \\color{red}{x}

    Returns:
        (full_command, end_index)
        or None
    """
    wrapper = read_color_wrapper(text, start)
    if wrapper is None:
        return None

    _, end = wrapper
    return text[start:end], end


def contains_color_wrapper(text: str) -> bool:
    """Find active wrappers, ignoring TeX comments and verbatim payloads."""
    index = 0
    while index < len(text):
        if text[index] == "%":
            index = read_comment_end(text, index)
            continue
        if text[index] == "\\":
            if read_color_wrapper(text, index) is not None:
                return True
            verb = read_verb_end(text, index)
            if verb is not None:
                index = verb[0]
                continue
            command = COMMAND_RE.match(text, index)
            index = command.end() if command is not None else index + 1
            continue
        index += 1
    return False
