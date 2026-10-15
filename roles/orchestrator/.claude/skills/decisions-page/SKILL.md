---
name: decisions-page
description: Maintain pages/decisions.md, the one place the operator looks for what is waiting on them. Use whenever a decision needs the operator, when the orchestrator decides within delegated authority, or when an operator step is required.
---

# /decisions-page

`pages/decisions.md` holds one card per item, in three kinds:

1. **NEEDS YOU**: a decision only the operator can make. Context in two lines, options each with a pro and a con,
   your recommendation with confidence, and the review clause you propose.
2. **DECIDED (within delegated authority)**: a record, not a request. What you decided, the delegation relied on, the
   recorded row. The operator may overrule; no action is required.
3. **OPERATOR STEP**: an act only the operator performs (release, credential, guard change), and the session in which
   to perform it.

End the page with **Program status**: `RUNNING` (what is in flight), `WAITING ON YOU` (which card), or `COMPLETE`
(each bead with its verified sha, workers stopped, the retrospective's path). Write `COMPLETE` only after every dispatch
is verified and closed.

Rules:
- Rewrite the whole page from durable sources each time (`abacus-logbook show rulings`, bead notes, open promises),
  using a heredoc redirect into `pages/decisions.md` (your only writable paths are `state/ pages/ retros/ docs/`).
- **Cap open NEEDS YOU cards** at the value of `abacus-logbook fact get decisions.cap` (default 5 if unset). At the cap,
  dispatch only work that can raise no ruling.
- Every card says **where to answer: agent:concierge** (in Agent View). When you add a NEEDS YOU card or reach
  `COMPLETE`, also send `agent:concierge` a one-line note (if it is live, per `abacus-session list`), so the operator
  hears it the next time they switch to the concierge. The status line shows the count in every session meanwhile.
