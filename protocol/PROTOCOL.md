# Abacus coordination protocol (v1)

This repository is the protocol's canonical home. The worker-facing half is distributed to participating
repositories by abacus-standards as the `/abacus-worker` skill. abacus-infra records and constrains dispatches
(logbook preconditions) but does not define meaning or authority.

Claude Code's `SendMessage` is the transport. This document defines what a message **means**: a message
authorizes only the bounded work it names.

## Addressing
Sessions are named `<role>:<repo>`: `coder:repo-a`, `agent:orchestrator` (successors: `agent:orchestrator-g2`, ...).
A lane's orchestrator is `agent:orchestrator-<lane>` (successors: `agent:orchestrator-<lane>-g2`, ...).

## Lanes
A lane is an independent line of work with its own orchestrator and its own decisions page
(`pages/decisions-<lane>.md`). The concierge opens lanes on demand, names them after the work, and tells the
operator the name. The logbook keeps each lane's goal (the operator's words), repositories and items, and refuses
(`LANE`) any claim or dispatch on a repository another active lane owns, so lanes never compete for a worker. Work
touching a lane's repositories joins that lane. A lane closes when its program completes, which releases its
repositories. Status questions are answered per lane: a question about one lane's work is answered from that lane
alone.
Names come from `abacus-session start`, never typed by hand. Workers reply to the `report_to` name in the dispatch.

## What the operator's verbs mean (operator ruling, 2026-10-13)
A standing default, so no one asks again. The operator: "build is the better word for what we would be doing here
than 'ship'. To-date, we are not packaging any software and deploying it. The farthest we will go right now is to
get something to a draft PR. … 'work on' is also a measure of advancement as tasks get more complicated."

| The operator says | It means | It's done when |
|---|---|---|
| **build X** (also "ship", "finish", "deliver", "do" X) | X and every bead X needs first (its `WAITS-ON` prerequisites, in any fleet repository), each run to done in dependency order | every one of those beads is closed and its commit verified: on the repository's default branch, or with `"landing": "draft-pr"` at the head of the bead's open draft PR (merging stays with people) |
| **work on X** (also "make a start on", "make progress on", "push X along") | advance X only | X reaches any report: `CLOSED`, `PROGRESS`, `BLOCKED` or `NEEDS-RULING` is a fine place to stop. Prerequisites in another repository are not started without asking |

These are meanings, not required words. The operator speaks plainly: map other wording onto build, work on or plan
(`/intake`) when the meaning is clear, and ask one question when it isn't ("compile X" might mean build it, or just
check it compiles). Never part of either: releases, tags, publishing or deploying. Those are the operator's alone,
so don't ask about them unless the operator's words mention a release, tag, deploy or PR. Read "ship" as **build**,
and if it matters, say once that nothing is released.

## Orchestrator → worker

### DISPATCH (authorizes exactly one bead)
```
DISPATCH <bead> (dispatch #<n>)
outcome: <what must be true when done, in the bead's own terms>
authority: run <bead> under its pipeline:<label> label; nothing else. <constraints, if any>
preconditions: <checkable facts, e.g. "repo-a commit 1a2b3c4 is on origin/<default branch>"; "none">
checks: <read-only commands abacus-verify runs on your report, e.g. `grep -q 1a2b3c4 vendor.json`; "none">
order: <place in the sequence; what waits on this>
validation: every acceptance criterion closed on evidence through abacus-finalize
report_to: agent:orchestrator
memory: <record identifiers returned by consult_memory, or "none returned">
```
Rules: under 1,500 characters. Names the outcome, never the implementation (no commands, no patches; `checks:` are
how the result will be *verified*, not instructions). The dispatch is recorded in the logbook (`dispatch add`, with
one `--check` per check) **before** it is sent, so a paused fleet, an attended repository, a duplicate, an unverified
prerequisite, a non-read-only check, or a ruling not yet relayed to that worker (`UNRELAYED`) refuses the send. Preconditions travel with the message
because a late HOLD cannot reliably stop work that has begun.

