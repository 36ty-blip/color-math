"""Small lossless LaTeX scanner for operands and structural tokens."""

from __future__ import annotations

import re
from dataclasses import dataclass


COMMAND_RE = re.compile(r"\\[A-Za-z]+|\\.")
NUMBER_RE = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)")

STYLE_MACROS = frozenset({
    "mathbf",
    "mathcal",
    "mathbb",
    "mathrm",
    "mathit",
    "mathsf",
    "mathtt",
    "boldsymbol",
    "operatorname",
    "text",
    "textbf",
    "textit",
    "textrm",
    "texttt",
})
FUNCTION_MACROS = frozenset({
    "Tr",
    "arccos",
    "arcsin",
    "arctan",
    "cos",
    "cosh",
    "det",
    "exp",
    "ln",
    "log",
    "max",
    "min",
    "sec",
    "sin",
    "sinh",
    "sqrt",
    "sup",
    "tan",
    "tanh",
    "tr",
    "trace",
    "operatorname",
})
OPERATOR_COMMANDS = frozenset({
    "bigcap",
    "bigcup",
    "bigoplus",
    "bigotimes",
    "bigsqcup",
    "bigvee",
    "bigwedge",
    "cdot",
    "coprod",
    "int",
    "iint",
    "iiint",
    "inf",
    "lim",
    "max",
    "min",
    "oint",
    "otimes",
    "prod",
    "sum",
    "sup",
    "times",
})
NON_OPERAND_COMMANDS = frozenset({
    "!",
    ",",
    ":",
    ";",
    "\\",
    "approx",
    "atop",
    "choose",
    "cap",
    "displaystyle",
    "displaylimits",
    "emptyset",
    "end",
    "equiv",
    "Leftarrow",
    "Leftrightarrow",
    "Rightarrow",
    "geq",
    "in",
    "leq",
    "leftarrow",
    "leftrightarrow",
    "limits",
    "longleftarrow",
    "longrightarrow",
    "mapsto",
    "middle",
    "mp",
    "neq",
    "nolimits",
    "notin",
    "over",
    "pm",
    "propto",
    "quad",
    "qquad",
    "right",
    "rVert",
    "scriptstyle",
    "scriptscriptstyle",
    "sim",
    "setminus",
    "subset",
    "subseteq",
    "supset",
    "supseteq",
    "to",
    "textstyle",
    "cup",
    "rightarrow",
})
UNARY_MACROS = frozenset({
    "acute",
    "bar",
    "breve",
    "check",
    "ddot",
    "dot",
    "grave",
    "hat",
    "mathring",
    "overline",
    "tilde",
    "underline",
    "vec",
    "widehat",
    "widetilde",
})
SYMBOL_MACROS = frozenset({
    "Delta",
    "Gamma",
    "Im",
    "Lambda",
    "Omega",
    "Phi",
    "Pi",
    "Psi",
    "Re",
    "Sigma",
    "Theta",
    "Upsilon",
    "Xi",
    "aleph",
    "alpha",
    "beta",
    "bot",
    "chi",
    "delta",
    "ell",
    "epsilon",
    "eta",
    "gamma",
    "hbar",
    "imath",
    "infty",
    "iota",
    "jmath",
    "kappa",
    "lambda",
    "mu",
    "nabla",
    "nu",
    "omega",
    "partial",
    "perp",
    "phi",
    "pi",
    "psi",
    "rho",
    "sigma",
    "tau",
    "theta",
    "top",
    "upsilon",
    "varepsilon",
    "varphi",
    "varpi",
    "varrho",
    "varsigma",
    "vartheta",
    "xi",
    "zeta",
})
DELIMITER_SIZE_COMMANDS = frozenset({
    "Big",
    "Bigg",
    "Biggl",
    "Biggm",
    "Biggr",
    "Bigl",
    "Bigm",
    "Bigr",
    "big",
    "bigg",
    "biggl",
    "biggm",
    "biggr",
    "bigl",
    "bigm",
    "bigr",
})
OPAQUE_MACROS = frozenset({
    "color",
    "colorbox",
    "fcolorbox",
    "text",
    "textbf",
    "textcolor",
    "textit",
    "textrm",
    "texttt",
    "verb",
})
MATRIX_ENVIRONMENTS = frozenset({
    "Bmatrix",
    "Vmatrix",
    "array",
    "bmatrix",
    "matrix",
    "pmatrix",
    "smallmatrix",
    "vmatrix",
})
NEGATABLE_RELATIONS = frozenset({
    "approx",
    "equiv",
    "geq",
    "in",
    "leq",
    "sim",
    "subset",
    "subseteq",
    "supset",
    "supseteq",
})


