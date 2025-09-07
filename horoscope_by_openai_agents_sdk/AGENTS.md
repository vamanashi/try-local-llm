# Repository Guidelines

## Project Structure & Module Organization
- `main.py`: Async CLI entrypoint. Starts chat loop and streams responses.
- `agent.py`: `HoroscopeAgent` wiring (Agents SDK model, tools, instructions).
- `tools.py`: Tool functions exposed to the agent via `@function_tool`.
- `history.py`: Lightweight stream/event formatting for console output.
- `local_tracing.py`: Local JSONL + Markdown tracing into `logs/`.
- `instruction.txt`: System/developer instructions (Japanese) for the agent.
- `references/`: Notes and docs; not imported at runtime.
- `logs/`: Generated traces and runs. Do not commit.

## Build, Test, and Development Commands
- Setup (Python 3.10+ recommended):
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -U pip && pip install openai agents pydantic`
- Run locally:
  - `python main.py`
  - Requires an OpenAI‑compatible server at `http://localhost:1234/v1` (e.g., LM Studio) and model `openai/gpt-oss-20b`.
- Traces:
  - Outputs JSONL to `logs/agents_traces.jsonl` and per‑run Markdown files in `logs/`.

## Coding Style & Naming Conventions
- Python: 4‑space indentation, type hints, concise docstrings on public functions.
- Naming: `snake_case` for files/functions, `PascalCase` for classes, module‑level constants in `UPPER_SNAKE_CASE`.
- Tools: keep `@function_tool` functions pure, typed, and fast; return user‑facing Japanese strings.
- Keep user‑visible responses in Japanese (see `instruction.txt`).

## Testing Guidelines
- Framework: `pytest` (add `tests/` as needed).
- Naming: `tests/test_*.py`; one behavior per test; prefer deterministic tool tests and `AgentHistory` formatting tests.
- Run: `pytest -q` (consider `pytest -k tools` while iterating).

## Commit & Pull Request Guidelines
- Commits: short, present tense; English or Japanese OK. Examples: `Add streaming output`, `tools: fix zodiac format`.
- PRs: include summary, reproduction steps, screenshots/log excerpts, and linked issue. Note changes to model/server config.

## Security & Configuration Tips
- Secrets: do not commit keys. This repo defaults to local server (`DEFAULT_BASE_URL`/`DEFAULT_MODEL` in `agent.py`). Adjust there if required.
- Logs may contain model I/O; avoid committing `logs/`.

## Instructions
- 日本語で簡潔かつ丁寧に回答してください。
