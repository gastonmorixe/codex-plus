# Chapter 1 — What “the prompt” means here

When people say “the prompt”, they often mean a single string. In Codex CLI, the model receives **two different prompt channels**:

1. A top-level **`instructions`** string (sometimes called system prompt).
2. An **`input`** list of structured items (messages, tool calls, tool outputs, etc.).

This is not an abstraction: it mirrors the OpenAI Responses API payload Codex builds.

## The two prompt channels

### 1) `instructions` (base instructions)

This is selected from:

- A built-in prompt file, such as `codex-rs/core/prompt.md`, or a model-specific variant.
- Optional overrides (local config overrides or remote model metadata overrides).
- Optional post-processing: some model families append extra apply-patch guidance.

In the code, this string is produced by `Prompt::get_full_instructions()` in `codex-rs/core/src/client_common.rs`.

### 2) `input` (conversation + injected context)

This is where Codex places:

- Developer instructions (if configured)
- User instructions (project docs merged from AGENTS.md + config + skills “index”)
- Environment context (sandbox + approval + cwd + shell)
- The actual user message(s)
- Optional skill body injections (the full `SKILL.md` contents), when skills are referenced
- The rest of the conversation history (assistant messages, tool calls, tool outputs)

The `input` list is built from the in-memory history plus per-turn items.

## Why this matters for “prompt engineering”

Prompt engineering in this repo is about **controlling the composition** of both channels:

- **Stable invariant rules** go into `instructions`.
- **Runtime session rules** (workspace conventions, policies, repo-specific norms) go into injected messages inside `input`.
- **Ephemeral turn-specific context** (the exact user message, skill bodies, tool results) is appended at the end of `input`.

This separation is the core design: it keeps global constraints stable while allowing flexible, user- and repo-specific behavior.
