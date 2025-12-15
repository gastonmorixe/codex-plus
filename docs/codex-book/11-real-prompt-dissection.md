# Chapter 11 — Dissecting the real prompt (piece by piece)

This chapter takes the generated payload from Chapter 10 and explains each component like a lab specimen.

Files used:

- `docs/codex-book/examples/real-prompt-gpt-5.1-codex.json`
- `docs/codex-book/examples/real-prompt-gpt-5.1-codex.flattened.txt`

## 11.1 The “final system prompt” in Codex CLI

When people say “system prompt”, in this repo it effectively means:

1. The **base `instructions` string**, *plus*
2. The **startup prefix messages** in `input` (developer/user/env)

A useful ASCII mental model:

```text
                     FINAL "PROMPT" THE MODEL SEES

+-----------------------------------------------------------+
| instructions (string)                                     |
|  - base model family prompt                               |
|  - optional overrides                                     |
|  - optional appended apply_patch guidance (some families)  |
+-----------------------------------------------------------+
| input (ordered items)                                     |
|  [0] developer message (optional)                          |
|  [1] user_instructions message (AGENTS.md + skills index)  |
|  [2] environment_context message (sandbox + approvals)     |
|  [3] user message                                          |
|  [4] skill injections (if any)                             |
|  [...] transcript continues                                |
+-----------------------------------------------------------+
| tools (function/custom tools + MCP)                        |
+-----------------------------------------------------------+
```

In our generated payload, the “system-like” steering is split across:

- `instructions`
- `input[0]` (user instructions wrapper)
- `input[1]` (environment context)

## 11.2 `instructions`: the base identity and global rules

In the example payload:

- `instructions` is loaded from `codex-rs/core/gpt_5_codex_prompt.md`.

This file defines:

- search preferences (`rg`)
- editing constraints
- git hygiene constraints
- sandbox/approval semantics and how to request escalation
- how to format final answers

It is designed to be stable across repos.

## 11.3 `input[0]`: the user-instructions wrapper

In the example payload, `input[0]` is:

```text
# AGENTS.md instructions for /abs/path/to/repo

<INSTRUCTIONS>
...contents...
</INSTRUCTIONS>
```

Inside `<INSTRUCTIONS>` you will find:

- the repo’s `AGENTS.md` content
- then a `## Skills` section appended (because skills are enabled)

This is the repo saying: “here is how to behave *in this workspace*.”

## 11.4 The “skills index” vs “skill injection”

The example contains both skill representations:

### Skills index (metadata)

This lives inside the project docs wrapper as:

- a `## Skills` header
- a bullet list with `(file: /abs/path/to/SKILL.md)`
- a usage rules block

This keeps the model aware of what skills exist without paying token cost for full skill bodies.

### Skill injection (full body)

In the example payload, the user message includes:

- `$codex-book-git-hygiene`
- `$codex-book-linting`

So Codex injects full skill content as extra user messages:

- `input[3]` → `<skill> ... full SKILL.md ... </skill>`
- `input[4]` → `<skill> ... full SKILL.md ... </skill>`

This is the “progressive disclosure” mechanism.

## 11.5 `input[1]`: environment context

The environment context is an XML-ish structured message. In the example it contains:

- `cwd`
- `approval_policy`
- `sandbox_mode`
- `network_access`
- `shell`

This is not just documentation: it is how the model learns *what kind of tool requests are allowed*.

## 11.6 `tools`: the action surface (schemas matter)

The payload’s `tools` array defines what the model can call.

For `gpt-5.1-codex` defaults, the set is:

```text
shell_command
list_mcp_resources
list_mcp_resource_templates
read_mcp_resource
update_plan
apply_patch
view_image
```

Two critical prompt-engineering consequences:

1. **Naming stability matters**: prompts and habits form around tool names.
2. **Schema shape is steering**: parameters like `sandbox_permissions` and `justification` enforce safety/approval workflows.

## 11.7 The “agentic loop” emerges from these ingredients

With:

- a stable instruction layer
- a persistent prefix (`AGENTS.md` + environment)
- on-demand skill expansion
- structured tool schemas
- an orchestrator enforcing sandbox + approvals

…you get a loop that behaves like an agent, even though each model call is just a single request/response.
