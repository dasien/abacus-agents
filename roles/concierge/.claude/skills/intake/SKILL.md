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
3. **Which lane?** Every piece of work runs in a **lane**: an independent line of work with its own orchestrator,
   `agent:orchestrator-<lane>`, and its own decisions page. A repository belongs to at most one active lane.
   - **An answer to a card** goes to the lane whose page holds that card (`pages/decisions-<lane>.md`).
   - **New work:** take the repositories of the beads you found, and ask the logbook who owns each one:
     `abacus-logbook lane owner <repo path>`. If a lane owns any of them, the work joins that lane. If two different
     lanes own them, ask the operator. If the operator named a lane ("put this in the android lane"), use it.
   - **Otherwise open a new lane**, named after the work: short, lowercase, unique, e.g. `android`, `sdk-heartbeat`.
     Check `abacus-logbook lane show` first; if the obvious name is taken, use a more specific one (`android-login`).
     `abacus-logbook lane open <name> --goal "<the operator's words>" --repo <path> [--repo …] --item <bead or source> [--item …]`
   - Lanes are created on demand; there's no limit on how many run at once.
4. **Confirm in one line, naming the lane**: "Recorded. Started the **<lane>** lane (`agent:orchestrator-<lane>`) for
   <the work>." or "Recorded. Added this to the **<lane>** lane." The operator learns the name here; later they can
   refer to the work any way they like ("the android work", "the login fix", the issue), and you resolve it.
5. **Lane orchestrator running?** `abacus-session list`. If `agent:orchestrator-<lane>` isn't live, start it (you may;
   nothing else): `abacus-session start agent:orchestrator-<lane> --prompt "/recover first, then act on the HANDOFF from agent:concierge for ruling <id>." --reason "operator: <the goal in a few words> (lane <lane>, ruling <id>)"`
   (the launcher tells it its lane and records that you started it and why)
6. **Send the HANDOFF** with SendMessage to `agent:orchestrator-<lane>` (a successor may be
   `agent:orchestrator-<lane>-g2`; use ListAgents if unsure), exactly:
   ```
   HANDOFF <bead or "no item">: the operator said "<verbatim>" (ruling <id>, agent:concierge, <UTC time>).
   LANE: <lane>
   Wants: <the act>. Told them: <what you already answered>.
   INTENT: <what should be true afterwards, in the operator's terms>.
   NOT ASKING FOR: <what the conversation ruled out>.
   STATUS: decided | lean
   ```
   `decided` only when the operator clearly asked for this act. `lean` when you're passing on a preference that still
   needs their confirmation - the orchestrator will come back with a question, never with work.
7. Tell the operator what happens next, and that they can ask you how it's going at any time (the status line
   shows it too). Don't send them to a terminal for status.

## Lanes, when the operator asks about them
- "What lanes are running?" → `abacus-logbook lane show`: each lane's name, goal, repositories and whether anything
  needs them.
- "Call that lane login-fix" → `abacus-logbook lane rename <old> <new>`, only when its orchestrator isn't running
  (`abacus-session list`); a running session keeps its name. Otherwise say it can be renamed when that work is done.

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

