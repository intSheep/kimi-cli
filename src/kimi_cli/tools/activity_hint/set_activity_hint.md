Update the activity hint shown to the user in the status bar.

**MANDATORY**: Call this tool at the start of every task and whenever you enter a new phase. The user relies on this hint to see what you are currently doing. If you skip this call, the status bar will show stale or missing information.

Call this tool when:
- The user assigns a new task (first thing you do)
- You finish analysis and start implementation
- You complete core changes and begin verification / testing
- You switch from one major subtask to another

Keep the hint to one short sentence (≤15 words) describing what you are
currently doing or trying to achieve. Use the same language as the user.

Examples:
- "Analyzing the current auth implementation"
- "Refactoring the auth module"
- "Running tests to verify the fix"
- "Searching for all callers of this function"

Do not call this tool on every single tool call — only when the overall
phase or status has meaningfully changed.