### HOLD / RESEQUENCE / CONTEXT
```
HOLD <bead|all>: <why>. Stop at the next stage boundary and report.
RESEQUENCE: <new order>. Authority unchanged.
CONTEXT <bead|general>: <information>. Authorizes nothing.
```

### RULING (relays the operator's words verbatim)
```
RULING <bead> (ruling <logbook id>)
question: <the question that was asked>
ruled: "<operator's exact words>"
recorded: <bead id where the JUDGEMENT row was written>
```
The ruling is stored in the logbook and on the bead **before** it is relayed. Sending a message whose first line is
`RULING <bead> (ruling <id>)` *is* the relay: the SendMessage hook records it, and the logbook refuses to dispatch a
bead covered by a ruling that its worker was never sent.

## Concierge → orchestrator

The concierge (`agent:concierge`) is the operator's front door. It records the operator's words verbatim
(`ruling add --where agent:concierge`) before handing them off:
```
HANDOFF <bead | "no item">: the operator said "<verbatim>" (ruling <id>, agent:concierge, <UTC time>).
LANE: <lane>
Wants: <the act>. Told them: <what the concierge already answered>.
INTENT: <what should be true afterwards, in the operator's terms>.
NOT ASKING FOR: <what the conversation ruled out>.
STATUS: decided | lean
```
`lean` is never acted on as chosen: the orchestrator replies with the question that would settle it. The
orchestrator acknowledges with `ACK HANDOFF ruling <id>: <next>` and messages the concierge when a NEEDS YOU card
appears or a program completes.

## Concierge ↔ planner

The planner (`agent:planner`) turns a source into draft beads. The concierge hands it requests with the same
`HANDOFF` grammar as above (Wants: `plan <source>`, or the operator's answer to a review). The planner answers:
```
PLAN-REVIEW <source> (ruling <id>)
repos: <repo>, <repo>
1. <repo>:<bead> "<title>" (draft)  proposed pipeline:<label>: <one reason>
   criteria: <n>: <the first one, shortened>
   waits on: <repo>:<bead> | nothing
2. ...
order: <bead> then <bead>
questions: <anything the planner couldn't settle | none>
```
The concierge shows it to the operator and records their answer verbatim, **with every draft bead it covers as a
`--target`**. Only then may the planner apply pipeline labels and lift `draft` (the guard checks those targets). After
applying an approval:
```
PLAN-APPLIED <source> (ruling <id>): <bead> pipeline:<label>, <bead> pipeline:<label>. Ready to build: "build <source>".
```
Jira and Confluence sources are TBD; GitHub issues, local files and pasted text are supported.

## Worker → orchestrator

### REPORT (a claim, never a state transition)
```
REPORT <bead> <CLOSED|BLOCKED|NEEDS-RULING|PROGRESS>
commit: <full sha or none> | pushed: <yes|no>
evidence: <verdict file / gate outcome / bead status / patch path>
ruling: <RULING-NEEDED: question | options a) ...; b) ... | recommended | why | where to answer> or none
next: <what you will do next, or what you are waiting for>
```
Gate evidence: the repository gate runs in the workflow's validate stage (under the heavy lock), and again in the
pre-push hook before the push is accepted. A worker doesn't re-run it by hand, and a report citing the workflow's
gate is complete. Only the worker's main loop reports. On receipt the orchestrator records the message and report, then runs
`abacus-verify` (bead closed on the owning board, commit reachable from origin, nothing unpushed, tree clean, and
with draft-PR landing the commit at the head of the bead's open PR)
before treating anything as done.

## Two limits, stated plainly
1. The format is a convention. No parser rejects a malformed message. Enforcement comes from logbook
   preconditions, tests over the skill files, and verification when a report arrives.
2. The worker side binds only repositories that adopted the `/abacus-worker` contract. The orchestrator's
   authority comes from the operator's recorded rulings and each repository's explicit adoption, not from the
   messaging tool.
