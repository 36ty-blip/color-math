# Forum post draft: Color Math — a local LaTeX colorizer for Obsidian notes

Hi everyone! I built a small local Python tool called **Color Math** that adds semantic color to LaTeX math inside Obsidian Markdown notes.

It converts `$$ ... $$` blocks into scoped `\textcolor{...}{...}` LaTeX for Obsidian's MathJax renderer. Beyond generic tokens such as relations and sums, it recognizes selected semantic structures including chain-rule derivatives, nested derivative stages, matrix/tensor expressions, determinants, traces, norms, and tensor products.

Example input:

```latex
$$
\frac{d}{dx}f(g(y))
=
f'(g(y))\cdot g'(y)y'
$$
```

The output keeps every original LaTeX character and only inserts color wrappers around recognized ranges. It colors the main expression, derivative stages, chain terms, relations, and multiplication markers separately; undo restores the exact input. Markdown code, TeX comments, `\verb` payloads, and prose outside display math are protected.

Repository: **[replace this text with the public GitHub URL before posting]**

Run it locally with:

```bash
python -m pip install .
python -m color_math --file tests/original/derivatives.md
```

In-place conversion preserves the note's UTF-8 BOM and newline style and uses an atomic replacement, while preview mode leaves the file untouched.

It includes regression fixtures for straightforward, matrix/tensor, and deeply nested derivative cases. It is currently a CLI tool rather than a native Obsidian plugin, so I’d especially welcome feedback on:

1. Whether this would be useful in real note-taking workflows.
2. Which LaTeX patterns should be prioritized next.
3. Whether a native plugin version would be worth building.

Everything runs locally; it makes no network requests or use of external AI services.
