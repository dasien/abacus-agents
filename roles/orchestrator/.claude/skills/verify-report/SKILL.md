---
name: verify-report
description: Handle an inbound worker REPORT. A report is a claim; verify it against the board and the remote before changing any state or releasing dependent work. Use whenever a message beginning "REPORT" arrives, or recovery finds a closed bead with an unverified dispatch.
---

# /verify-report

1. **Record what arrived, verbatim:** `abacus-logbook msg in --peer <sender> --body '<full message>'`, then
   `abacus-logbook report add <bead> --worker <sender> --status <CLOSED|BLOCKED|NEEDS-RULING|PROGRESS> --commit <sha> --pushed <0|1> --evidence "<evidence line>"`.
2. **By status:**
   - **CLOSED** → `abacus-verify --repo <repo> --bead <bead> --commit <sha> --record`. It also runs the dispatch's
     `--check` commands. Show the operator each check and its result (bead-closed, commit-on-remote,
     commit-names-bead, nothing-unpushed, tree-clean, bead-worktree-saved, pr-head with draft-PR landing, and each
     precondition). In a repository with `"landing": "draft-pr"`, the commit lands on the bead's own branch and
     reaches the default branch only when someone merges its PR: commit-on-remote reads that branch, and pr-head
     shows the commit is the head of its open draft PR. Only `verified: true` counts; never re-check by hand what a
     check already covers.
     If any check fails, the dispatch stays unverified: message the worker about the specific failed check.
   - **NEEDS-RULING** → if a recorded delegation covers it, decide, record it (`/relay-ruling`, marked as decided by
     the orchestrator) and tell the operator. Otherwise put it on the decisions page (`/decisions-page`) as a
     focused choice with options, your recommendation and confidence, and "answer in agent:concierge". Ask yourself
     whether existing delegated authority could have decided it; note the answer, as it is the raw material for
     expanding autonomy. When the operator's answer arrives (a HANDOFF), record and relay it (`/relay-ruling`; the
     JUDGEMENT row goes on the bead), then `abacus-logbook dispatch status <bead> in_progress`: the RULING message is
     the worker's go-ahead to resume the same dispatch.
   - **BLOCKED** → consult memory with the shape of the blocker; decide within authority (re-sequence, follow-up
     bead) or escalate to the operator.
   - **PROGRESS** → record only. If `next` says "replace me", end the worker (`abacus-session stop`) once its tree is
     clean and start a fresh one for the remaining work.
3. **Ship, then release dependants**, only after `verified: true`. If the verified bead carries an `export:<capability>`
   label, mark it delivered on its board: `cd <repo> && bd ship <capability>`. Consumers that depend on
   `external:<project>:<capability>` then show it delivered. (Beads 1.3 records these cross-repo edges but doesn't
   enforce them; the logbook's `--requires-verified` is what enforces the wait, so a missing board edge isn't a gap.)
   Then: for each bead waiting on this one, `/dispatch-bead` with
   `--requires-verified <this bead>` and the verified commit in its preconditions. Clear the wait on the consuming
   board with a note `[from orchestrator] prerequisite <bead> verified at <sha>`, written as literal text in one `bd`
   command per board (the foreign-board guard refuses notes it cannot read, e.g. built from shell variables).
4. Close the matching promise: `abacus-logbook promise done <id> --resolution "<what was verified>"`.
5. When a program's work is all verified, close the dispatch rows (`dispatch status <bead> closed`), end idle
   workers with a reason (`abacus-session stop coder:<repo> --reason "program complete"`), and write the program
   retrospective (blameless; intended vs happened; where the operator corrected the system; at most three actions with
   owners) into `retros/` using the retro header. **File every action as a proposal bead** (`/file-proposals`), so
   it is tracked instead of repeated in the next retro. Then set the decisions page to `COMPLETE`, send `agent:concierge` a
   one-line note, and, if nothing else is in flight and no card is open, close your lane if you have one
   (`abacus-logbook lane close <lane>`, which releases its repositories), then **stop yourself** as your very last
   action:
   `abacus-session stop <your session name> --reason "program complete; orchestrator runs on demand"`. The concierge
   starts a fresh orchestrator when the operator next asks for work.
