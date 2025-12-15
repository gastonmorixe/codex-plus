# Chapter 5 — One turn: from user input to `Prompt` to API request

This chapter follows the code path for a single user submission.

There are two distinct lifecycles:

- **Session initialization** (one-time): injects developer/user/env context into history.
- **Task execution** (per user submission): records the user message, injects skill bodies, then runs a model/tool loop.

## 5.1 Session initialization: seeding the “prefix”

When a new session starts, Codex records a small, stable prefix into history:

- Developer instructions (optional)
- User instructions (optional; includes AGENTS.md and skills section)
- Environment context (always)

This happens via `Session::record_initial_history()` → `Session::build_initial_context()` in `codex-rs/core/src/codex.rs`.

From this point on, every model request includes that prefix because it is part of conversation history.

## 5.2 User submission: inputs and skill injections

When the user submits, core runs `run_task(sess, turn_context, input, ...)`.

Key steps (in `codex-rs/core/src/codex.rs`):

1. Load skills for current cwd (if enabled)
2. Build skill injections from the input items
3. Record the user’s input into conversation history
4. Record skill injection messages (if any)

The important ordering:

- User text message is recorded first.
- Skill bodies are recorded next as separate user messages.

## 5.3 Construct the model `Prompt`

Each loop iteration constructs a `Prompt` (from `codex-rs/core/src/client_common.rs`):

- `input`: the current history slice used for prompting
- `tools`: tool specs from `ToolRouter` (built-ins + MCP)
- `parallel_tool_calls`: enabled only if both model and feature flags allow it
- `base_instructions_override`: from `turn_context.base_instructions`
- `output_schema`: optional schema for structured output

This happens in `run_turn()` in `codex-rs/core/src/codex.rs`.

## 5.4 Convert `Prompt` into the API payload

The model client ultimately creates an API payload:

- `instructions`: `prompt.get_full_instructions(model_family)`
- `input`: `prompt.get_formatted_input()`
- `tools`: JSON schema for tools

The wrapper used depends on which API mode is configured, but the conceptual shape is the same.

## 5.5 The tool loop and conversation growth

Once the request is sent, the response can include:

- Assistant messages
- Tool calls
- Tool outputs

Codex records these items into history, and the loop continues until the agent finishes the task.

Prompt engineering impact:

- The prefix (developer/user/env) is sticky across turns.
- Tool outputs and assistant messages are appended and can be compacted later.
- Skill bodies are injected per message and persist in history like any other user message.
