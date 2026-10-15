---
name: plan
description: Turn a source (GitHub issue, local file, pasted text) into draft beads on every fleet repository involved, wired in order with proposed pipeline labels, and send the operator one PLAN-REVIEW through the concierge. Use when a HANDOFF asks to plan something, or your launch prompt names a planning ruling.
---

# /plan

1. **Check the ruling.** `abacus-logbook show rulings`: the HANDOFF's ruling id, its words verbatim and
   `said_where: agent:concierge` must match. If not, reply to the concierge `HANDOFF <id> REFUSED: <why>` and stop.
2. **Read the source** (CLAUDE.md, "Sources"). Jira or Confluence: reply that it's TBD and ask for the text or a local
   file; stop. Note the source's canonical id: the issue URL, or the file's absolute path.
3. **Already planned?** `abacus-board find "<source>"` (and the title words). If beads exist for it, don't duplicate
   them: put what exists in the review and plan only what's missing.
4. **Which repositories.** `cat ~/.abacus/agents/fleet.json` lists the `coder:<repo>` repositories. Read the code that
   the source touches in each (Read, Grep, Glob; `git -C <repo> log`). `consult_memory` with the shape of the work and
   cite what returns. If you can't tell whether a repository is involved, list it under `questions:`.
5. **Draft the beads**, producer before consumer. For each, in its own repository (`cd <repo>`):
   - read the rules once: `cat <repo>/.claude/skills/bead-file/SKILL.md`
   - stamp: `git -C <repo> rev-parse --short HEAD`
   - file it as a draft, with real newlines:
     ```
     cd <repo> && bd create "<outcome as a title>" -t <feature|bug|task> -l draft --external-ref "<source>" \
       --acceptance "$(cat <<'AC'
     - <observable criterion, checkable inside this repository>
     AC
     )" --silent --body-file - <<'EOF'
     FILED AGAINST: <sha>
     SOURCE: <source>
     WAITS-ON <producer repo>:<producer bead> (<what must be true there>)   # consumers only

     <what and why; where it fits in the code; out of scope>
     EOF
     ```
   - a producer gets `bd label add <bead> export:<capability>`; its consumer gets
     `bd dep add <consumer> external:<producer repo>:<capability>`
   - read it back (`bd show <bead> --json`) and fix any mismatch in the stored acceptance
6. **Propose a pipeline label** for each draft, with one reason: `one-shot` (small, follows an existing pattern),
   `lite` (the default for real work), `full` (auth, crypto, migrations, many callers, or high uncertainty). Anything
   in the repository's `.abacus/config.json` `escalation_list` is never `one-shot`.
7. **Send one PLAN-REVIEW** to `agent:concierge` (grammar in the protocol), then close out the planning ruling, which
   names no bead: `abacus-logbook ruling recorded <id> --on none --reason "planned as <draft ids>"`. Wait for the
   operator's answer (it comes as a HANDOFF; use `/revise`).
