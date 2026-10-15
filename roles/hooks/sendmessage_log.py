#!/usr/bin/env python3
"""PreToolUse hook for SendMessage: record the exact message submitted, before it is sent.

The conversation compacts; the logbook does not. Never blocks the send: a logbook
failure is reported on stderr so the session can notice and record it by hand.
"""
import json
import os
import re
import subprocess
import sys

RULING_LINE = re.compile(r"^RULING\s+\S+\s+\(ruling\s+(\d+)\)")

LOGBOOK = os.path.join(os.environ.get("ABACUS_HOME", os.path.expanduser("~/.abacus")), "bin", "abacus-logbook")


def main():
    try:
        data = json.loads(sys.stdin.read())
    except ValueError:
        return 0
    ti = data.get("tool_input") or {}
    peer = ti.get("to") or ti.get("recipient") or "unknown"
    body = ti.get("message") or ti.get("content") or ""
    if not isinstance(body, str):
        body = json.dumps(body)
    if not body.strip() and ti.get("notify_when_idle"):
        body = "[notify_when_idle subscription: wake me when this session goes idle]"
    try:
        p = subprocess.run([LOGBOOK, "msg", "out", "--peer", str(peer), "--delivery", "submitted"],
                           input=body, capture_output=True, text=True, timeout=20)
        if p.returncode != 0:
            print(f"[abacus] message to {peer} NOT recorded in logbook: {p.stderr.strip()}", file=sys.stderr)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"[abacus] message to {peer} NOT recorded in logbook: {e}", file=sys.stderr)
    # A RULING message is the relay: record it from the text actually sent, so dispatches can require it.
    m = RULING_LINE.match(body.strip())
    if m:
        try:
            p = subprocess.run([LOGBOOK, "ruling", "relayed", m.group(1), "--to", str(peer)],
                               capture_output=True, text=True, timeout=20)
            if p.returncode != 0:
                print(f"[abacus] relay of ruling {m.group(1)} to {peer} NOT recorded: {p.stderr.strip()}",
                      file=sys.stderr)
        except (OSError, subprocess.SubprocessError) as e:
            print(f"[abacus] relay of ruling {m.group(1)} to {peer} NOT recorded: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