@dataclass(frozen=True)
class OperandSpan:
    """A half-open range containing one complete LaTeX operand."""

    kind: str
    start: int
    end: int

    def text(self, source: str) -> str:
        return source[self.start:self.end]


def skip_whitespace(source: str, index: int, end: int) -> int:
    while index < end and source[index].isspace():
        index += 1
    return index


def skip_ignorable(source: str, index: int, end: int) -> int:
    """Skip TeX whitespace and comments without changing the source."""
    while True:
        index = skip_whitespace(source, index, end)
        if index >= end or source[index] != "%":
            return index
        index = _skip_comment(source, index, end)


def read_command(source: str, start: int, end: int) -> tuple[str, int] | None:
    match = COMMAND_RE.match(source, start, end)
    if match is None:
        return None
    return match.group(0)[1:], match.end()


def _skip_comment(source: str, start: int, end: int) -> int:
    index = start + 1
    while index < end and source[index] not in "\r\n":
        index += 1
    if index < end and source[index] == "\r" and index + 1 < end and source[index + 1] == "\n":
        return index + 2
    return min(index + 1, end)


def read_group_end(
    source: str,
    start: int,
    end: int,
    opening: str | None = None,
) -> int | None:
    """Return the index after one balanced character-delimited group."""

    if start >= end:
        return None
    opening = source[start] if opening is None else opening
    closing = {"{": "}", "(": ")", "[": "]"}.get(opening)
    if closing is None or source[start] != opening:
        return None

    depth = 1
    index = start + 1
    while index < end:
        if source[index] == "%":
            index = _skip_comment(source, index, end)
            continue
        if source[index] == "\\":
            command = read_command(source, index, end)
            if command is not None and command[0] == "verb":
                verb_end = _read_verb_end(source, command[1], end)
                if verb_end >= end:
                    return None
                index = verb_end
                continue
            if command is not None and command[0] == "left":
                nested = read_left_right_end(source, index, end)
                if nested is not None:
                    index = nested
                    continue
            index = command[1] if command is not None else index + 1
            continue
        if source[index] == opening:
            depth += 1
        elif source[index] == closing:
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return None


def _read_delimiter_end(source: str, start: int, end: int) -> int | None:
    start = skip_ignorable(source, start, end)
    if start >= end:
        return None
    if source[start] == "\\":
        command = read_command(source, start, end)
        return command[1] if command is not None else None
    return start + 1


def _left_delimiter(source: str, start: int, end: int) -> str | None:
    r"""Return the delimiter following an exact ``\left`` command."""
    command = read_command(source, start, end)
    if command is None or command[0] != "left":
        return None
    delimiter_start = skip_ignorable(source, command[1], end)
    if delimiter_start >= end:
        return None
    if source[delimiter_start] != "\\":
        return source[delimiter_start]
    delimiter = read_command(source, delimiter_start, end)
    return delimiter[0] if delimiter is not None else None


def read_left_right_end(source: str, start: int, end: int) -> int | None:
    command = read_command(source, start, end)
    if command is None or command[0] != "left":
        return None
    index = _read_delimiter_end(source, command[1], end)
    if index is None:
        return None

    depth = 1
    while index < end:
        if source[index] == "%":
            index = _skip_comment(source, index, end)
            continue
        if source[index] == "{":
            group_end = read_group_end(source, index, end)
            if group_end is not None:
                index = group_end
                continue
        if source[index] != "\\":
            index += 1
            continue
        nested = read_command(source, index, end)
        if nested is None:
            index += 1
            continue
        name, command_end = nested
        if name == "verb":
            verb_end = _read_verb_end(source, command_end, end)
            if verb_end >= end:
                return None
            index = verb_end
            continue
        if name == "left":
            delimiter_end = _read_delimiter_end(source, command_end, end)
            if delimiter_end is not None:
                depth += 1
                index = delimiter_end
                continue
        elif name == "right":
            delimiter_end = _read_delimiter_end(source, command_end, end)
            if delimiter_end is not None:
                depth -= 1
                if depth == 0:
                    return delimiter_end
                index = delimiter_end
                continue
        index = command_end
    return None


