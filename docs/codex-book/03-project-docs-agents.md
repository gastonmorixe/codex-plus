# Chapter 3 — Project docs (AGENTS.md) discovery & merge rules

Project docs are the repo’s way to tell the agent “how to behave here.” In this codebase, project docs are primarily stored in files named `AGENTS.md`.

## Discovery algorithm

The discovery is implemented in `codex-rs/core/src/project_doc.rs`.

At a high level:

1. Start at `config.cwd`.
2. Walk upward until a git root is detected (`.git` file or directory), and stop there.
3. Collect documentation files from the git root down to the cwd.

The result is an ordered list of doc files (root → cwd), concatenated in that order.

## Filename precedence and fallbacks

For each directory in the chain, the code tries candidates in this order:

1. `AGENTS.override.md` (local override)
2. `AGENTS.md` (default)
3. Any `project_doc_fallback_filenames` from config

Only the first file found in that directory is taken (then it moves to the next directory).

## Byte budget and truncation

Project docs have a global byte budget:

- `config.project_doc_max_bytes`

If the combined docs exceed this budget, later files are truncated (and a warning is logged). If the budget is `0`, project docs are disabled.

This matters for prompt engineering because it is a *hard cap* on how much repo guidance can be injected into the model.

## Merge with user-instructions and skills

The final “user instructions” string is built by `get_user_instructions(config, skills)`.

It concatenates, in this order:

1. `config.user_instructions` (if any)
2. A separator if both parts exist: `\n\n--- project-doc ---\n\n`
3. The concatenated project docs (if any)
4. The rendered “## Skills” section (if enabled and any skills exist)

Then this merged blob is wrapped into the special `UserInstructions` message format (see Chapter 2).

## Why AGENTS.md is *not* base instructions

AGENTS.md is injected as a user message (not appended into `instructions`) so that:

- Base instructions remain stable across projects.
- Repo guidance remains visible and attributable (“this repo says…”) in conversation history.
- The system can limit AGENTS.md size without modifying the base prompt.

In other words: base instructions describe the *agent*, while AGENTS.md describes the *workspace*.
