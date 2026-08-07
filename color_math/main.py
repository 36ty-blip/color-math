# main.py

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import COLORS
from .converters.block import convert_text
from .io import encode_utf8, read_utf8, replace_bytes
from .parsers.math_parser import describe_math_blocks
from .self_test import run_self_test
from .undo import uncolor_text


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Colorize LaTeX math expressions."
    )

    parser.add_argument(
        "input",
        nargs="?",
        help=(
            "Equation text, or file path when --file is used. "
            "Reads stdin if omitted."
        ),
    )

    parser.add_argument(
        "-f",
        "--file",
        action="store_true",
        help="Treat input as a file path and convert file contents.",
    )

    parser.add_argument(
        "-i",
        "--in-place",
        action="store_true",
        help="Write converted text back to file. Requires --file.",
    )

    parser.add_argument(
        "--main-color",
        default=COLORS["main"],
        help="Override main function color.",
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run internal tests and dependency checks.",
    )

    parser.add_argument(
        "--update-generated",
        action="store_true",
        help="Refresh tests/generated while running --self-test.",
    )

    parser.add_argument(
        "--parse",
        action="store_true",
        help="Inspect nested function calls without rewriting LaTeX.",
    )

    parser.add_argument(
        "--undo",
        action="store_true",
        help="Remove LaTeX color wrappers instead of adding them.",
    )

    args = parser.parse_args()

    # sanity check
    if args.in_place and not args.file:
        parser.error("--in-place requires --file")
    if args.update_generated and not args.self_test:
        parser.error("--update-generated requires --self-test")

    # run tests
    if args.self_test:
        return run_self_test(update_generated=args.update_generated)

    # allow runtime color override
    COLORS["main"] = args.main_color

    # file mode
    if args.file:
        if not args.input:
            parser.error("--file requires a path")

        path = Path(args.input)
        try:
            text, source = read_utf8(path)
        except UnicodeDecodeError as error:
            parser.exit(
                1,
                f"color-math: {path} is not valid UTF-8 "
                f"(byte {error.start})\n",
            )
        except OSError as error:
            parser.exit(1, f"color-math: cannot read {path}: {error}\n")

        if args.parse:
            sys.stdout.write(describe_math_blocks(text))
            return 0

        converted = uncolor_text(text) if args.undo else convert_text(text)
        output = encode_utf8(converted, source)

        if args.in_place:
            try:
                replace_bytes(path, output, source)
            except OSError as error:
                parser.exit(1, f"color-math: cannot replace {path}: {error}\n")
            return 0

        sys.stdout.buffer.write(output)
        return 0

    # direct input or stdin
    text = (
        args.input
        if args.input is not None
        else sys.stdin.read()
    )

    if args.parse:
        sys.stdout.write(describe_math_blocks(text))
        return 0

    sys.stdout.write(uncolor_text(text) if args.undo else convert_text(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
