# Codex Book: Prompt Engineering in Codex CLI

This mini-book explains **how Codex CLI constructs the final prompt** sent to the model, with an emphasis on the exact layering used in the Rust implementation.

It is written as a set of short chapters you can read in order.

## Table of Contents

1. [Chapter 1 — What “the prompt” means here](01-what-is-the-prompt.md)
2. [Chapter 2 — The instruction stack (system vs developer vs user)](02-instruction-stack.md)
3. [Chapter 3 — Project docs (AGENTS.md) discovery & merge rules](03-project-docs-agents.md)
4. [Chapter 4 — Skills: discovery, listing, trigger, and injection](04-skills.md)
5. [Chapter 5 — One turn: from user input to `Prompt` to API request](05-turn-assembly.md)
6. [Chapter 6 — The final API payload shape (what the model receives)](06-api-payload.md)
7. [Chapter 7 — Diagrams & templates (copy/paste friendly)](07-diagrams-and-templates.md)
8. [Chapter 9 — The agenting loop (stream → tools → follow-up)](09-agent-loop.md)
9. [Chapter 10 — A real computed prompt payload (this repo)](10-real-prompt-example.md)
10. [Chapter 11 — Dissecting the real prompt (piece by piece)](11-real-prompt-dissection.md)
11. [Chapter 12 — ASCII architecture diagrams (quick intuition)](12-ascii-architecture.md)
12. [Appendix — Debugging & tests that lock behavior in](08-debugging-and-tests.md)

## Quick orientation (files to read in the codebase)

- Base instruction text (model-side `instructions` field):
  - `codex-rs/core/prompt.md`
  - `codex-rs/core/gpt_5_1_prompt.md`, `codex-rs/core/gpt_5_2_prompt.md`, etc.
  - `codex-rs/core/src/openai_models/model_family.rs`
  - `codex-rs/core/src/client_common.rs`
- Developer/user/environment “messages” injected into the `input` stream:
  - `codex-rs/core/src/codex.rs` (`build_initial_context`, `run_task`, `run_turn`)
  - `codex-rs/core/src/user_instructions.rs` (message wrappers)
- Project docs merge (AGENTS.md + overrides + byte budgets):
  - `codex-rs/core/src/project_doc.rs`
- Skills:
  - `codex-rs/core/src/skills/loader.rs` (parsing + discovery)
  - `codex-rs/core/src/skills/render.rs` (skills section appended to project docs)
  - `codex-rs/core/src/skills/injection.rs` (read `SKILL.md` bodies on demand)
  - `codex-rs/core/src/skills/manager.rs` (cache by cwd)
  - `codex-rs/tui/src/chatwidget.rs` (detect `$skill` mentions and emit `UserInput::Skill`)

## A note on “system prompt” terminology

Codex CLI uses the OpenAI Responses API concept of a top-level **`instructions`** string plus an **`input`** list of items. This book uses:

- **Base instructions**: the `instructions` string.
- **Developer instructions**: a `role: "developer"` message inserted into `input`.
- **User instructions** (project docs): a `role: "user"` message inserted into `input`.
- **Environment context**: a structured XML-ish message inserted into `input`.

## Render as a website (mdBook)

- **Install tools (pinned; avoids version warning)**: `just book-install`
- **Build once**: `just book-build`
- **Dev server**: `just book-serve --open` (serves `docs/codex-book/` on `http://localhost:3000`)
- **GitHub Pages**: `.github/workflows/codex-book-pages.yml` builds and deploys on pushes to `main`
