# Chapter 4 — Skills: discovery, listing, trigger, and injection

Skills are an **experimental** feature that adds “open-on-demand” instruction bundles.

There are two distinct places skills matter:

1. **Startup**: skills are *listed* (metadata only) inside the project docs blob.
2. **Per user message**: if a skill is mentioned/selected, the full `SKILL.md` body is loaded and injected.

## 4.1 Skill discovery (what counts as a skill?)

Skills are discovered by searching for files named exactly `SKILL.md` under skill roots.

### Roots

- User skills root: `<CODEX_HOME>/skills` (typically `~/.codex/skills`)
- Repo skills root: `<git-root>/.codex/skills`

The discovery logic is in `codex-rs/core/src/skills/loader.rs`.

### Traversal rules

- Recursive directory traversal
- Skips:
  - dotfiles / dot-directories (names starting with `.`)
  - symlinks

### Parsing rules

`SKILL.md` must start with YAML frontmatter delimited by `---` lines.

Required keys:

- `name`: non-empty, single line, max length enforced by code
- `description`: non-empty, single line, max length enforced by code

Implementation note: the repo’s user-facing docs in `docs/skills.md` describe older limits; the authoritative limits are in `codex-rs/core/src/skills/loader.rs`.

## 4.2 Startup: listing skills in “project docs”

If skills are enabled, Codex appends a `## Skills` section (metadata only) to the project-doc text.

- Rendering: `codex-rs/core/src/skills/render.rs`
- Merge into project docs: `codex-rs/core/src/project_doc.rs`

The rendered section includes:

- One bullet per skill: name + description + absolute file path
- A block of “usage rules” that tells the agent how to treat skills

Crucially, the skill body is **not** inlined at this stage.

## 4.3 Trigger: how `$skill` becomes a skill injection

### The protocol shape

The core engine only injects skill bodies when it sees a `UserInput::Skill { name, path }` item.

- Definition: `codex-rs/protocol/src/user_input.rs`
- Injection logic: `codex-rs/core/src/skills/injection.rs`

### The TUI bridge

The terminal UI turns plain text mentions into `UserInput::Skill` items.

In `codex-rs/tui/src/chatwidget.rs`, when a user submits text:

- It scans the message for occurrences of `"$" + skill.name`.
- For each match, it pushes a `UserInput::Skill { name, path }` into the outgoing item list.

So a message like:

```text
please use $demo for this
```

causes the UI to send both:

- `UserInput::Text { text: "please use $demo for this" }`
- `UserInput::Skill { name: "demo", path: /abs/path/to/SKILL.md }`

## 4.4 Injection: where the full skill body enters the model context

On every task run, core computes skill injections:

- It loads skills for the current cwd (cached): `SkillsManager::skills_for_cwd()`
- It calls `build_skill_injections(inputs, skills_outcome)`
- It reads the referenced `SKILL.md` file(s)
- It injects each one as a **separate user message** containing:

```xml
<skill>
<name>demo</name>
<path>/abs/path/to/SKILL.md</path>
... full markdown body ...
</skill>
```

This injection happens *after* the user message is recorded, and *before* the model turn is executed.

## 4.5 Prompt-engineering takeaway

Skills give you a two-stage prompt strategy:

- **Discovery/listing**: keep the model aware of available capabilities (metadata only).
- **On-demand expansion**: only pay token cost for a skill body when it’s explicitly referenced.

This is one of the repo’s primary “context hygiene” mechanisms.
