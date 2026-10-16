---
name: check-in
description: Quiet, board-first periodic check across the fleet. Reports only gaps; if nothing is off it records observations and sends nothing. Runs every 30 minutes from the scheduled job, or on request.
---

# /check-in

1. `abacus-logbook checkin start` (note the id).
2. **Logbook before boards:** `abacus-logbook show in-flight` (with `--lane <lane>` in a lane), `show overdue`, `show asks`.
3. **Then boards, sessions and branches:** for each repository with in-flight work, `cd <repo> && bd show <bead> --json`
   and `bd list --status in_progress --json`; `abacus-session list`; `git -C <repo> ls-remote origin refs/heads/<default branch>` (read-only; the branch from `ls-remote --symref origin HEAD`).
4. **Five progress questions per program:** What closed since last check-in? What is in progress and for how long?
   What is blocked or waiting on a ruling? Is any worker idle with work queued? Is anything overdue?
5. Keep a stall count per item: `abacus-logbook observe <bead> "stall <n>: <what you saw>" --checkin <id>`.
6. **Message a worker only about a specific gap:** a bead closed with no report; an idle worker with its queue not
   empty; an item running long (stall count ≥ 3); a worker waiting on input. Message the operator only for decisions
   or failures. Record each gap with `observe ... --gap`.
7. **If nothing is off: send nothing.** Do not manufacture activity.
8. `abacus-logbook checkin finish <id> --summary "<one line: gaps found or 'no gaps'>"`.
9. Check your own context: if roughly 30% or less remains, run `/hand-over` now.
