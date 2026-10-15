---
name: status
description: Answer "what's going on?" from durable state - what needs the operator, what's running, what finished. Use for any question about progress, and at session start.
---

# /status

0. **What's actually running comes from Agent View:** `abacus-session list` first. The logbook's saved liveness can be
   stale (a reset stops workers without the logbook seeing it), so never report a session as idle from it alone.
1. `abacus-status` (one screen: program status, NEEDS YOU count, in-flight dispatches, live sessions, and who
   started or stopped each session and why). If a session is gone, the start/stop events say who ended it; don't guess.
2. If anything needs the operator, read those cards from `~/.abacus/agents/orchestrator/pages/decisions.md` and present
   each as: the question, the options with a one-line pro/con, the orchestrator's recommendation and confidence.
   Tell them they can answer right here.
3. "Staged", "queued", "lined up" and "ready" mean beads that are filed, labeled, open and not started:
   `abacus-board find "<words>"` shows them across every board (`ready: true`), including drafts awaiting approval.
   For a specific item, read its bead on its board (`cd <repo> && bd show <id> --json`) and the dispatch/report rows
   (`abacus-logbook show in-flight`, `show reports`). Report verified results as verified, claims as claims.
4. Answer in at most ~8 lines: **Needs you** (if any) → **Running** → **Finished recently**. Don't narrate tools.
