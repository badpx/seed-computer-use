# Repository Guidelines

## Project Structure & Module Organization
Core code lives in `computer_use/`. `agent.py` runs the screenshot -> model -> parse -> execute loop, `cli.py` exposes the REPL and one-shot entrypoints, `config.py` centralizes environment loading, and `skills.py` manages `SKILL.md` discovery. Tests live in `tests/` and mirror behavior by module (`test_cli.py`, `test_action_parser.py`). Built-in skills live under `skills/<skill-name>/SKILL.md`. Root scripts include `check_env.py` for setup verification and `function_calling.py` for local experiments.

## Build, Test, and Development Commands
Create an isolated environment before editing:

```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Use `python check_env.py` to validate Python version, dependencies, config, and screenshot support. Run the tool locally with `python -m computer_use` for interactive mode or `python -m computer_use "打开浏览器"` for a single task. Run tests with `python -m unittest discover tests`; narrow scope with `python -m unittest tests.test_action_parser`.

## Coding Style & Naming Conventions
Follow the existing Python style: 4-space indentation, `snake_case` for modules/functions/variables, and `PascalCase` for classes. Keep functions small and explicit; favor standard-library solutions before adding dependencies. No formatter or linter is configured, so match surrounding code closely and preserve the repo’s mixed Chinese user-facing text and concise docstrings. Name skills and skill directories descriptively, typically with kebab-case such as `skills/open-browser/`.

## Testing Guidelines
This project uses `unittest`. Add tests in `tests/test_*.py`, and name test methods `test_<behavior>`. Prefer isolated tests with mocks or fake modules for GUI, clipboard, and SDK interactions; existing CLI and executor tests are the model. Add regression coverage whenever you change action parsing, CLI flags, config precedence, or skill loading.

## Commit & Pull Request Guidelines
Recent history uses short, imperative commit subjects, often in Chinese, for example `修复drag事件解析处理错误`. Keep each commit focused on one behavior change. PRs should summarize the affected flow, list any new config or CLI flags, mention test coverage, and include screenshots or terminal snippets when output/logging changes.

## Security & Configuration Tips
Do not commit `.env`, API keys, screenshots, or JSONL logs. Use `ARK_API_KEY` via environment variables or a local `.env`, and sanitize any debugging artifacts before sharing them in a PR.
