# Contributing

Forge is an Apache 2.0 coding agent. Useful PRs add a provider, a QA detector,
a tool, or a permission/ignore rule — not an IDE and not a license change.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Use `git commit -s` (Developer Certificate of Origin).

From the OPEN FORGE menu, **contributions** can send a recommendation
(opens mail to dariopro.1212@gmail.com) or open this GitHub repo.
Same from the shell: `forge contribute recommend "your idea"` or
`forge contribute code`.