def _read_environment_marker(
    source: str,
    start: int,
    end: int,
) -> tuple[str, str, int] | None:
    command = read_command(source, start, end)
    if command is None or command[0] not in {"begin", "end"}:
        return None
    marker, index = command
    group_start = skip_ignorable(source, index, end)
    group_end = read_group_end(source, group_start, end)
    if group_end is None:
        return None
    name = source[group_start + 1:group_end - 1].strip()
    if not name:
        return None
    return marker, name, group_end


def read_environment_end(source: str, start: int, end: int) -> tuple[str, int] | None:
    """Return the environment name and index after its matching ``\\end``."""

    opening = _read_environment_marker(source, start, end)
    if opening is None or opening[0] != "begin":
        return None

    stack = [opening[1]]
    index = opening[2]
    while index < end:
        if source[index] == "%":
            index = _skip_comment(source, index, end)
            continue
        if source[index] == "{":
            group_end = read_group_end(source, index, end)
            if group_end is not None:
                index = group_end
                continue
        if source[index] != "\\":
            index += 1
            continue

        marker = _read_environment_marker(source, index, end)
        if marker is None:
            command = read_command(source, index, end)
            if command is not None and command[0] == "verb":
                verb_end = _read_verb_end(source, command[1], end)
                if verb_end >= end:
                    return None
                index = verb_end
                continue
            index = command[1] if command is not None else index + 1
            continue

        marker_kind, name, marker_end = marker
        if marker_kind == "begin":
            stack.append(name)
        elif name != stack[-1]:
            return None
        else:
            stack.pop()
            if not stack:
                return opening[1], marker_end
        index = marker_end
    return None


def _read_argument_end(source: str, start: int, end: int) -> int | None:
    start = skip_ignorable(source, start, end)
    if start >= end:
        return None
    if source[start] in "{([":
        return read_group_end(source, start, end)
    if source[start] == "\\":
        operand = read_operand(source, start, end)
        return (
            operand.end
            if operand is not None and operand.kind != "opaque"
            else None
        )
    return start + 1


def _consume_scripts(source: str, start: int, end: int) -> int:
    current = start
    while True:
        marker = skip_ignorable(source, current, end)
        if marker >= end or source[marker] not in "_^":
            return current
        argument_end = _read_argument_end(source, marker + 1, end)
        if argument_end is None:
            return current
        current = argument_end


def _consume_postfix(source: str, start: int, end: int) -> int:
    """Consume attached scripts and transpose/derivative prime marks."""
    current = start
    while True:
        previous = current
        current = _consume_scripts(source, current, end)
        prime_start = skip_ignorable(source, current, end)
        if prime_start < end and source[prime_start] in "'’":
            current = prime_start
        while current < end and source[current] in "'’":
            current += 1
        if current == previous:
            return current


def _consume_operator_scripts(source: str, start: int, end: int) -> int:
    modifier_start = skip_ignorable(source, start, end)
    modifier = read_command(source, modifier_start, end)
    if modifier is not None and modifier[0] in {"displaylimits", "limits", "nolimits"}:
        start = modifier[1]
    return _consume_scripts(source, start, end)


def _read_norm_end(source: str, start: int, end: int) -> int | None:
    opening = read_command(source, start, end)
    if opening is None:
        return None
    closing_name = {"|": "|", "Vert": "Vert", "lVert": "rVert"}.get(opening[0])
    if closing_name is None:
        return None

    index = opening[1]
    brace_depth = 0
    while index < end:
        if source[index] == "%":
            index = _skip_comment(source, index, end)
            continue
        if source[index] == "{":
            brace_depth += 1
        elif source[index] == "}" and brace_depth:
            brace_depth -= 1
        elif source[index] == "\\":
            command = read_command(source, index, end)
            if command is not None:
                if command[0] == "verb":
                    verb_end = _read_verb_end(source, command[1], end)
                    if verb_end >= end:
                        return None
                    index = verb_end
                    continue
                if command[0] == "left":
                    group_end = read_left_right_end(source, index, end)
                    if group_end is not None:
                        index = group_end
                        continue
                if brace_depth == 0 and command[0] == closing_name:
                    return _consume_postfix(source, command[1], end)
                index = command[1]
                continue
        index += 1
    return None


