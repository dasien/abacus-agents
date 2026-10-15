---
name: file-proposals
description: Turn retrospective actions into tracked proposal beads on the board of the repository that owns the change, deduplicated against what is already open. Use after writing any retrospective, and when a retro would repeat an earlier action.
---

# /file-proposals

Retro actions that live only in a retro get repeated, not done. Each one becomes a bead the owner can triage.

1. **Owner.** Decide which repository owns each action:
   - guards, workflows, worker skills, doctor, adopt or finalize: `abacus-standards`
   - logbook, verify, session launcher, memory or status: `abacus-infra`
   - orchestrator or concierge roles, the protocol, deploy: `abacus-agents`
   - installer, demo or docs: `abacus`
   - a product repository's own code: that repository

   The Abacus repositories' paths are under `components` in `~/.abacus/config.json`. Read it with
   `cat ~/.abacus/config.json`, never a script (the fence treats interpreter one-liners as writes).
2. **Already open?** `cd <repo> && bd list --label retro-action --json`. If an open bead covers the same action, don't
   file a duplicate. Append a note, written literally:
   `bd update <id> --append-notes '[from orchestrator] seen again in <retro id>: <one line of new evidence>'`.
   Repeats then show up as a count of notes, which is the signal the owner needs.
3. **Otherwise file it** (filing on another board is allowed; never set status or a pipeline label, which belong to the owner):
   ```
   cd <repo> && bd create "<action as an outcome>" -t task -l retro-action --silent --body-file - <<'EOF'
   FILED AGAINST: <short sha or unknown>

   From retro <retro id>. Evidence: <what happened, with ids>.
   Proposed change: <one paragraph>.
   Review: <checkable thing> by <YYYY-MM-DD>
   EOF
   ```
   Pass the description as real lines (the heredoc above). A `\n` inside quotes is stored literally.
4. **Changes reserved to the operator** (guards, gates, verify, delegated authority) are still filed, with `operator`
   in the description. Filing is a proposal, not a change.
5. List the ids you filed or updated at the end of the retro, under the action items.
