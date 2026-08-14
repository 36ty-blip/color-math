# Obsidian Color Math v0.1.1

Obsidian Color Math is a local Python CLI that automatically applies semantic
colors to LaTeX and MathJax equations in Obsidian Markdown notes.

## Install

After the package is published to PyPI:

```bash
pipx install obsidian-color-math
```

Or install it into the active Python environment:

```bash
python -m pip install obsidian-color-math
```

## Use

Preview a note without changing it:

```bash
color-math --file "path/to/note.md"
```

## Highlights

- Semantic coloring for supported derivatives, nested functions, matrices, and tensors.
- Generic token coloring for other display-math expressions.
- Protection for Markdown code, TeX comments, and `\verb` payloads.
- Reversible output and byte-preserving in-place writes.
- No runtime dependencies, network requests, telemetry, or external AI service.

Version 0.1.1 improves the README, package metadata, distribution checks, and
visual examples. It does not change the mathematical coloring rules.

## Current limitations

- This is a Python command-line tool, not an Obsidian Community Plugin.
- Inline `$...$` math is not converted.
- Rich semantic rules cover the forms represented by the project fixtures;
  unsupported forms remain unchanged or receive generic coloring.

See the [README](https://github.com/36ty-blip/obsidian-color-math#readme) for complete installation, usage, undo, and
safety information.
