# Chapter 12 — ASCII architecture diagrams (quick intuition)

This chapter is intentionally visual.

## 12.1 Prompt assembly layers

```text
                      +---------------------------+
                      | base instructions         |
                      | (instructions string)     |
                      +-------------+-------------+
                                    |
                                    v
+------------------+      +------------------------+      +-------------------+
| AGENTS.md chain  | ---> | user instructions text | ---> | input[0] message  |
| + skills index   |      | (wrapped)              |      | (role=user)       |
+------------------+      +------------------------+      +-------------------+

+------------------+                                       +-------------------+
| sandbox + policy  | -----------------------------------> | input[1] message  |
| + shell + cwd     |                                       | env_context XML   |
+------------------+                                       +-------------------+

+------------------+                                       +-------------------+
| user text/images  | -----------------------------------> | input[2] message  |
+------------------+                                       +-------------------+

+------------------+                                       +-------------------+
| skill bodies      | -----------------------------------> | input[3..]        |
| (only when used)  |                                       | <skill>...</skill>|
+------------------+                                       +-------------------+

+------------------+
| tools list (JSON) |
| + MCP tools        |
+------------------+
```

## 12.2 The agent loop

```text
              +-------------------------------+
              | submit user input             |
              +---------------+---------------+
                              |
                              v
              +-------------------------------+
              | record user message           |
              | record skill injections       |
              +---------------+---------------+
                              |
                              v
        +---------------------+----------------------+
        | build Prompt: instructions + input + tools |
        +---------------------+----------------------+
                              |
                              v
              +-------------------------------+
              | stream model response         |
              +---------------+---------------+
                              |
                              v
              +-------------------------------+
              | output item done?             |
              +---------------+---------------+
                              |
               +--------------+--------------+
               |                             |
               v                             v
     +-------------------+         +------------------------+
     | it's a tool call  |         | it's a normal message   |
     | schedule tool     |         | record message          |
     | needs_follow_up=1 |         | needs_follow_up maybe 0 |
     +---------+---------+         +-----------+------------+
               |                               |
               v                               v
     +-------------------+         +------------------------+
     | run tool (policy) |         | if no follow-up: DONE  |
     | - approvals        |
     | - sandbox           |
     | - maybe retry       |
     +---------+---------+
               |
               v
     +-------------------+
     | record tool output |
     +---------+---------+
               |
               v
     +-------------------+
     | next turn          |
     +-------------------+
```

## 12.3 Where each piece lives (cheat sheet)

```text
Base instructions:
  codex-rs/core/*prompt*.md
  codex-rs/core/src/openai_models/model_family.rs

User instructions (AGENTS + skills index):
  codex-rs/core/src/project_doc.rs
  codex-rs/core/src/user_instructions.rs
  codex-rs/core/src/skills/render.rs

Skill injection (full bodies):
  codex-rs/tui/src/chatwidget.rs        (detect $skill)
  codex-rs/core/src/skills/injection.rs (read SKILL.md)
  codex-rs/core/src/codex.rs            (record injections)

Tools list + schemas:
  codex-rs/core/src/tools/spec.rs

Agent loop:
  codex-rs/core/src/codex.rs
  codex-rs/core/src/stream_events_utils.rs
  codex-rs/core/src/tools/router.rs
  codex-rs/core/src/tools/parallel.rs
  codex-rs/core/src/tools/orchestrator.rs
```
