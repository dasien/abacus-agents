---
name: revise
description: Apply the operator's answer to a PLAN-REVIEW - edit, add or drop drafts and send a fresh review, or apply an approval (pipeline labels, lift draft) and send PLAN-APPLIED. Use when a HANDOFF answers a plan.
---

# /revise

1. **Check the ruling** as in `/plan` step 1. An approval ruling must name each bead it approves as a target; if it
   doesn't, reply `HANDOFF <id> REFUSED: approval must name the beads` and stop.
2. **Changes** ("split the CLI bead", "drop the docs one", "make the SDK one full", "the criterion should say …"):
   apply them to the drafts (`bd update` / `bd create -l draft` / `bd close <draft> --reason "dropped: <operator words>"`),
   rewire edges if needed, then send a fresh PLAN-REVIEW. A label change is only recorded in the review; labels are
   applied at approval.
3. **Approval** (the operator says yes in their own words, naming or covering these drafts). For each approved draft,
   in its repository:
   - `bd label add <bead> pipeline:<label>` (the reviewed label, or the one the operator changed it to)
   - `bd label remove <bead> draft`
   - confirm with `cd <repo> && abacus-board brief <bead>`: it must print `"ok": true`
4. **Send PLAN-APPLIED** to `agent:concierge` (grammar in the protocol), suggesting the build in the operator's terms:
   "build <source>". Leave the approval ruling as it is: the orchestrator writes its row on each bead and records it
   when it builds (`/relay-ruling`). Never mark a ruling recorded on a bead whose notes don't quote it; the logbook
   refuses that.
5. **Stop yourself** (CLAUDE.md rule 7). Building is the orchestrator's job, when the operator asks for it.
