---
description: Review recent changes for bugs, security, and conventions
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Bash(git log:*)
model: sonnet
---

## Changes to review
!`git diff --name-only HEAD~1`
!`git diff HEAD~1 --stat`

## Review checklist
1. **SECURITY** — injection, auth bypass, secrets in code, XSS
2. **LOGIC** — edge cases, null/undefined, race conditions, off-by-one
3. **PERFORMANCE** — N+1 queries, missing indexes, memory leaks, unnecessary re-renders
4. **CONVENTIONS** — violations of CLAUDE.md rules, inconsistent patterns
5. **TESTS** — are new paths tested? are edge cases covered?

## Output format
### 🔴 Critical (must fix before merge)
### 🟡 Warning (should fix)
### 🟢 Suggestion (nice to have)
### ✅ Good patterns noticed

Be specific: file, line number, what's wrong, how to fix.
