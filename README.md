# 🎨 Obsidian Color Math

> Semantic color for LaTeX in Obsidian, without handing your notation to a computer algebra system.

Obsidian Color Math is a local Python command-line tool that adds semantic color to display-math blocks in Markdown notes. It inserts scoped `\textcolor{...}{...}` wrappers for Obsidian's MathJax renderer while preserving the original LaTeX structure.

> [!IMPORTANT]
> **Current status:** this is an alpha command-line tool, not an official Obsidian Community Plugin. It runs locally, makes no network requests, collects no telemetry, and uses no external AI service.

## ✨ Highlights

| Feature | Current behavior |
| --- | --- |
| Derivatives | Colors chain-rule stages, coefficients, powers, and selected nested forms semantically. |
| Nested functions | Distinguishes calls such as `y(x(g(3)))`, including `y`, `x`, and `g`, while treating `3` as a constant. |
| Matrices and tensors | Handles products, transpose/inverse groups, determinants, traces, norms, contractions, and tensor products. |
| General LaTeX | Colors operators, relations, arrows, scripts, sums, integrals, and limits. |
| Markdown safety | Leaves fenced code, inline code, TeX comments, and `\verb` payloads unchanged. |
| Reversibility | Removes both current `\textcolor` output and compatible legacy `\color` wrappers. |

## 🌈 Before and after

Input:

```latex
$$
\frac{d}{dx}f(g(y))
=
f'(g(y))\cdot g'(y)y'
$$
```

Generated output:

```latex
$$
\frac{d}{dx}\textcolor{#7aa2f7}{f(g(y))}
\textcolor{white}{=}
\textcolor{#bb9af7}{f'(g(y))}\textcolor{white}{\cdot} \textcolor{#9ece6a}{g'(y)}\textcolor{#9ece6a}{y'}
$$
```

The inserted wrappers are ordinary MathJax-compatible LaTeX, so the result stays inside the Markdown note rather than depending on a custom Obsidian theme.

## 🚀 Quick start

### Requirements

- Python 3.10 or newer
- Obsidian with its built-in MathJax rendering

### Install

From the repository directory:

```bash
python -m pip install .
```

There are no third-party runtime dependencies. `python -m pip install -r requirements.txt` is also supported for compatibility.

> [!TIP]
> Installation provides the shorter `color-math` command. You can use `color-math` anywhere this README shows `python -m color_math`.

### Convert a note

Preview the converted Markdown in the terminal:

```bash
python -m color_math --file "path/to/note.md"
```

Write the conversion back to the note:

```bash
python -m color_math --file --in-place "path/to/note.md"
```

Convert one expression directly:

```bash
python -m color_math "$$\\frac{d}{dx}f(y)^n=nf(y)^{n-1}\\cdot f'(y)y'$$"
```

## 🎨 Customize the colors

Edit the `COLORS` dictionary in [`color_math/config.py`](color_math/config.py):

```python
COLORS = {
    "main": "#7aa2f7",
    "orange": "#e0af68",
    "dot": "white",
    "derivative": "#bb9af7",
    "chain": "#9ece6a",
    "upper": "#bb9af7",
    "relation": "white",
    "arrow": "#f7768e",
    "set": "#bb9af7",
    "spacing": "white",
}
```

Keep the role names and replace only their values with MathJax-compatible color names or hex colors. The palette has 10 roles using 6 distinct default colors. For a temporary change to only the main color, use `--main-color "#your-color"`.

## ↩️ Undo colors

Preview a color-free version:

```bash
python -m color_math --file --undo "path/to/colored-note.md"
```

Overwrite the note only when the preview looks correct:

```bash
python -m color_math --file --undo --in-place "path/to/colored-note.md"
```

> [!WARNING]
> Undo removes generated `\textcolor{...}{...}` wrappers and legacy `\color{...}{...}` wrappers inside detected `$$...$$` blocks. It cannot distinguish generated wrappers from color wrappers you wrote by hand inside display math, so preview before using `--in-place` on a note with manual colors.

Text outside display math, Markdown code, TeX comments, and `\verb` payloads are left untouched.

## 🔎 Inspect math structure

Use the source-preserving parser to inspect recognized nested function calls and constants:

```bash
python -m color_math --file --parse tests/original/derivatives.md
```

The inspector reports structure without rewriting the LaTeX or pretending unsupported matrix/tensor notation is a scalar expression.

## 🧪 Verify the project

```bash
python -m color_math --self-test
python -m tests.self_test
```

