# Chapter 6 — The final API payload shape (what the model receives)

This chapter describes the “final prompt” in the most literal way: **the JSON payload** Codex sends.

Codex builds an `ApiPrompt` that always has:

- `instructions`: a string
- `input`: an array of items
- `tools`: an array of tool specs

(Plus optional fields like `parallel_tool_calls` and output schema).

## 6.1 `instructions` (base instructions)

`instructions` is produced by:

- base prompt selection (model family)
- optional overrides (config + remote)
- optional appends (apply-patch guidance)

Implementation:

- `codex-rs/core/src/openai_models/model_family.rs`
- `codex-rs/core/src/client_common.rs` (`Prompt::get_full_instructions()`)

## 6.2 `input` (messages + tool items)

`input` is a sequence of `ResponseItem` values.

It includes, in order over time:

- Developer message (if configured)
- User instructions message (AGENTS.md + config + skills section)
- Environment context message
- User text/image messages
- Skill injection messages (full `SKILL.md` bodies), when present
- Assistant messages
- Tool call records
- Tool output records

A key detail: the engine deliberately distinguishes “special prefix messages” from ordinary user messages.
For example, user-instructions and skill-instruction messages are tagged with predictable prefixes so they can be identified and filtered in some contexts.

## 6.3 `tools` (the callable surface area)

Tools are provided as a JSON array.

- Built-in tools depend on feature flags and model family.
- MCP servers can add tools dynamically at runtime.

Tool availability matters as much as text instructions: many constraints (like sandboxing and approvals) are enforced by the tool layer rather than just by prose.

## 6.4 Putting it together: “what the model sees”

A useful mental picture:

- The model receives a stable policy layer (`instructions`)
- plus a chronological transcript layer (`input`)
- plus an action surface (`tools`)

Prompt engineering, in this repo, is largely about keeping those three layers consistent with each other.
