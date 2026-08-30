---
name: New prompt
description: New prompt
invokable: true
---

---

name: Verify Code
description: Analyze, test and verify the current implementation
invokable: true

---

Analyze the current implementation before making any changes.

1. Understand what the code is supposed to do.
2. Inspect the relevant files, dependencies and related implementations.
3. Identify bugs, edge cases, missing validation and potential regressions.
4. Check whether the implementation follows the existing project architecture.
5. Check for duplicated or unnecessary logic.
6. Check error handling and security issues where relevant.
7. Create or update appropriate tests.
8. Run the relevant tests, build or validation commands when available.
9. Fix problems that are directly related to the requested implementation when appropriate.
10. Re-run the relevant verification after fixes.
11. Review the final changes and confirm that unrelated code was not modified.

Do not claim that tests passed unless they were actually executed.

Do not assume that files, functions, classes, APIs or dependencies exist. Inspect them first.

At the end, report:

- What was checked
- What was changed
- Tests/builds actually executed
- Problems found
- Problems remaining
- Recommended next step
