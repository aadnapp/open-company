#!/usr/bin/env python3
"""Append one line to the Open Company activity log, read by build_report.py / build_digests.py.

Two uses:
  1. An Agent in an IDE session records what it is doing (see .kiro/steering/activity-log.md):
       log_activity.py --role 固件研发与实测 --kind done "A/B 录音通过，出声比安静高 10-28 dB"
  2. A Kiro Stop hook records a heartbeat after each Agent turn, so the report shows that a
     session was active even when nothing was logged:
       log_activity.py --heartbeat        (reads and discards the hook's JSON on stdin)

Output: ~/.local/state/open-company/activity/<YYYY-MM-DD>.jsonl, one JSON object per line:
  {"ts": "2026-11-11T09:17:05", "role": "...", "product": "...", "kind": "done",
   "text": "...", "ref": "<optional path>", "source": "ide"}
Heartbeats: {"ts": ..., "kind": "heartbeat", "source": "hook", "workspace": "<cwd>", "ctx_keys": [...]}
Only the key names of the hook's stdin JSON are kept, never the values (they may hold chat text).

Python 3.8+, standard library only. Writes local files only.
"""
import argparse
import datetime as dt
import fcntl
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_report import KINDS, STATE, known_roles  # noqa: E402

HEARTBEAT_GAP = dt.timedelta(minutes=10)  # at most one heartbeat per workspace in this window


def log_path(day):
    d = STATE / "activity"
    d.mkdir(parents=True, exist_ok=True)
    return d / ("%s.jsonl" % day.isoformat())


def append(path, rec):
    line = json.dumps(rec, ensure_ascii=False) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(line)
        fcntl.flock(f, fcntl.LOCK_UN)


def last_heartbeat(path, workspace):
    if not path.exists():
        return None
    last = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("kind") == "heartbeat" and r.get("workspace") == workspace:
            last = r["ts"]
    return dt.datetime.fromisoformat(last) if last else None


def heartbeat(now):
    keys = []
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        try:
            obj = json.loads(raw) if raw.strip() else {}
            keys = sorted(obj) if isinstance(obj, dict) else []
        except ValueError:
            keys = ["<non-json stdin>"]
    workspace = os.getcwd()
    path = log_path(now.date())
    prev = last_heartbeat(path, workspace)
    if prev and now - prev < HEARTBEAT_GAP:
        return 0
    append(path, {"ts": now.isoformat(), "kind": "heartbeat", "source": "hook",
                  "workspace": workspace, "ctx_keys": keys})
    return 0


def main():
    roles = known_roles()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--heartbeat", action="store_true", help="record a session heartbeat (for the Stop hook)")
    ap.add_argument("--role", choices=sorted(roles), help="role name as shown in the report")
    ap.add_argument("--kind", choices=[k for k in KINDS if k != "heartbeat"], default="progress",
                    help="start / progress / done / blocked / waiting (default progress)")
    ap.add_argument("--ref", help="optional evidence path or URL")
    ap.add_argument("--source", default="ide", help="who is writing (default ide; cron tasks may pass cron)")
    ap.add_argument("text", nargs="?", help="one sentence: what was done, found, or is blocking")
    a = ap.parse_args()
    now = dt.datetime.now().replace(microsecond=0)

    if a.heartbeat:
        try:
            return heartbeat(now)
        except Exception as e:  # a broken heartbeat must never disturb the IDE session
            print("heartbeat skipped: %s" % e, file=sys.stderr)
            return 0

    if not a.role or not a.text:
        ap.error("--role and text are required (unless --heartbeat)")
    rec = {"ts": now.isoformat(), "role": a.role, "product": roles[a.role], "kind": a.kind,
           "text": " ".join(a.text.split()), "source": a.source}
    if a.ref:
        rec["ref"] = a.ref
    path = log_path(now.date())
    append(path, rec)
    print("logged to %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
