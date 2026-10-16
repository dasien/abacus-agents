---
name: recover
description: Rebuild the orchestrator's operating picture from durable state before acting. Run first in every session, after any restart or compaction, and when taking over in a handover. The conversation is a cache; this is the source.
---

# /recover

Do these in order. Do not dispatch, decide or message a worker until step 9 prints.

1. **Digest.** `abacus-logbook digest`. If it says the logbook is unreachable, continue from the boards (steps 3-4)
   and say so; `abacus-logbook rebuild` reconstructs in-flight dispatches from the boards once it is back.
2. **Live sessions.** `abacus-session list` (Agent View is authoritative for which sessions exist and their state;
   this also reconciles worker liveness into the logbook).
3. **In-flight work.** `abacus-logbook show in-flight`. For every row, read the bead on its owning board:
   `cd <repo> && bd show <bead> --json`. Remote state is read-only: `git -C <repo> ls-remote --symref origin HEAD`
   gives the default branch (never assume `main`), `git -C <repo> ls-remote origin refs/heads/<branch>` its tip.
   Never `git fetch`: it writes the sibling's refs and the role fence refuses it. The board wins on disagreement:
   - board closed, dispatch not verified → run `/verify-report` for it now
   - board open, dispatch closed/cancelled → flag it as a gap
   - worker `gone` with an open dispatch → it needs a fresh worker (ask before starting one if the plan changed)
4. **Promises and rulings.** `abacus-logbook show asks` (everything you owe) and
   `abacus-logbook show rulings-unrecorded` (operator words not yet on a bead: record them now via `/relay-ruling`;
   one that covers no bead is closed out with `--on none --reason`, step 6 there)
   and `abacus-logbook show rulings-unrelayed` (rulings a dispatched worker was never sent: relay them now).
5. **Handover.** `abacus-logbook show handovers`. If the newest is `launched` with `to_session` equal to your session
   name, read its `working_set`, then: `abacus-logbook handover recovered <id>` and SendMessage the `from_session`:
   `recovered (handover <id>)`.
6. **The decisions page.** Read `pages/decisions.md`. Check every bead and commit its `Program status` names: the bead
   exists on its board (`abacus-board find <bead>`), and the commit is on its repository's default branch
   (`git -C <repo> ls-remote origin refs/heads/<branch>`, then `git -C <repo> merge-base --is-ancestor`), or with
   `"landing": "draft-pr"` at the head of the bead's open PR (`abacus-verify --repo <repo> --bead <bead> --commit
   <sha>`, without `--record`). A page naming beads or commits that no longer exist (a demo was rebuilt, a branch
   reset) is stale: note it as a gap and rewrite the page from what you just verified before acting.
7. **Schedules.** CronList. Ensure exactly one check-in job exists (every 30 minutes, prompt `/check-in`); create it
   with CronCreate if missing. Recreate any scheduled responsibility recorded as a promise with a trigger.
8. **Shared memory.** MCP tools load on demand: `ToolSearch` with `select:mcp__abacus-memory__consult_memory`, then
   call `consult_memory` once with a trivial query. If the tool is missing, say so in the picture
   and put an OPERATOR STEP card on the decisions page; never silently skip rule 8 (CLAUDE.md). A score of 0.0 against an
   uncalibrated floor is expected while the corpus holds only a handful of records; note it once rather than
   reporting it as a new gap each program (calibration is a tracked proposal, done when real repositories feed memory).
9. **Print the picture**, briefly: programs and goal, in-flight dispatches with verified status, open promises,
   decisions waiting on the operator, and any gap found above. Then wait for the operator's goal or act on the
   open plan within delegated authority.

A compaction summary is never acted on until steps 1-4 have checked it against durable sources.
