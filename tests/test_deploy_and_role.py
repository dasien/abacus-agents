import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STANDARDS = Path(os.environ.get("ABACUS_STANDARDS", ROOT.parent / "abacus-standards"))
DEPLOY = ROOT / "bin" / "abacus-deploy"


class DeployTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name).resolve() / "home"
        self.home.mkdir()
        (self.home / "fleet.json").write_text((ROOT / "fleet.example.json").read_text())
        self.env = dict(os.environ, ABACUS_HOME=str(self.home), PATH="/usr/bin:/bin")  # no `claude` on PATH

    def tearDown(self):
        self.tmp.cleanup()

    def deploy(self):
        p = subprocess.run([sys.executable, str(DEPLOY), "--standards", str(STANDARDS), "--allow-unpublished"],
                           env=self.env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)

    def test_deploy_writes_manifest_and_role(self):
        self.deploy()
        agents = self.home / "agents"
        manifest = json.loads((agents / ".deployed").read_text())
        self.assertIn("orchestrator/CLAUDE.md", manifest["files"])
        self.assertIn("hooks/guards.py", manifest["files"])
        self.assertTrue((agents / "orchestrator" / ".claude" / "skills" / "judgments" / "SKILL.md").exists())
        self.assertTrue((agents / "orchestrator" / "protocol" / "PROTOCOL.md").exists())
        for rt in ("state", "pages", "retros", "docs"):
            self.assertTrue((agents / "orchestrator" / rt).is_dir())

    def test_runtime_untouched_and_local_edits_overwritten(self):
        self.deploy()
        role = self.home / "agents" / "orchestrator"
        (role / "pages" / "decisions.md").write_text("operator-visible state")
        (role / "CLAUDE.md").write_text("I widened my own authority")
        out = self.deploy()
        self.assertIn("orchestrator", out["changed"])
        self.assertEqual((role / "pages" / "decisions.md").read_text(), "operator-visible state")
        self.assertEqual((role / "CLAUDE.md").read_text(), (ROOT / "roles/orchestrator/CLAUDE.md").read_text())

    def test_role_policy_fences_the_deployed_orchestrator(self):
        self.deploy()
        role = self.home / "agents" / "orchestrator"
        hook = self.home / "agents" / "hooks" / "guards.py"

        def call(tool, tool_input):
            payload = {"tool_name": tool, "tool_input": tool_input, "cwd": str(role), "session_id": "t"}
            env = dict(self.env, CLAUDE_PROJECT_DIR=str(role), ABACUS_ROLE="orchestrator")
            return subprocess.run([sys.executable, str(hook), "role-policy", "foreign-bd", "destructive-git",
                                   "operator-only"], input=json.dumps(payload), env=env,
                                  capture_output=True, text=True).returncode

        self.assertEqual(call("Bash", {"command": "cat <<EOF > pages/decisions.md\n# cards\nEOF"}), 0)
        self.assertEqual(call("Bash", {"command": "abacus-logbook digest"}), 0)
        self.assertEqual(call("Bash", {"command": "echo x > CLAUDE.md"}), 2)
        self.assertEqual(call("Bash", {"command": "echo x > .claude/settings.json"}), 2)
        self.assertEqual(call("Bash", {"command": "echo x > /tmp/elsewhere"}), 2)
        self.assertEqual(call("Bash", {"command": "cd ~/src/repo-a && touch src/app.py"}), 2)
        self.assertEqual(call("Write", {"file_path": str(role / "pages" / "x.md"), "content": "x"}), 0)
        self.assertEqual(call("Edit", {"file_path": "/Users/x/repo-a/app.py"}), 2)


