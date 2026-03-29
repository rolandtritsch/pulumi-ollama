# Contributing

Contributions are welcome. Please follow the workflow below.

## Before you start

- Read [CLAUDE.md][] to understand the repo structure and how to verify changes.
- Open an issue first for non-trivial changes so the approach can be agreed on before implementation.

## Workflow

1. Fork the repo and create a branch from `trunk`.
2. Make your changes, keeping each source file under 400 lines.
3. Run a syntax check and Pulumi preview to verify nothing is broken (see [CLAUDE.md][]).
4. Open a pull request against `trunk` with a clear description of what changed and why.

## Code style

- Python only; no additional linters or formatters are required beyond what `uv` provides.
- Keep changes focused — one concern per PR.
- Do not commit `Pulumi.*.yaml` stack config files (they are gitignored).

## Reporting bugs

Open a GitHub issue with:

- What you expected to happen
- What actually happened
- The output of `pulumi preview` or `pulumi up` if relevant

[CLAUDE.md]: CLAUDE.md
