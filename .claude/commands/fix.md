---
description: Fix a bug or implement a feature from description
argument-hint: [issue-description]
---

## Task
Fix/implement: $ARGUMENTS

## Workflow
1. PLAN first (don't edit yet) — identify all files affected
2. Write/update tests FIRST
3. Implement the fix
4. Run tests: !`pytest -x` or `npm test`
5. Verify all tests pass before finishing

## Constraints
- Follow existing patterns in codebase
- Keep changes minimal
- Add comments for complex logic
- Use systematic-debugging skill for bug fixes
