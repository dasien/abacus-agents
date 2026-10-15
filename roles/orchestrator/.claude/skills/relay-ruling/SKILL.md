---
name: relay-ruling
description: Capture an operator ruling, instruction or correction verbatim, record it on the bead as a JUDGEMENT/STANDING row, then relay it to the worker. Use the moment the operator rules on anything, and for rulings found unrecorded during recovery.
---

# /relay-ruling

1. **Capture first, before replying** (skip this step when the ruling arrived in a HANDOFF from the concierge: it is
   already captured, and capturing it again would duplicate the operator's words):
   `abacus-logbook ruling add --words "<exact words as typed>" --where <chat|page card|session> --question "<what was asked>" --target <bead> [--target <bead> ...]`
   One utterance is one ruling: pass every bead it covers as a `--target`, never record the same words twice. Write
   the words literally in the command (not through a shell variable) so the attestation guard can read them.
2. **Map** the words to the options asked. "b with a change" stays "b with a change". If the words don't resolve the
   question, ask a follow-up; that is not a ruling.
3. **Build the row** per `/judgments` (JUDGEMENT for an answered question, STANDING for an unprompted instruction),
   with a review clause: a checkable thing, then `by <YYYY-MM-DD>`, and end it with `ruling: #<id>` so a worker can
   match the relayed `RULING <bead> (ruling <id>)` to this row. `abacus-judgment check '<row>'` must print OK.
4. **Record on the bead** (on the owning board; you are always foreign there). Write the note as literal text in the
   `bd` command, never through a shell variable or substitution, because the foreign-board guard can only check text it
   can see:
   `cd <repo> && bd update <bead> --append-notes '[from orchestrator] <row>'`, then
   `abacus-logbook ruling recorded <ruling id> --on <bead>`. The logbook checks the bead's notes and refuses unless the
   row quoting the operator's words is really there.
5. **Relay** with SendMessage to **every worker on a bead the ruling covers**, using the RULING grammar in
   `protocol/PROTOCOL.md`. The first line must be `RULING <bead> (ruling <id>)`: the SendMessage hook records the
   relay from it, and the logbook refuses to dispatch a covered bead to a worker that was never sent the ruling.
   `abacus-logbook show rulings-unrelayed` lists anything still owed.
6. **No bead to record it on?** Some operator words cover no bead: "start the orchestrator", "what's running?".
   Once you have acted on them (for a HANDOFF, after your `ACK HANDOFF`), close the ruling out so it stops showing as
   unrecorded: `abacus-logbook ruling recorded <id> --on none --reason "<what it asked>; <what you did>"`. The logbook
   refuses this for a ruling with targets. If the words decide anything about work, that work needs a bead: find or
   propose it and record the ruling there, never `--on none`.
7. If you decided under delegated authority, the row's `ruled:` field quotes the delegation you relied on and the
   decisions page shows it as "decided by the orchestrator" (a record, not something the operator must approve).
