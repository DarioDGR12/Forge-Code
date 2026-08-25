# Forge-Code

This repository is the Forge CLI itself.

## Verify

```bash
pip install -e ".[dev]"
pytest
forge --help
```

## Rules

- Keep the kernel small. New languages, sandboxes, and vendors are drivers.
- Do not add an IDE, a hosted SaaS, or a license change.
- Never commit API keys or `.env` files.
- Prefer tests that do not need a live model (`complete_fn` fakes, recipe-style).