class RoleDefinitionTest(unittest.TestCase):
    def test_orchestrator_agent_has_no_write_tools(self):
        text = (ROOT / "roles/orchestrator/.claude/agents/orchestrator.md").read_text()
        tools = re.search(r"^tools:(.*)$", text, re.M).group(1)
        for t in ("Edit", "Write", "NotebookEdit"):
            self.assertNotIn(t, [x.strip() for x in tools.split(",")])
        self.assertIn("initialPrompt: /recover", text)

    def test_skills_exist_for_every_procedure_named_in_claude_md(self):
        md = (ROOT / "roles/orchestrator/CLAUDE.md").read_text()
        for name in re.findall(r"`/([a-z-]+)`", md):
            if name == "judgments":
                continue  # deployed from abacus-standards
            self.assertTrue((ROOT / f"roles/orchestrator/.claude/skills/{name}/SKILL.md").exists(), name)

    def test_claude_md_stays_capped(self):
        self.assertLess(len((ROOT / "roles/orchestrator/CLAUDE.md").read_text().splitlines()), 80)

    def test_dispatch_template_carries_every_field(self):
        proto = (ROOT / "protocol/PROTOCOL.md").read_text()
        block = proto.split("### DISPATCH", 1)[1].split("```")[1]
        for field in ("outcome:", "authority:", "preconditions:", "checks:", "order:", "validation:", "report_to:",
                      "memory:"):
            self.assertIn(field, block)
        worker = (STANDARDS / "canonical/skills/abacus-worker/SKILL.md").read_text()
        report = proto.split("### REPORT", 1)[1].split("```")[1].strip()
        self.assertIn(report, worker, "worker contract REPORT format drifted from the protocol")


if __name__ == "__main__":
    unittest.main()


