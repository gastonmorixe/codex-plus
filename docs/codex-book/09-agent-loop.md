# Chapter 9 — The agenting loop (stream → tools → follow-up)

This chapter explains *how Codex turns a single user submission into an agentic loop*.

The core idea:

- A **task** can take multiple **turns**.
- Each turn sends a request to the model.
- The model can emit tool calls.
- Codex executes tools and feeds tool outputs back into the conversation.
- The loop repeats until the model produces a final assistant message with no more follow-up work.

## 9.1 The control loop at a glance (ASCII)

```text
UserInput items
  |
  v
run_task()
  |
  |-- record user message (history)
  |-- (optional) inject <skill> messages (history)
  |
  v
loop {
  build prompt input from history
  |
  v
  stream request to model
    |
    |-- response items arrive over SSE
    |
    |-- when an item completes:
    |     - record it immediately to history
    |     - if it's a tool call: schedule tool execution
    |
    |-- wait for any in-flight tool execution(s)
    |
    |-- record tool outputs to history
    |
    v
  if no follow-up needed: break
}
```

In the code, the important “where it happens” pieces are:

- `codex-rs/core/src/codex.rs`: `run_task()`, `run_turn()`, `try_run_turn()`
- `codex-rs/core/src/stream_events_utils.rs`: converts completed stream items into either:
  - a scheduled tool future, or
  - a completed UI-visible message
- `codex-rs/core/src/tools/router.rs`: turns a `ResponseItem` into an internal `ToolCall` and dispatches it
- `codex-rs/core/src/tools/parallel.rs`: concurrency gates for tool execution
- `codex-rs/core/src/tools/orchestrator.rs`: approvals + sandbox selection + retry rules

## 9.2 Streaming and item handling (why “record immediately” matters)

Codex consumes a streaming response from the model and processes **completed output items** one by one.

When an item completes, Codex:

- **records it immediately** into conversation history (so the transcript is coherent even if the turn is cancelled)
- decides whether it is:
  - a **tool call** → schedule execution and mark `needs_follow_up = true`
  - a **non-tool message** (assistant message, reasoning, web search call) → complete the turn item

This logic is centralized in `codex-rs/core/src/stream_events_utils.rs`.

## 9.3 Tool scheduling and parallelism (selective)

Codex supports parallel tool execution, but *only* when:

- The model family says it supports parallel tool calls, AND
- The feature flag `ParallelToolCalls` is enabled, AND
- The tool itself is marked as parallel-safe.

Even then, Codex gates parallelism *per tool invocation type*:

- Parallel-safe tools take a **read lock**.
- Non-parallel tools take a **write lock**.

So a single non-parallel tool call will serialize other tool calls until it finishes.

Implementation: `codex-rs/core/src/tools/parallel.rs`.

## 9.4 Tool dispatch (what counts as a tool call?)

A model output item becomes an executable tool call if it is one of:

- `ResponseItem::FunctionCall` (ordinary tool)
- `ResponseItem::CustomToolCall` (freeform tool, like freeform `apply_patch`)
- `ResponseItem::LocalShellCall` (legacy/local-shell pathway)

The “conversion” happens in `ToolRouter::build_tool_call()` (`codex-rs/core/src/tools/router.rs`).

## 9.5 Approvals + sandboxing: the orchestrator

Tools that mutate the system or require elevated permissions are mediated by a common orchestrator:

- Determine whether an approval is needed.
- If needed, request it.
- Run in the selected sandbox.
- If denied by sandbox and escalation is allowed by policy, optionally ask approval and retry without sandbox.

Implementation: `codex-rs/core/src/tools/orchestrator.rs`.

## 9.6 The most important emergent property

The “agent” is not a single prompt.

It is:

- a stable base instruction string (`instructions`), plus
- a growing transcript (`input`), plus
- a dynamic tool surface (`tools`), plus
- an execution policy enforced by the orchestrator.

That’s why prompt engineering in this repo is as much about **tool design and policy** as it is about text.
