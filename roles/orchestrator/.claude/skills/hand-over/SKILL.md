---
name: hand-over
description: Deliberately hand the orchestrator role to a fresh session before context runs out. Use when about 30% of the context window remains (even if busy), or when the operator asks.
---

# /hand-over

States: `launched` → `recovered` → `finished`; or `aborted` (successor never recovered, so you carry on) or
`adopted` (you vanished mid-handover; the successor carries on).

1. **Store the working set durably.** Every ask the operator made becomes a promise
   (`abacus-logbook promise add ...`); every chat ruling is a recorded ruling (`/relay-ruling`). Nothing may live only
   in this conversation.
2. **Choose the successor name:** your name plus the next generation (`agent:orchestrator` → `agent:orchestrator-g2`,
   `-g2` → `-g3`; in a lane, `agent:orchestrator-<lane>` → `agent:orchestrator-<lane>-g2`). Put your lane in the
   working set so the successor knows which lane it runs.
3. `abacus-logbook handover launched --from <your name> --to <successor> --working-set "<one paragraph: current plan, what you were about to do, open decisions>"`
4. `abacus-session start <successor>`. It runs `/recover`, finds the handover, and messages you `recovered (handover <id>)`.
5. **Wait for "recovered".** Do not dispatch or decide while waiting. If it does not arrive within 10 minutes, or the
   successor reports failure: `abacus-logbook handover aborted <id>`, stop the successor, and carry on.
6. On "recovered": `abacus-logbook handover finished <id>`, tell the operator which session now holds the role, then
   stop yourself: `abacus-session stop <your name>`.
