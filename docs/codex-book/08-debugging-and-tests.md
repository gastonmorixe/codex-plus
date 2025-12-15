# Appendix — Debugging & tests that lock behavior in

The fastest way to understand prompt assembly is to read the tests that assert the request payload.

## A.1 Prompt assembly invariants

### Tool and instruction stability

`codex-rs/core/tests/suite/prompt_caching.rs` asserts that:

- The `instructions` string matches expected base prompt behavior.
- The tool list is stable and consistent across requests.

This matters because model performance depends on stable tool availability and stable base instructions.

### Skill injection appears in user input

`codex-rs/core/tests/suite/skills.rs` asserts that when a `UserInput::Skill` item is provided, the request includes a `<skill>...</skill>` user message containing the full `SKILL.md` body.

## A.2 Practical debugging tips

- Inspect how the TUI turns `$skill` text into `UserInput::Skill`:
  - `codex-rs/tui/src/chatwidget.rs`
- Inspect where skill injection happens relative to user messages:
  - `codex-rs/core/src/codex.rs` (`run_task`)
- Inspect how base instructions are chosen:
  - `codex-rs/core/src/openai_models/model_family.rs`
- Inspect the exact message wrappers for user-instructions and skill-instructions:
  - `codex-rs/core/src/user_instructions.rs`

## A.3 A note about documentation drift

Skills are explicitly marked experimental, and some user-facing docs may drift from implementation (for example: field length limits).

When in doubt:

- Treat `codex-rs/core/src/skills/loader.rs` as the source of truth for parsing/validation.
- Treat `codex-rs/tui/src/chatwidget.rs` as the source of truth for how `$skill` triggers injection.
