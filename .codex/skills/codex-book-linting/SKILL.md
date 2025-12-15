---
name: codex-book-linting
description: Run the repo-standard Rust format/lint/test commands; use after Rust edits or before submitting a PR.
---

# Codex Book: Linting & Formatting

## Quick path (scoped)

- If you edited Rust in `codex-rs/<crate>`:
  - Run `just fmt`
  - Run `just fix -p <crate>`
  - Run `cargo test -p <crate>`

## Notes

- Prefer `-p` scoped clippy/fix to avoid slow workspace builds.
- If you touched shared crates, you may need broader checks.