class SendMessageHookTest(unittest.TestCase):
    """The hook records the message and, for a RULING message, the relay that dispatches require."""

    def test_ruling_message_records_the_relay(self):
        tmp = tempfile.TemporaryDirectory()
        home = Path(tmp.name)
        (home / "bin").mkdir()
        infra = ROOT.parent / "abacus-infra"
        (home / "bin" / "abacus-logbook").symlink_to(infra / "bin" / "abacus-logbook")
        env = dict(os.environ, ABACUS_HOME=str(home))
        lb = [sys.executable, str(home / "bin" / "abacus-logbook")]
        subprocess.run(lb + ["ruling", "add", "--words", "A then B", "--where", "chat", "--target", "a-1"],
                       env=env, check=True, capture_output=True)
        hook = ROOT / "roles" / "hooks" / "sendmessage_log.py"
        for msg in ('RULING a-1 (ruling 1)\nquestion: order?\nruled: "A then B"\nrecorded: a-1', "CONTEXT fyi"):
            payload = {"tool_name": "SendMessage", "tool_input": {"to": "coder:repo-a", "message": msg}}
            p = subprocess.run([sys.executable, str(hook)], input=json.dumps(payload), env=env,
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
        out = subprocess.run(lb + ["show", "messages"], env=env, capture_output=True, text=True).stdout
        self.assertEqual(len(json.loads(out)), 2)
        import sqlite3
        conn = sqlite3.connect(str(home / "state" / "logbook.db"))
        self.assertEqual(conn.execute("SELECT ruling_id, worker FROM ruling_relays").fetchall(), [(1, "coder:repo-a")])
        conn.close(); tmp.cleanup()


class ConciergeTest(unittest.TestCase):
    """The operator's front door: read-only plus one write, may start only the orchestrator."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.home = Path(cls.tmp.name).resolve() / "home"
        cls.home.mkdir()
        (cls.home / "fleet.json").write_text((ROOT / "fleet.example.json").read_text())
        env = dict(os.environ, ABACUS_HOME=str(cls.home), PATH="/usr/bin:/bin")
        p = subprocess.run([sys.executable, str(DEPLOY), "--standards", str(STANDARDS), "--allow-unpublished"],
                           env=env, capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        cls.role = cls.home / "agents" / "concierge"

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def call(self, cmd, transcript=None):
        payload = {"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(self.role), "session_id": "t"}
        if transcript:
            payload["transcript_path"] = transcript
        env = dict(os.environ, ABACUS_HOME=str(self.home), CLAUDE_PROJECT_DIR=str(self.role), ABACUS_ROLE="concierge")
        hook = self.home / "agents" / "hooks" / "guards.py"
        return subprocess.run([sys.executable, str(hook), "role-policy", "role-commands", "foreign-bd",
                               "destructive-git", "operator-only", "secrets", "human-only"],
                              input=json.dumps(payload), env=env, capture_output=True, text=True).returncode

    def test_deployed_with_runtime_dirs(self):
        self.assertTrue((self.role / "CLAUDE.md").exists())
        self.assertTrue((self.role / ".claude" / "skills" / "intake" / "SKILL.md").exists())
        self.assertTrue((self.role / "state").is_dir())

    def test_reads_and_its_powers_are_allowed(self):
        tr = Path(self.tmp.name) / "t.jsonl"
        tr.write_text(json.dumps({"type": "user", "promptSource": "typed",
                                  "message": {"content": "ship repo-a then repo-b"}}) + "\n")
        for cmd in ("abacus-status", "abacus-logbook digest", "abacus-logbook show in-flight",
                    "cat ~/.abacus/agents/orchestrator/pages/decisions.md", "abacus-session list",
                    "cd /tmp/repo-a && bd show a-1 --json", "git -C /tmp/repo-a log --oneline -3",
                    "abacus-session start agent:orchestrator --prompt '/recover first, then act on the HANDOFF'",
                    "abacus-session start agent:orchestrator",
                    "abacus-session start agent:orchestrator --prompt '/recover first' "
                    "--reason 'operator: ship ledger (ruling r-1)'",
                    "abacus-session start agent:orchestrator --reason 'operator: ship ledger'"):
            self.assertEqual(self.call(cmd), 0, cmd)
        self.assertEqual(self.call('abacus-logbook ruling add --words "ship repo-a then repo-b" '
                                   '--where agent:concierge --target a-1 --target b-1', transcript=str(tr)), 0)

    def test_everything_else_is_refused(self):
        tr = Path(self.tmp.name) / "t2.jsonl"
        tr.write_text(json.dumps({"type": "user", "promptSource": "typed", "message": {"content": "hello"}}) + "\n")
        for cmd in ("abacus-logbook dispatch add a-1 --repo /x --worker coder:repo-a",
                    "abacus-logbook fact set fleet.paused false", "abacus-session start coder:repo-a",
                    "abacus-session start coder:repo-a --reason 'operator: ship'",
                    "abacus-session stop agent:orchestrator", "abacus-verify --repo /x --bead a-1 --record",
                    "cd /tmp/repo-a && bd create 'x'", "cd /tmp/repo-a && bd close a-1 --reason x",
                    "git commit -m x", "python3 -c 'print(1)'", "make test", "rm -rf /tmp/x",
                    "echo hi > pages/x.md", "bash -c 'abacus-logbook dispatch add a-1'"):
            self.assertEqual(self.call(cmd), 2, cmd)
        # its one write still has to quote words the operator really typed
        self.assertEqual(self.call('abacus-logbook ruling add --words "ship everything now" --where agent:concierge',
                                   transcript=str(tr)), 2)

    def test_lanes_open_and_start_their_orchestrators_but_nothing_more(self):
        for cmd in ('abacus-logbook lane open android --goal "build the login fix" --repo /tmp/android --item and-1',
                    "abacus-logbook lane show", 'abacus-logbook lane find "the android work"',
                    "abacus-logbook lane owner /tmp/android", "abacus-logbook lane rename android login-fix",
                    "abacus-status --lane android",
                    "abacus-session start agent:orchestrator-android --prompt '/recover first' --reason 'operator: x'"):
            self.assertEqual(self.call(cmd), 0, cmd)
        # negative controls: closing is the lane orchestrator's job; no workers; no odd session names
        for cmd in ("abacus-logbook lane close android", "abacus-session start coder:android",
                    "abacus-session start agent:orchestrator-Android --prompt x",
                    "abacus-session start agent:concierge-2 --prompt x",
                    "abacus-logbook dispatch add a-1 --repo /x --worker coder:a --lane android"):
            self.assertEqual(self.call(cmd), 2, cmd)

    def test_agent_definition_has_no_write_tools_and_starts_with_status(self):
        text = (ROOT / "roles/concierge/.claude/agents/concierge.md").read_text()
        tools = [t.strip() for t in re.search(r"^tools:(.*)$", text, re.M).group(1).split(",")]
        for t in ("Edit", "Write", "NotebookEdit", "Agent"):
            self.assertNotIn(t, tools)
        self.assertIn("initialPrompt: /status", text)
        self.assertIn("model: sonnet", text)

    def test_handoff_grammar_matches_the_protocol(self):
        proto = (ROOT / "protocol/PROTOCOL.md").read_text()
        block = proto.split("## Concierge → orchestrator", 1)[1].split("```")[1].strip()
        intake = (ROOT / "roles/concierge/.claude/skills/intake/SKILL.md").read_text()
        for line in block.splitlines():
            self.assertIn(line.split("<")[0].strip(), intake, line)
        self.assertIn("STATUS: decided | lean", intake)
        self.assertIn('--reason "operator: ', intake)

    def test_fleet_example_registers_the_concierge_on_demand_orchestrator(self):
        fleet = json.loads((ROOT / "fleet.example.json").read_text())["workers"]
        self.assertEqual(fleet["agent:concierge"]["agent"], "concierge")
        self.assertEqual(fleet["agent:concierge"]["permission_mode"], "auto")


class DefaultBranchTest(unittest.TestCase):
    """vbp: repositories don't all use main (bwcli-rs uses master); the skills must read the default branch."""

    def test_no_skill_assumes_main(self):
        for f in list((ROOT / "roles").rglob("SKILL.md")) + [ROOT / "protocol" / "PROTOCOL.md"]:
            text = f.read_text()
            for assumed in ("refs/heads/main", "origin/main"):
                self.assertNotIn(assumed, text, f"{f.relative_to(ROOT)} assumes {assumed}")

    def test_dispatch_and_recover_read_it(self):
        for skill in ("dispatch-bead", "recover"):
            text = (ROOT / "roles" / "orchestrator" / ".claude" / "skills" / skill / "SKILL.md").read_text()
            self.assertIn("ls-remote --symref origin HEAD", text, skill)
            self.assertIn("Never `git fetch`", text, skill)

    def test_dispatch_checks_cross_repo_conditions_itself(self):
        text = (ROOT / "roles" / "orchestrator" / ".claude" / "skills" / "dispatch-bead" / "SKILL.md").read_text()
        self.assertIn("Cross-repo conditions are yours to check, not the worker's", text)


class VocabularyTest(unittest.TestCase):
    """Operator ruling 2026-10-13: 'build' and 'work on' are the verbs; releases and tags are never asked about."""

    def test_protocol_defines_build_and_work_on(self):
        proto = (ROOT / "protocol" / "PROTOCOL.md").read_text()
        section = proto.split("## What the operator's verbs mean", 1)[1].split("\n## ", 1)[0]
        for phrase in ("**build X**", "**work on X**", "every bead X needs first", "Never part of either",
                       "draft PR"):
            self.assertIn(phrase, section)

    def test_intake_and_handoff_use_it(self):
        intake = (ROOT / "roles/concierge/.claude/skills/intake/SKILL.md").read_text()
        handoff = (ROOT / "roles/orchestrator/.claude/skills/handoff/SKILL.md").read_text()
        self.assertIn("Never list a prerequisite under NOT ASKING FOR", " ".join(intake.split()))
        self.assertIn("never ask about releases or tags", handoff)

    def test_file_proposals_passes_real_newlines(self):
        text = (ROOT / "roles/orchestrator/.claude/skills/file-proposals/SKILL.md").read_text()
        self.assertIn("--body-file -", text)
        self.assertNotIn('\\n\\nFrom retro', text)


class PlannerTest(unittest.TestCase):
    """agent:planner: plans as draft beads, read-only otherwise; deployed with its own guards (ABACUS_ROLE=planner)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.home = Path(cls.tmp.name).resolve() / "home"
        cls.home.mkdir()
        (cls.home / "fleet.json").write_text((ROOT / "fleet.example.json").read_text())
        env = dict(os.environ, ABACUS_HOME=str(cls.home), PATH="/usr/bin:/bin")
        p = subprocess.run([sys.executable, str(DEPLOY), "--standards", str(STANDARDS), "--allow-unpublished"],
                           env=env, capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        cls.role = cls.home / "agents" / "planner"
        cls.board = Path(cls.tmp.name).resolve() / "sdk"
        cls.board.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=cls.board, check=True)
        subprocess.run(["bd", "init", "--prefix", "sdk", "--quiet", "--skip-agents", "--skip-hooks",
                        "--non-interactive"],
                       cwd=cls.board, check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def call(self, cmd):
        payload = {"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(self.role), "session_id": "t"}
        settings = json.loads((self.role / ".claude" / "settings.json").read_text())
        hook_cmd = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        guards = hook_cmd.split("guards.py\" ", 1)[1].split()
        env = dict(os.environ, ABACUS_HOME=str(self.home), CLAUDE_PROJECT_DIR=str(self.role), ABACUS_ROLE="planner")
        hook = self.home / "agents" / "hooks" / "guards.py"
        return subprocess.run([sys.executable, str(hook), *guards], input=json.dumps(payload), env=env,
                              capture_output=True, text=True).returncode

    def test_deployed_with_skills_protocol_and_role_env(self):
        for f in ("CLAUDE.md", ".claude/skills/plan/SKILL.md", ".claude/skills/revise/SKILL.md",
                  "protocol/PROTOCOL.md", ".claude/role-policy.json"):
            self.assertTrue((self.role / f).exists(), f)
        settings = (self.role / ".claude" / "settings.json").read_text()
        self.assertIn("ABACUS_ROLE=planner", settings)
        self.assertIn("foreign-bd", settings)

    def test_plans_and_reads(self):
        b = self.board
        for cmd in ('abacus-board find "https://github.com/o/r/issues/1"', "abacus-logbook show rulings",
                    f"cd {b} && bd list --json", f"cd {b} && bd create 'Add heartbeat' -l draft --silent",
                    f"git -C {b} rev-parse --short HEAD", f"cat {b}/README.md", f"grep -rn heartbeat {b}",
                    "abacus-session stop agent:planner --reason 'plan applied'"):
            self.assertEqual(self.call(cmd), 0, cmd)

    def test_refuses_code_work_and_other_powers(self):
        b = self.board
        for cmd in (f"echo x > {b}/src.rs", f"cd {b} && git commit -m x", "make test", "cargo build",
                    "abacus-session start coder:sdk", "abacus-logbook ruling add --words 'approve' --where x",
                    "abacus-logbook dispatch add sdk-1 --repo /x --worker coder:sdk",
                    f"python3 -c \"open('{b}/x','w')\"", f"cd {b} && bd create 'No draft label' --silent",
                    f"cd {b} && bd delete sdk-1 --force"):
            self.assertEqual(self.call(cmd), 2, cmd)

    def test_agent_definition_and_fleet(self):
        text = (ROOT / "roles/planner/.claude/agents/planner.md").read_text()
        tools = [t.strip() for t in re.search(r"^tools:(.*)$", text, re.M).group(1).split(",")]
        for t in ("Edit", "Write", "MultiEdit", "NotebookEdit", "Agent"):
            self.assertNotIn(t, tools)
        self.assertIn("WebFetch", tools)
        self.assertIn("model: opus", text)
        fleet = json.loads((ROOT / "fleet.example.json").read_text())["workers"]
        self.assertEqual(fleet["agent:planner"]["model"], "opus")
        self.assertEqual(fleet["agent:planner"]["authority_check"], "deployed")

    def test_concierge_routes_plans_and_may_start_only_these_sessions(self):
        policy = json.loads((ROOT / "roles/concierge/.claude/role-policy.json").read_text())["commands"]
        self.assertIn("abacus-session start agent:planner --prompt *", policy)
        self.assertIn("abacus-board find *", policy)
        intake = " ".join((ROOT / "roles/concierge/.claude/skills/intake/SKILL.md").read_text().split())
        self.assertIn("every draft bead in the review it covers", intake)
        self.assertIn("Jira and Confluence are **TBD**", intake)

    def test_protocol_defines_the_plan_messages(self):
        proto = (ROOT / "protocol" / "PROTOCOL.md").read_text()
        for line in ("PLAN-REVIEW <source> (ruling <id>)", "PLAN-APPLIED <source> (ruling <id>)"):
            self.assertIn(line, proto)
        for skill in ("plan", "revise"):
            text = (ROOT / "roles" / "planner" / ".claude" / "skills" / skill / "SKILL.md").read_text()
            self.assertIn("PLAN-REVIEW" if skill == "plan" else "PLAN-APPLIED", text)


class FixesFromThePlannerRunTest(unittest.TestCase):
    """0.7.1: allowlists that fit the work, approval rulings left for the orchestrator, ids on rows, page checks."""

    def test_allowlists(self):
        planner = json.loads((ROOT / "roles/planner/.claude/role-policy.json").read_text())["commands"]
        for cmd in ("git grep *", "git branch *", "git show *", "git ls-files *"):
            self.assertIn(cmd, planner)
        concierge = json.loads((ROOT / "roles/concierge/.claude/role-policy.json").read_text())["commands"]
        self.assertIn("sed -n *", concierge)

    def test_revise_never_records_the_approval_on_a_bead(self):
        text = (ROOT / "roles/planner/.claude/skills/revise/SKILL.md").read_text()
        self.assertNotIn("ruling recorded <id> --on <first approved bead>", text)
        self.assertIn("Leave the approval ruling as it is", text)

    def test_relay_writes_the_ruling_id_and_recover_checks_the_page(self):
        relay = (ROOT / "roles/orchestrator/.claude/skills/relay-ruling/SKILL.md").read_text()
        self.assertIn("ruling: #<id>", relay)
        recover = (ROOT / "roles/orchestrator/.claude/skills/recover/SKILL.md").read_text()
        self.assertIn("**The decisions page.**", recover)


class LanesAgreeTest(unittest.TestCase):
    """0.10.0: the protocol, the orchestrator, the concierge and the fleet agree on lanes."""

    def test_lanes_are_described_where_each_agent_reads_them(self):
        proto = (ROOT / "protocol" / "PROTOCOL.md").read_text()
        self.assertIn("## Lanes", proto)
        self.assertIn("agent:orchestrator-<lane>", proto)
        orch = (ROOT / "roles/orchestrator/CLAUDE.md").read_text()
        for phrase in ("pages/decisions-<lane>.md", "--lane <lane> --report-to", "abacus-logbook lane close <lane>"):
            self.assertIn(phrase, orch)
        intake = " ".join((ROOT / "roles/concierge/.claude/skills/intake/SKILL.md").read_text().split())
        self.assertIn("abacus-logbook lane owner <repo path>", intake)
        self.assertIn("Started the **<lane>** lane", intake)
        status = " ".join((ROOT / "roles/concierge/.claude/skills/status/SKILL.md").read_text().split())
        self.assertIn("Answer only what was asked", status)
        self.assertIn("abacus-status --lane <lane>", status)
        fleet = json.loads((ROOT / "fleet.example.json").read_text())["workers"]
        self.assertTrue(fleet["agent:orchestrator"]["lanes"])