def _consume_arguments(
    source: str,
    start: int,
    end: int,
    count: int,
) -> int | None:
    index = start
    for _ in range(count):
        argument_end = _read_argument_end(source, index, end)
        if argument_end is None:
            return None
        index = argument_end
    return index


def _consume_optional_bracket(source: str, start: int, end: int) -> int | None:
    index = skip_ignorable(source, start, end)
    if index >= end or source[index] != "[":
        return start
    return read_group_end(source, index, end)


def _read_verb_end(source: str, start: int, end: int) -> int:
    index = start + 1 if start < end and source[start] == "*" else start
    if index >= end or source[index].isspace():
        return end
    closing = source.find(source[index], index + 1, end)
    return end if closing < 0 else closing + 1


def _contains_verb_command(source: str, start: int, end: int) -> bool:
    """Return whether a range contains active verbatim math source."""
    index = start
    while index < end:
        if source[index] == "%":
            index = _skip_comment(source, index, end)
            continue
        if source[index] != "\\":
            index += 1
            continue
        command = read_command(source, index, end)
        if command is None:
            index += 1
            continue
        if command[0] == "verb":
            return True
        index = command[1]
    return False


def _read_negated_relation_end(source: str, start: int, end: int) -> int | None:
    index = skip_ignorable(source, start, end)
    if index < end and source[index] in "=<>":
        return index + 1
    command = read_command(source, index, end)
    if command is not None and command[0] in NEGATABLE_RELATIONS:
        return command[1]
    return None


