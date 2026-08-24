# Forge

**An open-source AI coding agent for the terminal.**

Bring your own key. Or bring no key — Ollama and llama.cpp work out of the box.
After every edit, Forge runs **integrated QA** (tests, lint, compile) and sends
the failures back to the model until the suite is green.

Apache License 2.0. Not affiliated with OpenCode or Anthropic.

```
$ forge

  Forge  v0.1.0
  repo   ~/src/app
  model  ollama/qwen2.5-coder:7b
  mode   build    qa on

❯ fix the failing tests

  ▸ read_file {'path': 'src/add.py'}
  ▸ edit_file {'path': 'src/add.py', ...}
  QA: passed
      - pytest: pass (412ms)
```

## Install

Python 3.10+.

```bash
git clone https://github.com/DarioDGR12/Forge-Code.git
cd Forge-Code
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
forge --help
```

`forge` with no arguments opens the interactive agent. Same idea as Claude Code
or OpenCode: you stay in the repo, you talk, it reads and writes files.

## Bring your own key

Keys live in `~/.config/forge-code/credentials.json` (mode `600`).
They are never sent anywhere except the provider you chose.

```bash
forge auth login openai
forge auth login anthropic
forge auth login openrouter
forge auth login groq
forge auth status
```

Environment variables also work — useful in CI:

| Provider    | Variable             | Default endpoint                         |
| ----------- | -------------------- | ---------------------------------------- |
| OpenAI      | `OPENAI_API_KEY`     | `https://api.openai.com/v1`              |
| Anthropic   | `ANTHROPIC_API_KEY`  | `https://api.anthropic.com`              |
| OpenRouter  | `OPENROUTER_API_KEY` | `https://openrouter.ai/api/v1`           |
| Groq        | `GROQ_API_KEY`       | `https://api.groq.com/openai/v1`         |
| Custom      | `FORGE_API_KEY`      | `FORGE_BASE_URL` (any OpenAI-compatible) |

```bash
export OPENAI_API_KEY=sk-...
export FORGE_PROVIDER=openai
export FORGE_MODEL=gpt-4.1-mini
forge run "add a README section about install"
```

## Local models

No account required. Forge treats local runtimes as first-class providers.

**Ollama**

```bash
ollama pull qwen2.5-coder:7b
forge auth login ollama
# or:
export FORGE_PROVIDER=ollama
export FORGE_MODEL=qwen2.5-coder:7b
forge
```

**llama.cpp** (OpenAI-compatible server)

```bash
# example — your binary and GGUF may differ
./llama-server -m qwen2.5-coder-7b.gguf --port 8080

forge auth login llamacpp --base-url http://127.0.0.1:8080/v1
export FORGE_PROVIDER=llamacpp
export FORGE_MODEL=local
forge
```

**Any OpenAI-compatible proxy** (vLLM, LocalAI, LiteLLM, a company gateway):

```bash
forge auth login custom --base-url https://llm.internal.example/v1 --key "$TOKEN"
```

```bash
forge models     # probes Ollama + llama.cpp and the active remote provider
forge doctor     # keys, local runtimes, QA
```

## Integrated QA

This is the difference from “a chat that edits files.”

Forge detects the repo and runs the right suite:

| If it finds            | It runs                         |
| ---------------------- | ------------------------------- |
| `tests/test_*.py`, pytest | `python -m pytest -q`         |
| `package.json` `test`  | `npm test`                      |
| `package.json` `lint`  | `npm run lint`                  |
| `Cargo.toml`           | `cargo test`                    |
| `go.mod`               | `go test ./...`                 |
| Python without tests   | `python -m compileall`          |

After the agent writes or edits a file, QA runs automatically. Failures go back
into the conversation so the model can fix them. You can also run it yourself:

```bash
forge qa                 # standalone, exit 1 if red
# inside the REPL:
/qa
/qa off                  # disable auto-QA
/qa on
```

## Commands

| Command | What it does |
| --- | --- |
| `forge` | Interactive agent (REPL) |
| `forge run "task"` | One shot, then exit |
| `forge run "task" --json` | Machine-readable result |
| `forge auth login <provider>` | BYOK |
| `forge auth status` | Which keys / local endpoints are set |
| `forge models` | Local + remote model list |
| `forge qa` | Run the detected suite |
| `forge init` | Write `AGENTS.md` |
| `forge doctor` | Health check |

Inside the REPL:

`/help` `/status` `/model NAME` `/provider NAME` `/mode build\|plan` `/qa` `/init` `/clear` `/exit`

**plan** mode is read-only: the agent can look around, not edit or run shell.
**build** mode is the default.

## Tools the agent can use

`read_file` `write_file` `edit_file` `list_dir` `glob` `grep` `bash`

Paths are jailed to the workspace. `.env`, credentials, and `..` are blocked
by the file tools. `bash` runs with `cwd` set to the repo (same trust model as
Claude Code / OpenCode: you are running an agent on your machine).

## Project memory

`forge init` writes `AGENTS.md`. Forge also reads `FORGE.md` and
`.forge/AGENTS.md` if present. Put test commands, style rules, and “do not
touch” paths there.

Config lives at `~/.config/forge-code/config.json`:

```json
{
  "provider": "ollama",
  "model": "qwen2.5-coder:7b",
  "mode": "build",
  "qa": { "auto": true, "timeout": 120 }
}
```

## Quick demo (no API key)

```bash
pip install -e ".[dev]"
forge qa --repo examples/broken-add    # red: add() is wrong
# Point Forge at any OpenAI-compatible model, then:
forge run "Make add() return the sum" --repo examples/broken-add
forge qa --repo examples/broken-add    # green
```

## Why this exists

Closed coding CLIs are products. Forge is a **small Apache-2.0 agent** you can
run on-prem with *your* endpoint or a GGUF on disk. Companies keep the keys.
Contributors add providers, QA detectors, and tools.

## License

[Apache License 2.0](LICENSE)

Forge-Code is an independent project. “OpenCode” is a trademark of its
respective owners. “Claude” is a trademark of Anthropic.
