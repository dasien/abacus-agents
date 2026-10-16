# The concierge role (design)

The concierge is the operator's front door to Abacus: a session you talk to in plain language. It answers
from durable state, records your instructions verbatim, and hands them to the planner or the orchestrator in a fixed
format. The decisions below were taken on 2026-10-11; the planner joined in 0.7.0.

## Decisions
| Question | Decision |
|---|---|
| How the operator reaches it | A dedicated background session, `agent:concierge`, in Agent View (`claude agents`, switch to it), or `abacus chat`, which starts it if needed and attaches |
| Orchestrator and planner lifecycle | **On demand.** The concierge may start the orchestrator or the planner (only those sessions) when the operator asks for work or a plan. Both stop themselves when done; nothing idles between programs |
| Ambient awareness | An opt-in Claude Code **status line** in every session (`abacus · RUNNING · 2 in flight · 1 needs you`), enabled by the operator with `abacus statusline enable` |

## Why a dedicated session
Abacus accepts operator words as a ruling only if they appear in a session where the operator typed them (the
`human-only` guard). So the concierge must be the session you type into, not a relay behind another one. A
dedicated role session can also have its tools constrained. An `/abacus` skill inside your normal session could not.

## What it may and may not do
Model: Sonnet. Permission mode: `auto`. No Edit/Write tools. Deployed to `~/.abacus/agents/concierge` from this
repository, out of its own reach.

**May:**
- read state: `abacus-session list` first (Agent View knows what's running), `abacus-status`, `abacus-logbook digest` /
  `show …`, the decisions page, boards (`bd show|list|ready`, and `abacus-board find` across every board), git
  history (read-only), `consult_memory`
- write exactly one thing: `abacus-logbook ruling add --words "<verbatim>" --where agent:concierge --target …`
  (an approval of a plan names every draft bead it covers)
- start the orchestrator or the planner, recording why:
  `abacus-session start agent:orchestrator --reason "operator: <goal>"`
- message the orchestrator or the planner with `HANDOFF`

**May not:** dispatch, decide, file beads, verify, start workers, or touch any repository.

This is enforced by a new **`role-commands`** guard. Every shell command must match the role's allowlist in
`.claude/role-policy.json`. The write fence alone can't stop logbook writes, because they go through a CLI rather
than files.

## Three moves for anything the operator says
1. **Answer it** from durable state (what's running, what needs me, what happened to X).
2. **Pass it on.** Record the words verbatim (`ruling add`), confirm the intent back in one line, start the planner
   ("plan …") or the orchestrator ("build …", "work on …", a card's answer) if it isn't running, and send a
   `HANDOFF … STATUS: decided`. For a build, name the whole chain when confirming.
3. **Talk it through first.** A remark, a "should", or a "maybe" isn't an instruction. Clarify. If it's still
   ambiguous but worth passing on, send `STATUS: lean`. The orchestrator never acts on a lean handoff as if the
   operator had decided.

## HANDOFF grammar (concierge → orchestrator or planner)
```
HANDOFF <bead | "no item">: the operator said "<verbatim>" (ruling <id>, agent:concierge, <UTC time>).
LANE: <lane>
Wants: <the act>. Told them: <what the concierge already answered>.
INTENT: <what should be true afterwards, in the operator's terms>.
NOT ASKING FOR: <what the conversation ruled out>.
STATUS: decided | lean
```

## Orchestrator side
- A `/handoff` skill. Check the ruling exists in the logbook with the quoted words. Act on `decided` within the
  rulings and authority boundary. For `lean`, reply to the concierge with the question that would settle it. Then
  send the concierge a one-line acknowledgement.
- A ruling that arrives by handoff is already captured, so it isn't recorded twice. The orchestrator records it on
  the beads and relays it to workers as usual.
- Decisions-page cards name `agent:concierge` as where to answer.

## Status line
`abacus-status --line` reads only the logbook and the decisions page, so it is fast and safe to run on every
redraw. `abacus statusline enable` / `disable` changes `~/.claude/settings.json`, and only when you run it.

## Out of scope
Integrating Bitwarden's own Claude Code agents (on hold until the core is settled).

## Done means
- In Agent View, `agent:concierge` answers "what's running?" from durable state.
- A goal typed to the concierge becomes one verbatim ruling, an on-demand orchestrator, and a completed program.
- A lean handoff produces a question, not work.
- Any command outside the allowlist is refused.
- The status line shows the program state in other sessions.
