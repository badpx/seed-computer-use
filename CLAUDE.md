# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a desktop GUI automation agent powered by ByteDance's Volcengine Ark vision model (`doubao-seed-1-6-vision-250815`). It implements an agentic loop: screenshot → LLM call → parse action → execute via pyautogui → repeat until done. Code comments and README are in Chinese.

## Setup

```bash
# Copy and fill in your Volcengine API key
cp .env.example .env

# Create virtualenv and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Verify environment
python check_env.py
```

The only required configuration is `ARK_API_KEY` in `.env`. All other settings have defaults.

## Running

```bash
# Interactive REPL mode
python -m computer_use

# Single task mode
python -m computer_use "open the browser"

# With debug output (full context/screenshots logged)
python -m computer_use --verbose "click the Submit button"

# With skills from a custom directory
python -m computer_use --skills-dir ./my-skills "open the browser"

# Disable skills system
python -m computer_use --no-skills "click the button"
```

## Testing

```bash
# Run all tests
python -m unittest discover tests

# Run a single test file
python -m unittest tests.test_action_parser

# Run a single test method
python -m unittest tests.test_action_parser.TestActionParser.test_float_coordinates
```

No linter or formatter is configured.

## Architecture

The agent loop lives in `agent.py` (`ComputerUseAgent.run()`). Each step:

1. **Screenshot** (`screenshot.py`) — captures screen via pyautogui; optionally resizes via `SCREENSHOT_SIZE` config
2. **Build messages** (`agent.py:_build_request_messages`) — assembles: system prompt + all prior assistant turns + sliding window of recent N screenshots (default 5) + optional execution feedback
3. **LLM call** — Volcengine Ark SDK (`chat.completions.create`) with configurable thinking mode and reasoning effort
4. **Parse** (`action_parser.py:parse_action`) — extracts `Thought:` and `Action: func(args)` from the model output; has fallback extraction when the model doesn't follow the format
5. **Execute** (`action_executor.py:ActionExecutor.execute`) — translates actions to pyautogui calls; handles coordinate space conversion (relative 0-1000 scale vs pixel)
6. **Log** (`logging_utils.py:ContextLogger`) — writes JSONL events per task for debugging

### Key design decisions

**Coordinate spaces**: The model works in a 0–1000 normalized space (`relative` mode) or raw pixels (`pixel` mode), controlled by `COORDINATE_SPACE` env var. `action_executor.py` scales to real screen dimensions.

**Context management**: All assistant messages are retained across steps (so the model sees its full history), but only the most recent N screenshots are included in each request to limit token usage.

**Text input**: Single characters are typed directly; longer strings are pasted via clipboard (`pyperclip`) using platform-aware hotkeys (Cmd+V on macOS).

**Action format**: The model outputs `Thought: ...\nAction: action_name(param=value, ...)`. Coordinates use `<point>x y</point>` XML-like tags. The `finished` action terminates the loop.

### Skills system

Skills extend the agent with domain-specific capabilities using the Ark SDK's function-calling API for progressive disclosure:

- **Level 1 (always loaded)**: Skill `name` + `description` from `SKILL.md` frontmatter are sent as `tools` definitions in every API call — lightweight, no context cost
- **Level 2 (on demand)**: When the model calls a skill tool (`finish_reason == "tool_calls"`), the full `SKILL.md` body is injected as a tool result and the model is re-called
- The skill-loading sub-loop runs up to 5 rounds per step; exchanges are ephemeral (not stored in `assistant_history`)

**Skill directory structure:**
```
skills/                    # Default dir (SKILLS_DIR config)
  my-skill/
    SKILL.md               # Required: YAML frontmatter + markdown instructions
    extra-resources.md     # Optional: additional resources
```

**SKILL.md format:**
```yaml
---
name: my-skill
description: What this skill does and when to use it (shown to model as tool description)
---

## Instructions
Step-by-step guidance for the model...
```

### Module map

| Module | Role |
|--------|------|
| `cli.py` | Argument parsing, interactive/single-task modes |
| `config.py` | All configuration (env vars > `.env` > defaults) |
| `agent.py` | Orchestration loop |
| `action_parser.py` | LLM output → structured action dict |
| `action_executor.py` | Action dict → pyautogui calls |
| `screenshot.py` | Screen capture |
| `prompts.py` | System prompt templates |
| `skills.py` | Skill discovery, frontmatter parsing, tool generation |
| `logging_utils.py` | Per-task JSONL context logging |
| `compat.py` | Python version gate (3.8–3.13 only) |

### Supported actions

`click`/`left_single`, `left_double`, `right_single`, `hover`, `drag`, `hotkey`, `press`/`keydown`, `release`/`keyup`, `type`, `scroll`, `wait`, `finished`

## Key Configuration Variables

Set in `.env` or environment. See `.env.example` for all options.

| Variable | Default | Description |
|----------|---------|-------------|
| `ARK_API_KEY` | *(required)* | Volcengine API key |
| `ARK_MODEL` | `doubao-seed-1-6-vision-250815` | Model endpoint ID |
| `MAX_STEPS` | `20` | Max steps per task |
| `SCREENSHOT_HISTORY` | `5` | Rolling screenshot window |
| `COORDINATE_SPACE` | `relative` | `relative` (0-1000) or `pixel` |
| `SCREENSHOT_SIZE` | *(none)* | Max width/height for screenshots |
| `THINKING_MODE` | `enabled` | Thinking/reasoning mode |
| `NATURAL_SCROLL` | auto-detected | macOS natural scroll direction |
| `SKILLS_DIR` | `./skills` | Skills directory path |
| `ENABLE_SKILLS` | `true` | Enable/disable skills system |
