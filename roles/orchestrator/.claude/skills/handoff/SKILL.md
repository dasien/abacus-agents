---
name: handoff
description: Act on a HANDOFF from agent:concierge (the operator's front door). Use whenever a message beginning "HANDOFF" arrives, or your launch prompt names a concierge ruling.
---

# /handoff

The concierge has already recorded the operator's words as a ruling. You turn that into coordinated work, or
into a question. Never into work the operator didn't ask for.

1. **Record the message:** `abacus-logbook msg in --peer agent:concierge --body '<full HANDOFF text>'`.
2. **Check the ruling exists:** `abacus-logbook show rulings`. Its id, its words (verbatim, as quoted in the HANDOFF),
   `said_where: agent:concierge`, and its targets must match. If they don't, reply to the concierge
   `HANDOFF <id> REFUSED: <what didn't match>` and stop.
3. **STATUS: lean** → do not dispatch, file, or decide anything. Reply to the concierge with the single question that
   would let the operator decide (options, your recommendation and confidence). Stop.
4. **STATUS: decided** → first rewrite the decisions page with `Program status: RUNNING` (the goal, the beads, what
   happens next) so the concierge and the status line show it from the start. Then act within your authority, exactly
   as if the operator had said it to you:
   - a new goal: read its verb by the protocol's standing meanings (**build** = the beads and every prerequisite, to
     done; **work on** = advance the named bead only, stopping at any report; never ask about releases or tags unless
     the operator's words did). Then consult memory, check the premise on the boards, record the ruling on each target
     bead (`/relay-ruling` steps 3-6; **skip step 1**, since the ruling is already captured, and pass every bead as a
     `--target` when one utterance covers several), then run the program (`/dispatch-bead`, `/verify-report`).
   - an answer to a NEEDS YOU card: map it to the card's options, record and relay it (`/relay-ruling`, skipping
     step 1), update the decisions page, carry on.
   - anything outside your authority (releases, credentials, guard changes, money, irreversible acts): don't act; put
     an OPERATOR STEP card on the decisions page naming the exact act and session.
5. **Acknowledge** to the concierge in one line: `ACK HANDOFF ruling <id>: <what you are doing next>`.
