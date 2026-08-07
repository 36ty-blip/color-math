"""Preview or remove LaTeX color wrappers from a Markdown file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from color_math.io import encode_utf8, read_utf8, replace_bytes
from color_math.undo import uncolor_text


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove LaTeX color wrappers from a Markdown file."
    )
    parser.add_argument("file", type=Path, help="Markdown file to undo")
    parser.add_argument(
        "-i", "--in-place", action="store_true", help="Overwrite the file"
    )
    args = parser.parse_args()

    try:
        text, source = read_utf8(args.file)
    except (OSError, UnicodeDecodeError) as error:
        parser.exit(1, f"undo: cannot read {args.file}: {error}\n")

    restored = uncolor_text(text)
    output = encode_utf8(restored, source)
    if args.in_place:
        try:
            replace_bytes(args.file, output, source)
        except OSError as error:
            parser.exit(1, f"undo: cannot replace {args.file}: {error}\n")
    else:
        sys.stdout.buffer.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
