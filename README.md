# Forge

**An open-source AI coding agent for the terminal.**

Bring your own key. Or bring no key — Ollama and llama.cpp work out of the box.
After every edit, Forge runs **integrated QA** and feeds failures back to the
model until the suite is green.

Apache License 2.0 · v0.3.0  
Not affiliated with OpenCode or Anthropic.

```
$ forge

  Forge  v0.3.0
  session  a1b2c3d4e5f6
  repo     ~/src/app
  model    ollama/qwen2.5-coder:7b
  mode     build    qa on    bash allow

❯ fix the failing tests

  ▸ read_file src/add.py
  ▸ edit_file src/add.py
  QA: passed · pytest 412ms
  1,204 tokens (980 in / 224 out)
```

## Install

Python 3.10+.

```bash
git clone https://github.com/DarioDGR12/Forge-Code.git
cd Forge-Code
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
forge --help
```

`forge` with no arguments opens the interactive agent.

## Bring your own key

Keys live in `~/.config/forge-code/credentials.json` (mode `600`).
They only go to the provider you chose.

```bash
forge auth login openai
forge auth login anthropic
forge auth login openrouter
forge auth login groq
forge auth status
```

| Provider   | Variable             | Default endpoint                         |
| ---------- | -------------------- | ---------------------------------------- |
| OpenAI     | `OPENAI_API_KEY`     | `https://api.openai.com/v1`              |
| Anthropic  | `ANTHROPIC_API_KEY`  | `https://api.anthropic.com`              |
| OpenRouter | `OPENROUTER_API_KEY` | `https://openrouter.ai/api/v1`           |
| Groq       | `GROQ_API_KEY`       | `https://api.groq.com/openai/v1`         |
| Custom     | `FORGE_API_KEY`      | `FORGE_BASE_URL` (any OpenAI-compatible) |

```bash
export OPENAI_API_KEY=sk-...
export FORGE_PROVIDER=openai
export FORGE_MODEL=gpt-4.1-mini
forge run "add an install section to the README"
```

## Local models

**Ollama**

```bash
ollama pull qwen2.5-coder:7b
forge auth login ollama
export FORGE_PROVIDER=ollama
export FORGE_MODEL=qwen2.5-coder:7b
forge
```

**llama.cpp** (OpenAI-compatible server)

```bash
./llama-server -m qwen2.5-coder-7b.gguf --port 8080
forge auth login llamacpp --base-url http://127.0.0.1:8080/v1
```

**Company gateway / vLLM / LocalAI / LiteLLM**

```bash
forge auth login custom --base-url https://llm.internal.example/v1 --key "$TOKEN"
```

```bash
forge models
forge doctor
```

## Integrated QA

After the agent writes or edits a file, Forge detects the repo and runs:

| If it finds                 | It runs                 |
| --------------------------- | ----------------------- |
| pytest / `tests/test_*.py`  | `python -m pytest -q`   |
| `package.json` `test`/`lint`| `npm test` / `npm lint` |
| `Cargo.toml`                | `cargo test`            |
| `go.mod`                    | `go test ./...`         |
| `ruff.toml`                 | `ruff check`            |
| `[tool.mypy]`               | `mypy .`                |
| `Makefile` `test:`          | `make test`             |
| Python without tests        | `compileall`            |

Failures go back into the conversation. Standalone:

```bash
forge qa
# inside the REPL:
/qa
/qa off
```

Pin extra checks in `.forge/config.json`:

```json
{ "qa": { "auto": true, "timeout": 120, "extra": ["npm run typecheck"] } }
```

## Safety

- Paths are jailed to the workspace
- `.env`, keys, and credential filenames cannot be read or written
- `.forgeignore` + `.gitignore` hide vendor and secret trees from search
- Destructive bash (`rm -rf /`, `mkfs`, `curl | sh`, …) is rejected
- **plan** mode is read-only
- `/bash ask` prompts before each shell command (`FORGE_YES=1` auto-approves in CI)
- `/undo` and `forge undo` restore the last turn (git snapshot when possible)
- Ctrl+C cancels the current model/tool loop
- After edits, Forge runs language diagnostics (pyright/ruff, tsc, go vet) when those tools exist

## Commands

| Command | What it does |
| --- | --- |
| `forge` | Interactive agent (REPL) |
| `forge --resume ID` | Continue a saved session |
| `forge run "task"` | One shot |
| `forge run "task" --json` | Machine-readable result |
| `forge auth login <p>` | BYOK |
| `forge models` | Local + remote models |
| `forge qa` | Run the detected suite |
| `forge sessions` | List saved conversations |
| `forge sessions export ID` | Write a markdown transcript |
| `forge tools` | List agent tools |
| `forge init` | Write `AGENTS.md` |
| `forge doctor` | Health check |
| `forge undo` | Revert the last agent edits |
| `forge ci --task "…"` | CI / GitHub Actions (sets `FORGE_YES=1`) |

REPL: `/help` `/status` `/tools` `/model` `/provider` `/mode` `/qa` `/compact` `/cost` `/undo` `/bash` `/sessions` `/export` `/clear` `/exit`

Multiline: end a line with `\` and keep typing. Tab completes slash commands.

## Tools

`read_file` `write_file` `edit_file` `apply_patch` `list_dir` `tree` `glob` `grep` `bash` `git_status` `git_diff` `git_log` `todo_write` `todo_read`

## MCP

Add stdio MCP servers in `.forge/config.json`. Each server’s tools show up as `mcp_<name>_<tool>`.

```json
{
  "mcp": {
    "files": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    }
  }
}
```

## GitHub Actions

```yaml
- uses: actions/checkout@v4
- uses: ./.github/actions/forge
  with:
    task: "fix the failing tests"
    provider: openai
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

Or `forge ci --task "…"` with `FORGE_YES=1`. A `/forge …` issue comment can drive the example workflow.

## Project files

| File | Purpose |
| --- | --- |
| `AGENTS.md` / `FORGE.md` | Instructions injected every turn |
| `.forgeignore` | Hide paths from glob/grep/tree |
| `.forge/config.json` | Repo overlay (provider, QA, permissions) |
| `~/.config/forge-code/` | User config + credentials |

## Quick demo (no API)

```bash
pip install -e ".[dev]"
pytest
forge qa --repo examples/broken-add    # red on purpose
```

## License

[Apache License 2.0](LICENSE)
