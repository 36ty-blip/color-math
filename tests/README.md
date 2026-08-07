# Tests

- `original/` contains unprocessed Markdown and LaTeX input.
- `expected/` contains the correct expected output.
- `generated/` contains committed visual output snapshots.
- `self_test.py` compares current conversion and committed `generated/` snapshots with `expected/` exactly, then checks round trips, idempotence, and byte-safe atomic I/O.
- Run the checks with `python -m tests.self_test` from the repository root.
- Refresh snapshots explicitly with `python -m tests.self_test --update-generated`.
