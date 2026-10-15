---
name: intake
description: Pass an operator instruction or ruling on - to the orchestrator (build, work on, card answers) or the planner (plan a source, answer a plan review). Record the words verbatim, start the session on demand, and send a HANDOFF. Use whenever the operator asks for work, a plan, or answers a card or review.
---

# /intake

1. **Is it an instruction?** "Build X", "work on X", "ship X", "do Y", "go with b" on an open card: yes. The verbs have
   standing meanings (protocol, "What the operator's verbs mean"): **build** covers X and every bead X needs first;
   **work on** advances X only. Find the beads with `abacus-board find "<words | link | #number>"` (every fleet board;
   it pulls in prerequisites from WAITS-ON lines) and, for build, name the whole chain when you confirm ("That's
   bwcli-069, which needs sdk-eef first"). Never list a prerequisite under NOT ASKING FOR. Don't ask about releases
   or tags unless the operator mentioned one. "Plan X" goes to the planner: see **Plans** below. "We should
   probably…", "I wonder if…": no - talk it through (ask the one question that settles it) and stop here.
2. **Record the words first, verbatim** (the guard checks they are really what the operator typed):
   `abacus-logbook ruling add --words "<exact words>" --where agent:concierge --question "<the goal or the card's question>" --target <each bead it covers>`
   Note the ruling id it prints.
3. **Confirm in one line**: "Recorded. I'll ask the orchestrator to <act>."
4. **Orchestrator running?** `abacus-session list`. If `agent:orchestrator` is not live, start it (you may; nothing
   else): `abacus-session start agent:orchestrator --prompt "/recover first, then act on the HANDOFF from agent:concierge for ruling <id>." --reason "operator: <the goal in a few words> (ruling <id>)"`
   (the launcher records that you started it and why; `abacus-status` shows the reason)
   Tell the operator you started it.
5. **Send the HANDOFF** with SendMessage to `agent:orchestrator` (a successor may be `agent:orchestrator-g2`; use
   ListAgents if unsure), exactly:
   ```
   HANDOFF <bead or "no item">: the operator said "<verbatim>" (ruling <id>, agent:concierge, <UTC time>).
   Wants: <the act>. Told them: <what you already answered>.
   INTENT: <what should be true afterwards, in the operator's terms>.
   NOT ASKING FOR: <what the conversation ruled out>.
   STATUS: decided | lean
   ```
   `decided` only when the operator clearly asked for this act. `lean` when you're passing on a preference that still
   needs their confirmation - the orchestrator will come back with a question, never with work.
6. Tell the operator what happens next, and that they can ask you how it's going at any time (the status line
   shows it too). Don't send them to a terminal for status.

## Plans (the planner)
- **"Plan <source>"** (also "scope", "break down", "file the beads for", "turn this into beads"). The source is a
  GitHub issue link, a local file or folder path, or text the operator pasted. Jira and Confluence are **TBD**: ask
  for the text or a local file instead.
  1. Record the words verbatim, with no `--target` (nothing exists yet).
  2. Confirm in one line: "Recorded. I'll ask the planner to plan <source>."
  3. If `agent:planner` isn't live (`abacus-session list`), start it:
     `abacus-session start agent:planner --prompt "/plan the HANDOFF from agent:concierge for ruling <id>." --reason "operator: plan <source> (ruling <id>)"`
  4. Send the HANDOFF to `agent:planner` (Wants: plan <source>; include pasted text in full).
- **A PLAN-REVIEW arrives:** show it plainly: each draft (repository, title, proposed label and why, how many criteria,
  what it waits on), the order, and the planner's questions. Ask the operator to approve or say what to change.
- **Their answer:** record it verbatim with `--target` for **every draft bead in the review it covers**, then send the
  HANDOFF to `agent:planner`. Only a clear yes is an approval; "looks fine but…" is a change. Without those targets
  the planner can't apply labels (the guard checks them).
- **PLAN-APPLIED arrives:** tell the operator the plan is ready, and suggest building it in their terms:
  "build <source>". Building goes to the orchestrator as usual.

