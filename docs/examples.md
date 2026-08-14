# Examples

Color Math processes display-math blocks delimited by `$$`. Inline `$...$`
math is intentionally left unchanged.

## Preview a note

Print the converted Markdown without changing the file:

```bash
color-math --file tests/original/derivatives.md
```

## Update a note

```bash
color-math --file --in-place "path/to/note.md"
```

## Undo generated colors

Preview first, then add `--in-place` when the result is correct:

```bash
color-math --file --undo "path/to/colored-note.md"
```

## Inspect nested functions

```bash
color-math --file --parse tests/original/derivatives.md
```

## Run the tests

```bash
color-math --self-test
python -m tests.self_test
```

The files in [`tests/original/`](../tests/original/) are source notes, while
[`tests/expected/`](../tests/expected/) contains their expected colorized output.
