#!/usr/bin/env python3
"""Copy new IDE chat messages (user prompts and visible Agent replies) into the Open Company chat log.

Called by log_activity.py --heartbeat (Kiro Stop hook), so it runs after every Agent turn.

Reads Kiro session transcripts:
  ~/.kiro/sessions/<workspace-hash>/sess_<id>/session.json    (title, workspacePaths)
  ~/.kiro/sessions/<workspace-hash>/sess_<id>/messages.jsonl  (the turn-by-turn record)

Keeps only:
  - payload.type == "user"                                 -> the user's own words
  - payload.type == "assistant" with operationType == "Say" -> what the Agent actually said
Drops: reasoning ("operationType": "Reasoning"), tool_call/tool_result, steering_inclusion,
context_snapshot/agent_note, attached file/folder contents, images.

Each kept text is secret-redacted (best effort, see REDACT_RE) and truncated to MAX_CHARS.
Only sessions whose session.json workspacePaths intersect WORKSPACES are captured, so chat from
unrelated projects on this machine never enters this repo's report.

Output: ~/.local/state/open-company/chat/<YYYY-MM-DD>.jsonl, one JSON object per line:
  {"ts": "...", "session": "sess_...", "title": "...", "workspace": "<first matching root>",
   "who": "user" | "assistant", "text": "..."}

Progress (so a message is captured once even though this runs every turn) is kept in
~/.local/state/open-company/chat/offsets.json: {"<transcript path>": <lines already read>}.

Python 3.8+, standard library only. Never sends anything over the network.
"""
import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path

STATE = Path(os.environ.get("OPEN_COMPANY_STATE_DIR", Path.home() / ".local/state/open-company"))
SESSIONS_DIR = Path.home() / ".kiro/sessions"
CHAT_DIR = STATE / "chat"
OFFSETS_FILE = CHAT_DIR / "offsets.json"
MAX_CHARS = 2000
# Only capture sessions rooted at one of these workspaces (avoid leaking unrelated project chat).
WORKSPACES = {
    "/home/whole/data/src/open-company",
    "/home/whole/data/reawork/weband",
}
REDACT_RE = re.compile(
    r"(?i)\b("
    r"(?:api|secret|access)[_-]?key|token|password|passwd|bearer\s+\S+|"
    r"AKIA[0-9A-Z]{16}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----"
    r")\b"
)


def redact(text):
    # Conservative best-effort scrub; this is a convenience log, not a security boundary.
    text = re.sub(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
                  "[redacted private key]", text, flags=re.S)
    text = re.sub(r"(?i)\b(api[_-]?key|secret|token|password|passwd)\s*[=:]\s*\S+", r"\1=[redacted]", text)
    text = re.sub(r"\bAKIA[0-9A-Z]{16}\b", "[redacted aws key]", text)
    return text


def load_offsets():
    if OFFSETS_FILE.exists():
        try:
            return json.loads(OFFSETS_FILE.read_text(encoding="utf-8"))
        except ValueError:
            return {}
    return {}


def save_offsets(offsets):
    CHAT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = OFFSETS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(offsets), encoding="utf-8")
    tmp.replace(OFFSETS_FILE)


def matching_workspace(roots):
    for r in roots or []:
        if r in WORKSPACES:
            return r
    return None


def iter_transcripts():
    if not SESSIONS_DIR.exists():
        return
    for session_json in SESSIONS_DIR.glob("*/sess_*/session.json"):
        messages = session_json.parent / "messages.jsonl"
        if messages.exists():
            yield session_json, messages


def day_path(d):
    CHAT_DIR.mkdir(parents=True, exist_ok=True)
    return CHAT_DIR / ("%s.jsonl" % d.isoformat())


def capture():
    offsets = load_offsets()
    out_files = {}
    written = 0
    for session_json, messages in iter_transcripts():
        try:
            meta = json.loads(session_json.read_text(encoding="utf-8", errors="replace"))
        except ValueError:
            continue
        ws = matching_workspace(meta.get("workspacePaths"))
        if not ws:
            continue
        key = str(messages)
        start = offsets.get(key, 0)
        lines = messages.read_text(encoding="utf-8", errors="replace").splitlines()
        if start >= len(lines):
            continue
        for line in lines[start:]:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            payload = rec.get("payload", {})
            ptype = payload.get("type")
            who = None
            if ptype == "user":
                who = "user"
            elif ptype == "assistant" and payload.get("operationType") == "Say":
                who = "assistant"
            if not who:
                continue
            text = (payload.get("content") or "").strip()
            if not text:
                continue
            text = redact(text)
            if len(text) > MAX_CHARS:
                text = text[:MAX_CHARS] + " …[截断]"
            ts = rec.get("timestamp")
            try:
                t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().replace(tzinfo=None)
            except (ValueError, AttributeError):
                t = dt.datetime.now()
            out = out_files.setdefault(t.date(), [])
            out.append({"ts": t.isoformat(timespec="seconds"), "session": session_json.parent.name,
                        "title": meta.get("title") or "", "workspace": ws, "who": who, "text": text})
            written += 1
        offsets[key] = len(lines)
    for day, recs in out_files.items():
        p = day_path(day)
        with open(p, "a", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    save_offsets(offsets)
    return written


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.parse_args()
    n = capture()
    print("captured %d new chat message(s)" % n)
