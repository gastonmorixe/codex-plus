# Chapter 10 — A real computed prompt payload (this repo)

This chapter contains an **actual, concrete prompt payload** computed from this repository’s code and docs.

It is intentionally written to be copy/paste readable and easy to audit.

## 10.1 What was computed

We generated a single request payload example with:

- **Model**: `gpt-5.1-codex`
- **CWD**: `/abs/path/to/repo`
- **Skills**: enabled (demo skills live under `.codex/skills/`)
- **Tools**: the default built-in toolset for this model family (no extra MCP tools)
- **Environment context**: example values `approval_policy=on-failure`, `sandbox_mode=workspace-write`, `network_access=restricted`, `shell=zsh`

Outputs:

- Full JSON payload: `docs/codex-book/examples/real-prompt-gpt-5.1-codex.json`
- Flattened single-scroll view: `docs/codex-book/examples/real-prompt-gpt-5.1-codex.flattened.txt`

The JSON includes:

- `instructions`: the full base instruction string (from `codex-rs/core/gpt_5_codex_prompt.md`)
- `input`: the injected context messages + a sample user message + skill injections
- `tools`: full tool specs (including the `apply_patch` Lark grammar)

## 10.2 How to read it

Start with the flattened view:

- `docs/codex-book/examples/real-prompt-gpt-5.1-codex.flattened.txt`

It shows, in order:

- `instructions`
- `input[0]` user instructions wrapper (`AGENTS.md` + skills index)
- `input[1]` environment context XML
- `input[2]` user message
- `input[3..]` skill injections (`<skill>...</skill>`)
- tool names

Then open the full JSON:

- `docs/codex-book/examples/real-prompt-gpt-5.1-codex.json`

## 10.3 Why this is “real” (and what’s still variable)

This payload is “real” in the sense that it is built from:

- the actual base prompt file and project docs in this repo
- the real tool schemas encoded in `codex-rs/core/src/tools/spec.rs`
- the real skill formatting (`## Skills` section and `<skill>...</skill>` wrapper)

But in production, some elements are inherently runtime-variable:

- MCP tools/resources (if configured)
- remote model overrides (if enabled)
- the real sandbox policy / approval policy chosen by the user
- the user’s actual shell and writable roots

The computed example is best understood as a **fully expanded template instance**.