def read_operand(source: str, start: int, end: int | None = None) -> OperandSpan | None:
    """Read one operand without normalizing or reconstructing its source."""

    end = len(source) if end is None else end
    if start >= end or source[start].isspace():
        return None

    if source[start] == "\\":
        command = read_command(source, start, end)
        if command is None:
            return None
        name, command_end = command
        if name == "operatorname" and command_end < end and source[command_end] == "*":
            command_end += 1
        if name in {"|", "Vert", "lVert"}:
            norm_end = _read_norm_end(source, start, end)
            if norm_end is not None:
                return OperandSpan("norm", start, norm_end)
            return OperandSpan(
                "opaque" if name == "lVert" else "structural",
                start,
                command_end if name != "lVert" else end,
            )
        if name == "verb":
            return OperandSpan("opaque", start, _read_verb_end(source, command_end, end))
        if name == "not":
            relation_end = _read_negated_relation_end(source, command_end, end)
            return OperandSpan(
                "opaque",
                start,
                relation_end if relation_end is not None else end,
            )
        if name == "begin":
            environment = read_environment_end(source, start, end)
            if environment is not None:
                environment_name, environment_end = environment
                if _contains_verb_command(source, start, environment_end):
                    return OperandSpan("opaque", start, environment_end)
                kind = "matrix" if environment_name in MATRIX_ENVIRONMENTS else "environment"
                return OperandSpan(
                    kind,
                    start,
                    _consume_postfix(source, environment_end, end),
                )
            return OperandSpan("opaque", start, end)
        if name == "left":
            group_end = read_left_right_end(source, start, end)
            if group_end is None:
                return OperandSpan("opaque", start, end)
            if _contains_verb_command(source, start, group_end):
                return OperandSpan("opaque", start, group_end)
            return OperandSpan(
                "group",
                start,
                _consume_postfix(source, group_end, end),
            )
        if name in OPERATOR_COMMANDS:
            return OperandSpan(
                "operator",
                start,
                _consume_operator_scripts(source, command_end, end),
            )
        if name == "\\":
            layout_end = command_end
            if layout_end < end and source[layout_end] == "*":
                layout_end += 1
            optional_start = skip_ignorable(source, layout_end, end)
            if optional_start < end and source[optional_start] == "[":
                optional_end = read_group_end(source, optional_start, end)
                if optional_end is None:
                    return OperandSpan("opaque", start, end)
                layout_end = optional_end
            return OperandSpan("structural", start, layout_end)
        if name in NON_OPERAND_COMMANDS:
            return OperandSpan("structural", start, command_end)
        if name in DELIMITER_SIZE_COMMANDS:
            delimiter_end = _read_delimiter_end(source, command_end, end)
            return OperandSpan(
                "structural",
                start,
                delimiter_end if delimiter_end is not None else command_end,
            )
        if name in SYMBOL_MACROS:
            return OperandSpan(
                "symbol",
                start,
                _consume_postfix(source, command_end, end),
            )

        if name in {"color", "colorbox", "textcolor"}:
            optional_end = _consume_optional_bracket(source, command_end, end)
            arguments_end = (
                _consume_arguments(source, optional_end, end, 2)
                if optional_end is not None
                else None
            )
            return OperandSpan(
                "opaque",
                start,
                arguments_end if arguments_end is not None else end,
            )

        if name == "fcolorbox":
            optional_end = _consume_optional_bracket(source, command_end, end)
            frame_end = (
                _consume_arguments(source, optional_end, end, 1)
                if optional_end is not None
                else None
            )
            background_model_end = (
                _consume_optional_bracket(source, frame_end, end)
                if frame_end is not None
                else None
            )
            arguments_end = (
                _consume_arguments(source, background_model_end, end, 2)
                if background_model_end is not None
                else None
            )
            return OperandSpan(
                "opaque",
                start,
                arguments_end if arguments_end is not None else end,
            )

        argument_count = 0
        if name in {"frac", "dfrac", "tfrac"}:
            argument_count = 2
        elif name in STYLE_MACROS:
            argument_count = 1
        elif name == "sqrt":
            optional = skip_ignorable(source, command_end, end)
            if optional < end and source[optional] == "[":
                optional_end = read_group_end(source, optional, end)
                if optional_end is None:
                    return None
                command_end = optional_end
            argument_count = 1
        elif name in UNARY_MACROS:
            argument_count = 1
        elif name in {"overset", "stackrel", "underset"}:
            argument_count = 2

        atom_end = command_end
        if argument_count:
            arguments_end = _consume_arguments(
                source,
                command_end,
                end,
                argument_count,
            )
            if arguments_end is None:
                return OperandSpan("opaque", start, end)
            atom_end = arguments_end

        if not argument_count and name not in FUNCTION_MACROS:
            return OperandSpan("opaque", start, end)

        scripted_end = _consume_scripts(source, atom_end, end)
        if name in FUNCTION_MACROS:
            group_start = skip_ignorable(source, scripted_end, end)
            if group_start < end and source[group_start] in "([":
                group_end = read_group_end(source, group_start, end)
                if group_end is not None:
                    atom_end = group_end
            elif (
                source.startswith(r"\left", group_start)
                and _left_delimiter(source, group_start, end)
                in {"(", "[", "lparen", "lbrack"}
            ):
                group_end = read_left_right_end(source, group_start, end)
                if group_end is not None:
                    atom_end = group_end
            else:
                atom_end = scripted_end

        kind = "opaque" if name in OPAQUE_MACROS else "function" if name in FUNCTION_MACROS else "operand"
        return OperandSpan(kind, start, _consume_postfix(source, atom_end, end))

    if source[start] in "({[":
        group_end = read_group_end(source, start, end)
        if group_end is None:
            return OperandSpan("opaque", start, end)
        if _contains_verb_command(source, start, group_end):
            return OperandSpan("opaque", start, group_end)
        inner_start = skip_ignorable(source, start + 1, group_end - 1)
        inner_command = read_command(source, inner_start, group_end - 1)
        kind = (
            "opaque"
            if source[start] == "{"
            and inner_command is not None
            and inner_command[0] == "color"
            else "group"
        )
        return OperandSpan(kind, start, _consume_postfix(source, group_end, end))

    number = NUMBER_RE.match(source, start, end)
    if number is not None:
        return OperandSpan(
            "number",
            start,
            _consume_postfix(source, number.end(), end),
        )

    if source[start].isalpha():
        name_end = start + 1
        while name_end < end and source[name_end] == "'":
            name_end += 1
        group_start = skip_ignorable(source, name_end, end)
        atom_end = name_end
        kind = "symbol"
        if group_start < end and source[group_start] == "(":
            group_end = read_group_end(source, group_start, end)
            if group_end is not None:
                atom_end = group_end
                kind = "function"
        elif (
            source.startswith(r"\left", group_start)
            and _left_delimiter(source, group_start, end) in {"(", "lparen"}
        ):
            group_end = read_left_right_end(source, group_start, end)
            if group_end is not None:
                atom_end = group_end
                kind = "function"
        return OperandSpan(kind, start, _consume_postfix(source, atom_end, end))

    return None