- `python -m color_math --self-test` runs the installed-package smoke tests.
- `python -m tests.self_test` runs the exact repository suite, including byte-for-byte fixtures, undo round trips, idempotence, Markdown protection, BOM/newline preservation, and atomic file replacement.

Both commands are read-only by default. Refresh [`tests/generated/`](tests/README.md) explicitly:

```bash
python -m tests.self_test --update-generated
```

GitHub Actions runs the suite on Windows and Linux. You can also build a local wheel without another packaging dependency:

```bash
python -m pip wheel --no-deps --wheel-dir dist .
```

## 🗂️ Project layout

The package is separated into conversion rules, source-preserving parsers, and small shared utilities:

```text
obsidian-color-math/
├── color_math/
│   ├── converters/                 # LaTeX coloring rules
│   │   ├── __init__.py
│   │   ├── align.py                # Reserved align-environment rule
│   │   ├── block.py                # Main Markdown-to-math pipeline
│   │   ├── derivative.py           # Chain-rule semantic formatter
│   │   ├── equation.py             # Reserved equation rule
│   │   ├── generic.py              # Token-coloring fallback
│   │   ├── integral.py             # Reserved integral rule
│   │   ├── limit.py                # Reserved limit rule
│   │   ├── matrix.py               # Matrix and tensor formatter
│   │   └── semantic.py             # Shared math-block helpers
│   ├── parsers/                    # Lossless Markdown and LaTeX scanning
│   │   ├── __init__.py
│   │   ├── latex_spans.py          # Lossless LaTeX operand spans
│   │   ├── markdown_scanner.py     # Code-fence-aware Markdown spans
│   │   ├── math_parser.py          # Nested-function inspector
│   │   └── scanner.py              # Generic operator scanner
│   ├── utils/                      # Small shared formatting helpers
│   │   ├── __init__.py
│   │   ├── coloring.py             # Builds color wrappers
│   │   ├── latex_helpers.py        # Balanced-group and command readers
│   │   └── spans.py                # Selects and applies color spans
│   ├── __init__.py                 # Public conversion and undo helpers
│   ├── __main__.py                 # `python -m color_math` entry point
│   ├── config.py                   # Color palette and command groups
│   ├── io.py                       # Byte-preserving atomic file writes
│   ├── main.py                     # Command-line interface
│   ├── self_test.py                # Installed-package smoke tests
│   └── undo.py                     # Removes current and legacy colors
├── tests/
│   ├── original/                   # Unprocessed Markdown fixtures
│   ├── expected/                   # Exact expected output
│   ├── generated/                  # Latest generated output
│   ├── __init__.py
│   ├── README.md                   # Fixture guide
│   └── self_test.py                # Exact and round-trip test suite
├── docs/
│   └── examples.md                 # Additional usage examples
├── .github/
│   └── workflows/
│       └── tests.yml               # Windows and Linux CI
├── .gitignore                      # Local/build files excluded from Git
├── COMMUNITY_POST.md               # Obsidian community announcement draft
├── LICENSE                         # MIT License
├── pyproject.toml                  # Package metadata and CLI entry point
├── README.md                       # This guide
├── requirements.txt                # Compatibility installation file
└── UNDO.py                         # Backward-compatible undo launcher
```

## ⚠️ Limitations

- Generic LaTeX receives token-level coloring when no semantic rule matches.
- Rich semantic coloring currently covers the derivative, matrix, and tensor forms represented by the test fixtures; it does not algebraically simplify or repair expressions.
- Nested-call recognition currently covers plain `name(...)` and `name\left(...\right)` forms. Unsupported forms remain unchanged or receive generic coloring.
- Inline `$...$` math is intentionally not converted yet.
- The Markdown scanner protects common fenced-code, inline-code, list, blockquote, and Obsidian-callout forms, but it is not a complete CommonMark parser. Rare indentation and lazy-container forms may need manual review.
- `--in-place` expects UTF-8. It preserves UTF-8 BOMs and exact newline bytes, writes a same-directory temporary file, and atomically replaces the note only after the full output reaches disk.

## 🤝 Contributing

The most useful contribution is a representative fixture containing:

1. The unprocessed Markdown and LaTeX input.
2. The exact output you expect.
3. A short explanation of the intended Obsidian/MathJax rendering.

See [`tests/README.md`](tests/README.md) for the fixture layout and [`COMMUNITY_POST.md`](COMMUNITY_POST.md) for the community announcement draft.

## 📄 License

Released under the [MIT License](LICENSE).
