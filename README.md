# abacus-agents

The agents repository for [Abacus](https://github.com/dasien/abacus): the builder repo for the constrained Claude Code roles that coordinate
work and never write code, and the canonical home of the **coordination protocol**. Each role is deployed to
`~/.abacus/agents/<role>`, out of its own reach. Until 0.4.0 this repository was called `abacus-orchestrator`.

```
roles/concierge/         the operator's front door (Sonnet, no Edit/Write, command allowlist). Skills: status, intake
                         (verbatim ruling, then a HANDOFF to the planner or orchestrator). Design: docs/CONCIERGE.md
roles/planner/           turns a source into draft beads across fleet repos for the operator's review (Opus, no
                         Edit/Write, WebFetch, command allowlist, foreign-bd draft rules). Skills: plan, revise
roles/orchestrator/      CLAUDE.md (8 binding rules), no Edit/Write, role-policy fence, foreign-bd, SendMessage
                         logger. Skills: recover, handoff, dispatch-bead, verify-report, relay-ruling,
                         file-proposals, check-in, hand-over, decisions-page
roles/hooks/             sendmessage_log.py: logs every outbound message and records a RULING message as the
                         relay (guards and redaction come from abacus-standards at deploy)
protocol/PROTOCOL.md     the operator's verbs (plan / build / work on); DISPATCH (incl. checks:) / HOLD /
                         RESEQUENCE / CONTEXT / RULING / REPORT; HANDOFF; PLAN-REVIEW / PLAN-APPLIED
fleet.example.json       worker registry template (the real one is ~/.abacus/fleet.json)
bin/abacus-deploy        deploy roles to ~/.abacus/agents from a published commit, with a manifest
```

A running agent cannot modify its own definition. Changes are made here, published, and deployed. A
direct edit in `~/.abacus/agents` is overwritten on the next deploy. Run tests with `make test`.
