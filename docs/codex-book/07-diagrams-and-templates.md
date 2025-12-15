# Chapter 7 — Diagrams & templates (copy/paste friendly)

This chapter is the “poster” version: diagrams you can screenshot and templates you can reuse.

## 7.1 The full assembly pipeline (high-level)

```text
User submits message
  |
  v
TUI / SDK
  |-- UserInput::Text ------------------------------+
  |-- Detect "$skill" -> UserInput::Skill ---------+|
                                                   ||
                                                   vv
                                            Core engine
                                                   |
                                                   v
                                             Session init
                                                   |
    +--------------------------- record_initial_history --------------------------+
    |                                                                            |
    v                                                                            v
(maybe) DeveloperInstructions message                                        Conversation history
(maybe) UserInstructions message (config + AGENTS.md + skills index)               ^
(always) EnvironmentContext message                                               |
    |                                                                            |
    +---------------------------------- append ----------------------------------+
                                                   |
                                                   v
                                              run_task()
                                                   |
                                    +--------------+--------------+
                                    |                             |
                                    v                             v
                             record user input            build_skill_injections()
                                                           (read SKILL.md bodies)
                                                          -> ⟨skill⟩…⟨/skill⟩ msgs
                                    |                             |
                                    +--------------+--------------+
                                                   |
                                                   v
                                     get_history_for_prompt()
                                                   |
                                                   v
                              Turn input: Vec⟨ResponseItem⟩ (messages)
                                                   |
                                                   v
                                                run_turn
                                                   |
                                                   v
                                    Prompt { input, tools, ... }
                                      |        |         |
                                      |        |         +-> tools JSON
                                      |        +------------> input items
                                      +---------------------> instructions string
                                                   |
                                                   v
                                          Responses API request
                                                   |
                                                   v
                              Model output (assistant messages + tool calls)
                                                   |
                                                   v
                                         appended to history (loop)
```

## 7.2 The instruction stack (layer diagram)

```text
Top-level: instructions (single string)
  - Base instructions (prompt.md or model-specific)
  - Optional: apply-patch guidance (for some families)

Input stream: messages + tools (ordered items)
  [0] (optional) role=developer  -> config.developer_instructions
  [1] (optional) role=user       -> config.user_instructions + AGENTS.md + Skills index
  [2] (always)   role=user       -> environment context (cwd + sandbox + approvals + shell)
  [3]            role=user       -> the user's message (text/images)
  [4..] (opt)    role=user       -> skill body injections (⟨skill⟩…⟨/skill⟩)
  [...]          assistant/tool  -> normal conversation items
```

## 7.3 A precise template: what a request “looks like”

This is a **template**, not exact JSON; the repo evolves. The point is the structure.

### `instructions` template

```text
<BASE_INSTRUCTIONS>

(optional) <APPLY_PATCH_TOOL_INSTRUCTIONS>
```

Sources:

- `<BASE_INSTRUCTIONS>`: `codex-rs/core/prompt.md` or model-family variant
- `<APPLY_PATCH_TOOL_INSTRUCTIONS>`: appended only in a specific condition (see Chapter 2)

### `input` template

```text
[0] (optional) role=developer
    <config.developer_instructions>

[1] (optional) role=user
    # AGENTS.md instructions for <cwd>

    <INSTRUCTIONS>
    <config.user_instructions>

    --- project-doc ---

    <AGENTS.md concatenation (root→cwd)>

    ## Skills
    - <skill-name>: <skill-description> (file: /abs/path/to/SKILL.md)
    ...

    <skills usage rules block>
    </INSTRUCTIONS>

[2] (always) role=user
    <environment_context>
      <cwd>...</cwd>
      <approval_policy>...</approval_policy>
      <sandbox_mode>...</sandbox_mode>
      <network_access>...</network_access>
      <shell>...</shell>
    </environment_context>

[3] role=user
    <the user’s message text and/or image items>

[4..N] (optional) role=user
    <skill>
    <name>demo</name>
    <path>/abs/path/to/SKILL.md</path>
    ... full SKILL.md contents ...
    </skill>

[...] role=assistant / tool / tool_output
    <normal conversation items>
```

## 7.4 A reusable “prompt pack” template for repo authors

If you want to shape Codex behavior for a repo, these are your levers:

1. **`AGENTS.md`** (repo-local guidance): put conventions and workflows here.
2. **`AGENTS.override.md`** (developer-local override): per-machine tweaks.
3. **Skills** (`.codex/skills/**/SKILL.md` or `~/.codex/skills/**/SKILL.md`): workflows you only want expanded on demand.
4. **Config overrides**:
   - `developer_instructions`: strong, global steering
   - `user_instructions`: global “user message” steering
   - `base_instructions`: replace the base `instructions` prompt

A good pattern:

- Put invariant safety/process rules in `AGENTS.md`.
- Put heavy procedures in skills so they only load when invoked.
- Only override `base_instructions` when you truly need to replace the agent identity.
