Update the activity hint shown to the user in the status bar.

Call this tool whenever you enter a new phase of the task, such as:
- After finishing analysis and starting implementation
- After completing core changes and beginning verification / testing
- When switching from one major subtask to another

Keep the hint to one short sentence (≤15 words) describing what you are
currently doing or trying to achieve. Use the same language as the user.

Examples:
- "Analyzing the current auth implementation"
- "Refactoring the auth module"
- "Running tests to verify the fix"
- "Searching for all callers of this function"

Do not call this tool on every single tool call — only when the overall
phase or status has meaningfully changed.
