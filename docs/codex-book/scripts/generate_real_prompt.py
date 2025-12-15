#!/usr/bin/env python3
"""Generate a concrete example of Codex CLI prompt assembly.

This script intentionally produces a *static* example for the current repo:
- Model: gpt-5.1-codex
- Features: defaults + skills enabled
- Tools: derived from codex-core ToolsConfig/build_specs rules (replicated here)

It writes:
- docs/codex-book/examples/real-prompt-gpt-5.1-codex.json
- docs/codex-book/examples/real-prompt-gpt-5.1-codex.flattened.txt
- docs/codex-book/examples/real-prompt-gpt-5.1-codex.sanitized.json
- docs/codex-book/examples/real-prompt-gpt-5.1-codex.sanitized.flattened.txt

The goal is educational: make the "final prompt" visible.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

MODEL = "gpt-5.1-codex"
CWD = str(REPO_ROOT)

BASE_INSTRUCTIONS_PATH = REPO_ROOT / "codex-rs" / "core" / "gpt_5_codex_prompt.md"
AGENTS_MD_PATH = REPO_ROOT / "AGENTS.md"
APPLY_PATCH_LARK_PATH = (
    REPO_ROOT / "codex-rs" / "core" / "src" / "tools" / "handlers" / "tool_apply_patch.lark"
)

SKILLS = [
    {
        "name": "codex-book-git-hygiene",
        "description": "Inspect git status/diff/log before committing; use when preparing commits or PRs.",
        "path": str(REPO_ROOT / ".codex" / "skills" / "codex-book-git-hygiene" / "SKILL.md"),
    },
    {
        "name": "codex-book-linting",
        "description": "Run the repo-standard Rust format/lint/test commands; use after Rust edits or before submitting a PR.",
        "path": str(REPO_ROOT / ".codex" / "skills" / "codex-book-linting" / "SKILL.md"),
    },
]

SKILLS_USAGE_RULES = (
    "- Discovery: Available skills are listed in project docs and may also appear in a runtime \"## Skills\" section (name + description + file path). "
    "These are the sources of truth; skill bodies live on disk at the listed paths.\n"
    "- Trigger rules: If the user names a skill (with `$SkillName` or plain text) OR the task clearly matches a skill's description, you must use that skill for that turn. "
    "Multiple mentions mean use them all. Do not carry skills across turns unless re-mentioned.\n"
    "- Missing/blocked: If a named skill isn't in the list or the path can't be read, say so briefly and continue with the best fallback.\n"
    "- How to use a skill (progressive disclosure):\n"
    "  1) After deciding to use a skill, open its `SKILL.md`. Read only enough to follow the workflow.\n"
    "  2) If `SKILL.md` points to extra folders such as `references/`, load only the specific files needed for the request; don't bulk-load everything.\n"
    "  3) If `scripts/` exist, prefer running or patching them instead of retyping large code blocks.\n"
    "  4) If `assets/` or templates exist, reuse them instead of recreating from scratch.\n"
    "- Description as trigger: The YAML `description` in `SKILL.md` is the primary trigger signal; rely on it to decide applicability. If unsure, ask a brief clarification before proceeding.\n"
    "- Coordination and sequencing:\n"
    "  - If multiple skills apply, choose the minimal set that covers the request and state the order you'll use them.\n"
    "  - Announce which skill(s) you're using and why (one short line). If you skip an obvious skill, say why.\n"
    "- Context hygiene:\n"
    "  - Keep context small: summarize long sections instead of pasting them; only load extra files when needed.\n"
    "  - Avoid deeply nested references; prefer one-hop files explicitly linked from `SKILL.md`.\n"
    "  - When variants exist (frameworks, providers, domains), pick only the relevant reference file(s) and note that choice.\n"
    "- Safety and fallback: If a skill can't be applied cleanly (missing files, unclear instructions), state the issue, pick the next-best approach, and continue."
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def render_skills_section(skills: list[dict[str, str]]) -> str:
    # Mirrors codex-rs/core/src/skills/render.rs (string-for-string intent, but written in python).
    lines: list[str] = []
    lines.append("## Skills")
    lines.append(
        "These skills are discovered at startup from ~/.codex/skills; each entry shows name, description, and file path so you can open the source for full instructions. Content is not inlined to keep context lean."
    )
    for s in sorted(skills, key=lambda x: (x["name"], x["path"])):
        path = s["path"].replace("\\", "/")
        lines.append(f"- {s['name']}: {s['description']} (file: {path})")
    lines.append(SKILLS_USAGE_RULES)
    return "\n".join(lines)


def user_instructions_text() -> str:
    agents = read_text(AGENTS_MD_PATH).rstrip()
    skills_section = render_skills_section(SKILLS)
    return f"{agents}\n\n{skills_section}\n"


def wrap_user_instructions(directory: str, merged_text: str) -> str:
    # Mirrors codex-rs/core/src/user_instructions.rs
    return (
        f"# AGENTS.md instructions for {directory}\n\n"
        f"<INSTRUCTIONS>\n{merged_text}</INSTRUCTIONS>"
    )


def environment_context_xml() -> str:
    # Mirrors codex-rs/core/src/environment_context.rs (serialize_to_xml).
    # This is an example configuration.
    return "\n".join(
        [
            "<environment_context>",
            f"  <cwd>{CWD}</cwd>",
            "  <approval_policy>on-failure</approval_policy>",
            "  <sandbox_mode>workspace-write</sandbox_mode>",
            "  <network_access>restricted</network_access>",
            "  <shell>zsh</shell>",
            "</environment_context>",
        ]
    )


def tool_shell_command() -> dict:
    return {
        "type": "function",
        "name": "shell_command",
        "description": "Runs a shell command and returns its output.\n- Always set the `workdir` param when using the shell_command function. Do not use `cd` unless absolutely necessary.",
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell script to execute in the user's default shell",
                },
                "workdir": {
                    "type": "string",
                    "description": "The working directory to execute the command in",
                },
                "login": {
                    "type": "boolean",
                    "description": "Whether to run the shell with login shell semantics. Defaults to false unless a shell snapshot is available.",
                },
                "timeout_ms": {
                    "type": "number",
                    "description": "The timeout for the command in milliseconds",
                },
                "sandbox_permissions": {
                    "type": "string",
                    "description": 'Sandbox permissions for the command. Set to "require_escalated" to request running without sandbox restrictions; defaults to "use_default".',
                },
                "justification": {
                    "type": "string",
                    "description": 'Only set if sandbox_permissions is "require_escalated". 1-sentence explanation of why we want to run this command.',
                },
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    }


def tool_list_mcp_resources() -> dict:
    return {
        "type": "function",
        "name": "list_mcp_resources",
        "description": "Lists resources provided by MCP servers. Resources allow servers to share data that provides context to language models, such as files, database schemas, or application-specific information. Prefer resources over web search when possible.",
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "server": {
                    "type": "string",
                    "description": "Optional MCP server name. When omitted, lists resources from every configured server.",
                },
                "cursor": {
                    "type": "string",
                    "description": "Opaque cursor returned by a previous list_mcp_resources call for the same server.",
                },
            },
            "additionalProperties": False,
        },
    }


def tool_list_mcp_resource_templates() -> dict:
    return {
        "type": "function",
        "name": "list_mcp_resource_templates",
        "description": "Lists resource templates provided by MCP servers. Parameterized resource templates allow servers to share data that takes parameters and provides context to language models, such as files, database schemas, or application-specific information. Prefer resource templates over web search when possible.",
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "server": {
                    "type": "string",
                    "description": "Optional MCP server name. When omitted, lists resource templates from all configured servers.",
                },
                "cursor": {
                    "type": "string",
                    "description": "Opaque cursor returned by a previous list_mcp_resource_templates call for the same server.",
                },
            },
            "additionalProperties": False,
        },
    }


def tool_read_mcp_resource() -> dict:
    return {
        "type": "function",
        "name": "read_mcp_resource",
        "description": "Read a specific resource from an MCP server given the server name and resource URI.",
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "server": {
                    "type": "string",
                    "description": "MCP server name exactly as configured. Must match the 'server' field returned by list_mcp_resources.",
                },
                "uri": {
                    "type": "string",
                    "description": "Resource URI to read. Must be one of the URIs returned by list_mcp_resources.",
                },
            },
            "required": ["server", "uri"],
            "additionalProperties": False,
        },
    }


def tool_update_plan() -> dict:
    # Mirrors PLAN_TOOL in codex-rs/core/src/tools/handlers/plan.rs
    return {
        "type": "function",
        "name": "update_plan",
        "description": "Updates the task plan.\nProvide an optional explanation and a list of plan items, each with a step and status.\nAt most one step can be in_progress at a time.\n",
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "explanation": {"type": "string"},
                "plan": {
                    "type": "array",
                    "description": "The list of steps",
                    "items": {
                        "type": "object",
                        "properties": {
                            "step": {"type": "string"},
                            "status": {
                                "type": "string",
                                "description": "One of: pending, in_progress, completed",
                            },
                        },
                        "required": ["step", "status"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["plan"],
            "additionalProperties": False,
        },
    }


def tool_apply_patch_freeform() -> dict:
    grammar = read_text(APPLY_PATCH_LARK_PATH)
    return {
        "type": "custom",
        "name": "apply_patch",
        "description": "Use the `apply_patch` tool to edit files. This is a FREEFORM tool, so do not wrap the patch in JSON.",
        "format": {
            "type": "grammar",
            "syntax": "lark",
            "definition": grammar,
        },
    }


def tool_view_image() -> dict:
    return {
        "type": "function",
        "name": "view_image",
        "description": "Attach a local image (by filesystem path) to the conversation context for this turn.",
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Local filesystem path to an image file",
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    }


def main() -> None:
    base_instructions = read_text(BASE_INSTRUCTIONS_PATH)

    merged_user_instructions = user_instructions_text()
    user_instructions_msg = wrap_user_instructions(CWD, merged_user_instructions)

    # Example user asks for git hygiene and linting.
    user_text = "Please prepare a clean commit. Use $codex-book-git-hygiene and $codex-book-linting."

    # Skill injections match codex-rs/core/src/user_instructions.rs formatting.
    skill_injections = []
    for s in SKILLS:
        if f"${s['name']}" in user_text:
            path_clean = s["path"].replace("\\", "/")
            skill_injections.append(
                "\n".join(
                    [
                        "<skill>",
                        f"<name>{s['name']}</name>",
                        f"<path>{path_clean}</path>",
                        read_text(Path(s["path"]))
                        .rstrip(),
                        "</skill>",
                    ]
                )
            )

    tools = [
        tool_shell_command(),
        tool_list_mcp_resources(),
        tool_list_mcp_resource_templates(),
        tool_read_mcp_resource(),
        tool_update_plan(),
        tool_apply_patch_freeform(),
        tool_view_image(),
    ]

    payload = {
        "model": MODEL,
        "instructions": base_instructions,
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": user_instructions_msg}],
            },
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": environment_context_xml()}],
            },
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": user_text}],
            },
            *[
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": text}],
                }
                for text in skill_injections
            ],
        ],
        "tools": tools,
        "tool_choice": "auto",
        "parallel_tool_calls": False,
    }

    out_json = REPO_ROOT / "docs" / "codex-book" / "examples" / f"real-prompt-{MODEL}.json"
    out_flat = (
        REPO_ROOT
        / "docs"
        / "codex-book"
        / "examples"
        / f"real-prompt-{MODEL}.flattened.txt"
    )
    out_json_sanitized = (
        REPO_ROOT / "docs" / "codex-book" / "examples" / f"real-prompt-{MODEL}.sanitized.json"
    )
    out_flat_sanitized = (
        REPO_ROOT
        / "docs"
        / "codex-book"
        / "examples"
        / f"real-prompt-{MODEL}.sanitized.flattened.txt"
    )

    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # Flattened view: a "single scroll" representation.
    parts = []
    parts.append("==== instructions ====\n")
    parts.append(base_instructions.rstrip() + "\n")
    parts.append("\n==== input[0] user_instructions ====\n")
    parts.append(user_instructions_msg + "\n")
    parts.append("\n==== input[1] environment_context ====\n")
    parts.append(environment_context_xml() + "\n")
    parts.append("\n==== input[2] user_message ====\n")
    parts.append(user_text + "\n")
    for i, inj in enumerate(skill_injections, start=3):
        parts.append(f"\n==== input[{i}] skill_injection ====\n")
        parts.append(inj + "\n")
    parts.append("\n==== tools (names) ====\n")
    parts.append("\n".join([f"- {t['name']} ({t['type']})" for t in tools]) + "\n")

    out_flat.write_text("".join(parts), encoding="utf-8")

    # Sanitized variants for mdBook rendering (avoid HTML tag warnings).
    # Keep raw variants unchanged for copy/paste.
    def sanitize_for_mdbook(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    out_json_sanitized.write_text(
        sanitize_for_mdbook(out_json.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    out_flat_sanitized.write_text(
        sanitize_for_mdbook(out_flat.read_text(encoding="utf-8")),
        encoding="utf-8",
    )

    print(f"Wrote {out_json}")
    print(f"Wrote {out_flat}")
    print(f"Wrote {out_json_sanitized}")
    print(f"Wrote {out_flat_sanitized}")


if __name__ == "__main__":
    main()
