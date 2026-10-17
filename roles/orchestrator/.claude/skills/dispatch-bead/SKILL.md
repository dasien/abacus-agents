---
name: dispatch-bead
description: Send one bead to one worker session with a complete, bounded DISPATCH. Use whenever work is assigned to a worker; never message work any other way.
---

# /dispatch-bead <bead> <worker>

1. **Consult memory first.** `consult_memory` with the shape of the work (not the bead id), no project filter.
   Note returned record identifiers, or "none returned".
2. **Read the bead** on its owning board: `cd <repo> && bd show <bead> --json`. For remote state, first learn the
   repository's default branch, never assume `main`: `git -C <repo> ls-remote --symref origin HEAD` prints
   `ref: refs/heads/<branch>`. Use that name everywhere (preconditions, checks, rows on the bead), and read its tip
   with `git -C <repo> ls-remote origin refs/heads/<branch>`. Never `git fetch` (a fetch writes the sibling's refs;
   the role fence refuses it). It must be open, have exactly one
   `pipeline:` label (set by the owner) and acceptance criteria. If not, do not dispatch: tell the operator or the
   owner what is missing.
3. **Worker live?** `abacus-session list`. If the repository has no live worker, start one:
   `abacus-session start coder:<repo> --reason "<bead> dispatch"`. A refusal (ATTENDED, BUSY, UNSAVED, AUTHORITY, MODEL, ROLE) is final; report it.
4. **Record BEFORE sending** (refusals stop the send):
   ```
   abacus-logbook dispatch add <bead> --repo <repo path> --worker coder:<repo> --pipeline <label> \
     --order-note "<place in sequence>" --preconditions "<checkable facts>" [--requires-verified <prereq bead>] \
     [--check "<read-only command>" ...] [--lane <your lane> --report-to <your session name>]
   ```
   In a lane, always pass `--lane` and `--report-to` (the worker reports to you, and the dispatch claims the
   repository for your lane). `LANE` means another lane owns the repository: don't work around it; tell the concierge.
   `--requires-verified` refuses unless the prerequisite's dispatch is verified. Use it for every cross-repo wait.
   **Cross-repo conditions are yours to check, not the worker's.** For a bead with a `WAITS-ON` line, check the other
   side yourself, read-only, before recording the dispatch (e.g. `git -C <producer> rev-parse HEAD` equals the
   verified commit, for a path dependency), and write what you saw into `--preconditions`. If a bead's acceptance
   criteria read another repository, the worker can't check them from its worktree: tell the board's owner and
   propose moving the condition to a `WAITS-ON` line rather than dispatching it as is. A worker that reports a
   sibling read refused is not showing a gap in the fence: Abacus's fence guards writes only, and Claude Code's
   worktree isolation is what stops git pointing outside the worktree (docs/CONCEPTS.md in the abacus repo).
   Add a `--check` for anything you would otherwise verify by reading files yourself (e.g. a consumer pins the
   prerequisite's verified sha: `--check "grep -q <sha> vendor.json"`). Checks must be read-only (grep, test, cat,
   read-only git); `abacus-verify` runs them on the report and they must pass. File checks read the files of the
   **reported commit** (workers commit from worktrees, so the main checkout may lag); git checks run in the repo. `UNRELAYED` means a ruling covering
   this bead was never sent to this worker: run `/relay-ruling` first.
5. **Compose** the DISPATCH exactly per `protocol/PROTOCOL.md` (under 1,500 chars), listing the same checks on the
   `checks:` line. Include the dispatch number from
   step 4 and the verified commit of any prerequisite in `preconditions`. Outcome, never implementation.
6. **Send** with SendMessage to `coder:<repo>` (the hook records the submitted text in the logbook). Then subscribe
   to that worker going idle (SendMessage with `notify_when_idle: true` and empty content) instead of polling: you
   are woken when it finishes or stalls, which is far cheaper than periodic check-ins.
7. `abacus-logbook dispatch sent <bead>`, and add a promise for the follow-up you owe:
   `abacus-logbook promise add "verify <bead> report" --trigger "REPORT from coder:<repo>" --work-item <bead>`
   (plus `--lane <your lane>` in a lane).
