---
name: codex-book-git-hygiene
description: Inspect git status/diff/log before committing; use when preparing commits or PRs.
---

# Codex Book: Git Hygiene

## Standard inspection bundle

- `git status`
- `git diff`
- `git log -n 20 --oneline`

## Before committing

- Ensure no secrets or tokens are staged.
- Keep commits scoped and messages aligned with repo style.