def find_operand_spans(
    source: str,
    start: int = 0,
    end: int | None = None,
) -> tuple[OperandSpan, ...]:
    """Return top-level operands in a source range."""

    end = len(source) if end is None else end
    operands: list[OperandSpan] = []
    index = start
    while index < end:
        index = skip_whitespace(source, index, end)
        if index >= end:
            break
        if source[index] == "%":
            index = _skip_comment(source, index, end)
            continue
        operand = read_operand(source, index, end)
        if operand is None:
            index += 1
            continue
        if operand.kind not in {"operator", "opaque", "structural"}:
            operands.append(operand)
        index = max(index + 1, operand.end)
    return tuple(operands)


def find_operator_spans(
    source: str,
    start: int = 0,
    end: int | None = None,
) -> tuple[OperandSpan, ...]:
    """Return top-level operators together with attached limits/scripts."""

    end = len(source) if end is None else end
    operators: list[OperandSpan] = []
    index = start
    while index < end:
        index = skip_whitespace(source, index, end)
        if index >= end:
            break
        if source[index] == "%":
            index = _skip_comment(source, index, end)
            continue
        operand = read_operand(source, index, end)
        if operand is None:
            index += 1
            continue
        if operand.kind == "operator":
            operators.append(operand)
        index = max(index + 1, operand.end)
    return tuple(operators)


def find_all_operator_spans(
    source: str,
    start: int = 0,
    end: int | None = None,
) -> tuple[OperandSpan, ...]:
    """Return operators at any structural depth, excluding opaque source."""
    end = len(source) if end is None else end
    operators: list[OperandSpan] = []
    index = start
    while index < end:
        if source[index] == "%":
            index = _skip_comment(source, index, end)
            continue

        operand = read_operand(source, index, end)
        if operand is not None:
            if operand.kind == "operator":
                operators.append(operand)
                index = operand.end
                continue
            if operand.kind == "opaque":
                index = operand.end
                continue

        if source[index] == "\\":
            command = read_command(source, index, end)
            if command is not None:
                index = command[1]
                continue
        index += 1

    return tuple(operators)


def find_top_level_tokens(
    source: str,
    tokens: tuple[str, ...],
    start: int = 0,
    end: int | None = None,
) -> tuple[tuple[int, int, str], ...]:
    """Find tokens outside complete operands/groups."""

    end = len(source) if end is None else end
    found: list[tuple[int, int, str]] = []
    index = start
    ordered = tuple(sorted(tokens, key=len, reverse=True))
    while index < end:
        index = skip_whitespace(source, index, end)
        if index >= end:
            break
        if source[index] == "%":
            index = _skip_comment(source, index, end)
            continue
        token = next(
            (
                item
                for item in ordered
                if source.startswith(item, index)
                and not (
                    item.startswith("\\")
                    and item[-1:].isalpha()
                    and index + len(item) < end
                    and source[index + len(item)].isalpha()
                )
            ),
            None,
        )
        if token is not None:
            found.append((index, index + len(token), token))
            index += len(token)
            continue
        operand = read_operand(source, index, end)
        if operand is not None:
            index = max(index + 1, operand.end)
            continue
        index += 1
    return tuple(found)


def find_script_argument_spans(source: str) -> tuple[OperandSpan, ...]:
    """Find only script arguments, leaving ``_``/``^`` source markers intact."""

    spans: list[OperandSpan] = []
    index = 0
    while index < len(source):
        if source[index] == "%":
            index = _skip_comment(source, index, len(source))
            continue
        if source[index] not in "_^":
            operand = read_operand(source, index)
            if operand is not None and operand.kind == "opaque":
                index = operand.end
                continue
            if source[index] == "\\":
                command = read_command(source, index, len(source))
                if command is not None:
                    index = command[1]
                    continue
            index += 1
            continue

        argument_start = skip_ignorable(source, index + 1, len(source))
        argument_end = _read_argument_end(source, argument_start, len(source))
        if argument_end is None:
            index += 1
            continue
        if source[argument_start:argument_start + 1] == "{":
            inner_start = argument_start + 1
            inner_end = argument_end - 1
        else:
            inner_start = argument_start
            inner_end = argument_end
        if inner_start < inner_end:
            spans.append(
                OperandSpan(
                    "subscript" if source[index] == "_" else "superscript",
                    inner_start,
                    inner_end,
                )
            )
        index = argument_end
    return tuple(spans)
