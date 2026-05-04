# CLAUDE.md

Behavioral + workflow guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Bias:** caution over speed. For trivial tasks, use judgment and skip ceremony.

---

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

For any non-trivial task (3+ steps or architectural decisions), enter plan mode first. Write detailed specs upfront to reduce ambiguity. If something goes sideways mid-task, **stop and re-plan** — don't keep pushing.

## 2. Plan → Verify → Execute

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, write the plan to `tasks/todo.md` as checkable items:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Check in on the plan before implementing. Mark items complete as you go. Add a review section to `tasks/todo.md` when done.

Strong success criteria let you loop independently. Weak criteria ("make it work") cause constant clarification.

## 3. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Test: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

For non-trivial changes, also pause and ask: "Is there a more elegant way?" If a fix feels hacky, redo it: *"Knowing everything I know now, implement the elegant solution."* Skip this for simple, obvious fixes — don't over-engineer.

## 4. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that **your** changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the user's request.

## 5. Subagent Strategy

**Keep main context window clean. Throw compute at hard problems.**

- Use subagents liberally for research, exploration, parallel analysis.
- One task per subagent for focused execution.
- For complex problems, spawn multiple subagents instead of bloating main context.

## 6. Verification Before Done

**Never mark a task complete without proving it works.**

- Run tests, check logs, demonstrate correctness.
- Diff behavior between main and your changes when relevant.
- Ask: "Would a staff engineer approve this?"
- Use plan mode for verification steps too, not just building.

## 7. Autonomous Bug Fixing

**When given a bug report: fix it. Don't ask for hand-holding.**

- Point at logs, errors, failing tests — then resolve them.
- Zero context-switching required from the user.
- Fix failing CI without being told how.

## 8. Self-Improvement Loop

**Every correction becomes a permanent rule.**

After ANY correction from the user:
- Update `tasks/lessons.md` with the pattern.
- Write a rule for yourself that prevents the same mistake.
- Iterate until mistake rate drops.
- Review `tasks/lessons.md` at session start for the relevant project.

---

## Core Principles

- **Simplicity First** — minimum code, minimum impact.
- **No Laziness** — find root causes, no temporary fixes, senior-engineer standards.
- **Minimal Impact** — only touch what's necessary; avoid introducing bugs.
- **Plan Before Build** — write the plan, verify the plan, then execute.
- **Verify Before Done** — proof of correctness or it isn't done.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, clarifying questions come *before* implementation rather than *after* mistakes, and the same correction never needs to be made twice.
