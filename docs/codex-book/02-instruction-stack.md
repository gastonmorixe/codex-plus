# Chapter 2 — The instruction stack (system vs developer vs user)

Codex CLI layers instructions in multiple places. The critical implementation detail is: **base instructions are a string**, while developer/user instructions are **messages**.

## Layer 0: Base instructions (`instructions`)

A model request always includes an `instructions` string, chosen via the model family.

- Default base instructions: `codex-rs/core/prompt.md`
- Model-specific base instructions: `codex-rs/core/gpt_5_1_prompt.md`, `codex-rs/core/gpt_5_2_prompt.md`, etc.
- Selection logic: `codex-rs/core/src/openai_models/model_family.rs`

### Optional override: `base_instructions_override`

Each turn constructs a `Prompt { base_instructions_override: turn_context.base_instructions.clone(), ... }`.

- Source: `turn_context.base_instructions` is set from config at session initialization.
- Use: `Prompt::get_full_instructions()` uses this override when present.

This is how a user can replace the built-in prompt without rebuilding the binary.

### Optional append: apply-patch instructions for some families

`Prompt::get_full_instructions()` may append `codex_apply_patch::APPLY_PATCH_TOOL_INSTRUCTIONS` only when:

- There is **no** `base_instructions_override`, AND
- The model family is marked `needs_special_apply_patch_instructions`, AND
- No `apply_patch` tool is present in the tool list.

This is implemented in `codex-rs/core/src/client_common.rs`.

## Layer 1: Developer instructions (`role: developer` message)

If `config.developer_instructions` is set, the session records a developer message into history at startup.

- Wrapper type: `DeveloperInstructions` in `codex-rs/core/src/user_instructions.rs`
- Injection site: `Session::build_initial_context()` in `codex-rs/core/src/codex.rs`

This is a **separate message**, not concatenated into base instructions.

## Layer 2: User instructions (`role: user` message)

Codex merges:

- `config.user_instructions` (optional)
- “project docs” (AGENTS.md chain, optional)
- a “Skills” section (optional, metadata only)

into a single string, then injects it as a special user message at startup.

- Merge logic: `get_user_instructions()` in `codex-rs/core/src/project_doc.rs`
- Wrapper type: `UserInstructions` in `codex-rs/core/src/user_instructions.rs`
- Injection site: `Session::build_initial_context()` in `codex-rs/core/src/codex.rs`

This message is formatted as:

```text
# AGENTS.md instructions for <cwd>

<INSTRUCTIONS>
<merged instructions text>
</INSTRUCTIONS>
```

## Layer 3: Environment context (`<environment_context>...`)

Codex always injects an environment context message at startup.

It contains the session’s working directory and execution policy context (approval mode, sandbox mode, network mode, shell selection, etc.).

- Injection site: `Session::build_initial_context()` in `codex-rs/core/src/codex.rs`

This gives the model a structured summary of what it can and cannot do.

## Layering principle (the “stack”)

In first-turn order, the model sees:

1. `instructions` string (base)
2. `input[0]`: developer message (optional)
3. `input[1]`: user instructions message (optional)
4. `input[2]`: environment context message (always)
5. `input[...]`: user message + any skill injections + conversation history

The rest of the book explains where each layer comes from and how it’s kept stable.
