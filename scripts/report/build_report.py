#!/usr/bin/env python3
"""Build a self-contained HTML progress report of what each Open Company role did.

Reads (all local, nothing is sent anywhere):
  ~/.local/state/open-company/logs/<task>-<date>.log   cron runner log (run-task.sh)
  ~/.local/state/open-company/runs/<task>/<ts>/digest.md
  ~/.local/state/open-company/activity/<date>.jsonl    activity log (log_activity.py: IDE sessions + Stop-hook heartbeats)
  ~/.local/state/open-company/chat/<date>.jsonl        chat log (capture_chat.py: user prompts + Agent replies, via Stop hook)
  ~/.local/state/open-company/needs-owner.log
  /proc/*/cmdline                                       to tell which cron tasks are running right now
  <repo>/companies/*/products/*/goal.md, handoff.md
  evidence digests listed in MANUAL_ROLES

Writes ~/.local/state/open-company/report/index.html (no scripts, no external assets).

Section order is fixed by SECTION_ORDER below (data-freshness line first, then the sections in that list).

Usage: build_report.py [--days N] [--out PATH]
Python 3.8+, standard library only.
"""
import argparse
import datetime as dt
import html
import json
import os
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STATE = Path(os.environ.get("OPEN_COMPANY_STATE_DIR", Path.home() / ".local/state/open-company"))

# Scheduled cron roles: task id -> (role label, product). Keep in sync with scripts/cron/crontab.example.
# OpenCompare is a reference template only, so its triage and release roles are not listed.
# To bring them back, add e.g. "github-issue-pr-actions": ("盯盘分诊", "OpenCompare").
ROLES = {
    "daily-patrol": ("晚间复盘", "团队"),
}
# Products kept only as reference templates: not shown in the progress section, not reconciled by daily-patrol
TEMPLATE_PRODUCTS = {"open-compare"}
# Roles worked by hand in IDE sessions: (role, product, evidence digest or None).
# They report through the activity log (log_activity.py); the evidence digest is the
# product's own append-only step log, shown as a second source.
MANUAL_ROLES = [
    ("固件研发与实测", "Weband", Path("/home/whole/data/reawork/weband/evidence/digest.md")),
    ("团队运营", "团队", None),  # work on this repo itself: rules, cron, report scripts
]
# Activity kinds accepted by log_activity.py, in report order
KINDS = {"start": "开始", "progress": "进展", "done": "完成", "blocked": "受阻", "waiting": "等人", "heartbeat": "会话心跳"}
# 报告各节的固定顺序（key, 标题）。改顺序只改这里，并同步 docs/operator-manual.md 第 2 节。
SECTION_ORDER = [
    ("roles", "各角色概览"),
    ("todo", "产品待办与待人处理（handoff.md 待办清单 / needs-owner.log）"),
    ("activity", "今日活动（IDE 会话与任务记录，新的在上）"),
    ("chat", "今日对话记录（用户与 Agent 原文，新的在上）"),
    ("history", "历史对话（按日期折叠，新的在上）"),
    ("digests", "今日各角色 digest"),
    ("timeline", "时间线（每格 1 小时，悬停看明细）"),
    ("runs", "Agent 运行记录"),
    ("manual", "手动任务（证据 digest）"),
]
REFRESH_MINUTE = 7  # first cron rebuild of each hour (crontab: capture_chat + build_digests + build_report)
REFRESH_EVERY = 10   # minutes between cron rebuilds (crontab.example: 7-59/10)

LINE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[([\w-]+)\] (.*)$")
COLORS = {"err": "#d64545", "woke": "#2f6fdb", "run": "#1f9d55", "ok": "#b9c2cc", "skip": "#e0a100",
          "act": "#7b5cd6", "hb": "#cdbff2"}
LABELS = {"ok": "检查无事件", "woke": "有事件唤醒", "run": "Agent 运行", "err": "出错 / 受阻", "skip": "跳过 / 等人",
          "act": "IDE 记录了进展", "hb": "IDE 会话有活动（只有心跳）"}
# activity kind -> timeline colour key
ACT_COLOR = {"start": "act", "progress": "act", "done": "act", "blocked": "err", "waiting": "skip", "heartbeat": "hb"}
HB_ROW = "IDE 会话心跳"


def known_roles():
    """role name -> product, for every role that may write to the activity log."""
    roles = {role: product for role, product in ROLES.values()}
    roles.update({r: p for r, p, _ in MANUAL_ROLES})
    return roles


def esc(s):
    return html.escape(str(s), quote=True)


def classify(msg):
    if "guard exit=1" in msg:
        return "ok"
    if "guard exit=0" in msg:
        return "woke"
    if "guard exit=" in msg or msg.startswith("error:"):
        return "err"
    if msg.startswith("start:"):
        return "run"
    if msg.startswith("skip:"):
        return "skip"
    return None


def read_events(since):
    events = []  # (datetime, task, kind, msg)
    for f in sorted((STATE / "logs").glob("*.log")):
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            m = LINE_RE.match(line)
            if not m:
                continue
            t = dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
            if t < since:
                continue
            events.append((t, m.group(2), classify(m.group(3)), m.group(3)))
    events.sort()
    return events


def read_runs(events):
    """Pair start/end lines into runs and attach digest info."""
    runs, open_runs = [], {}
    for t, task, _kind, msg in events:
        if msg.startswith("start: run_dir="):
            if task in open_runs:  # previous run never logged an end: it was killed or crashed
                runs.append(open_runs.pop(task))
            open_runs[task] = {"task": task, "start": t, "end": None, "exit": None,
                               "dir": Path(msg.split("=", 1)[1])}
        elif msg.startswith("end: exit=") and task in open_runs:
            r = open_runs.pop(task)
            r["end"], r["exit"] = t, msg.split("=", 1)[1]
            runs.append(r)
    runs.extend(open_runs.values())  # still running or killed
    for r in runs:
        d = r["dir"] / "digest.md"
        r["digest"] = d if d.exists() else None
        r["highlights"], r["needs_owner"] = [], False
        if r["digest"]:
            text = r["digest"].read_text(encoding="utf-8", errors="replace")
            r["needs_owner"] = bool(re.search(r"^[\s*-]*`?needsOwner:\s*true`?\s*$", text, re.M))
            for sec in ("收工结论", "结果", "结论"):
                m = re.search(r"^##+ *%s.*?\n(.*?)(?=^##|\Z)" % sec, text, re.M | re.S)
                if m:
                    r["highlights"] = [l.strip("- ").strip() for l in m.group(1).splitlines() if l.strip()][:4]
                    break
            if not r["highlights"]:
                r["highlights"] = [l.strip("- ").strip() for l in text.splitlines()
                                   if l.startswith("- ") and ("判定" in l or "blocked" in l)][:4]
    runs.sort(key=lambda r: r["start"], reverse=True)
    return runs


def read_chat(since):
    """Chat log records at or after `since`, oldest first. Written by capture_chat.py (Stop hook)."""
    out = []
    d = STATE / "chat"
    for f in sorted(d.glob("*.jsonl")) if d.exists() else []:
        try:
            day = dt.date.fromisoformat(f.stem)
        except ValueError:
            continue
        if day < since.date():
            continue
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(line)
                r["t"] = dt.datetime.fromisoformat(r["ts"])
            except (ValueError, KeyError, TypeError):
                continue
            if r["t"] >= since:
                out.append(r)
    out.sort(key=lambda r: r["t"])
    return out


WAIT_WORDS = ("是否", "要不要", "需要我", "需要人", "确认", "请问", "？", "?")
BLOCK_WORDS = ("blocked", "受阻", "卡住", "缺", "失败", "出错", "error")


def first_sentence(text, limit=90):
    """First line / sentence of a message, cut to `limit` chars, for use as a one-line highlight."""
    if not text:
        return ""
    head = text.strip().splitlines()[0].strip()
    for sep in ("。", ". ", "！", "!", "\n"):
        i = head.find(sep)
        if 0 < i < limit:
            head = head[:i + 1]
            break
    return (head[:limit] + "…") if len(head) > limit else head


def chat_sessions(chat, day):
    """Group today's chat messages by session and reduce each to a one-line highlight.

    `kiro 的一句话摘要`：用户诉求取第一条 user 消息，结果/现状取最后一条 assistant 消息，
    不调用模型，纯文本规则，保证离线、可复现。"""
    rows = [r for r in chat if r["t"].date() == day]
    by_session = defaultdict(list)
    for r in rows:
        by_session[r.get("session", "")].append(r)
    sessions = []
    for sid, msgs in by_session.items():
        msgs.sort(key=lambda r: r["t"])
        users = [m for m in msgs if m["who"] == "user"]
        agents = [m for m in msgs if m["who"] == "assistant"]
        last_agent_text = agents[-1]["text"] if agents else ""
        waiting = any(w in last_agent_text for w in WAIT_WORDS)
        blocked = any(w in last_agent_text.lower() for w in BLOCK_WORDS)
        sessions.append({
            "session": sid, "title": msgs[0].get("title") or sid, "msgs": msgs,
            "start": msgs[0]["t"], "end": msgs[-1]["t"], "n_user": len(users), "n_agent": len(agents),
            "ask": first_sentence(users[0]["text"]) if users else "（无用户发言，只有 Agent 输出）",
            "result": first_sentence(last_agent_text) if agents else "（Agent 还没有回复）",
            "waiting": waiting, "blocked": blocked,
        })
    sessions.sort(key=lambda s: s["end"], reverse=True)
    return sessions


def chat_table(chat, day):
    sessions = chat_sessions(chat, day)
    if not sessions:
        return ("<p>今天还没有对话记录。由 Stop hook 调用 <code>scripts/report/capture_chat.py</code> "
                "从 Kiro 会话记录中摘取。</p>")
    cards = []
    for s in sessions:
        tag = ""
        if s["blocked"]:
            tag = '<span class="tag bad">受阻/出错</span>'
        elif s["waiting"]:
            tag = '<span class="tag warn">等待确认</span>'
        detail_rows = "".join(
            '<tr><td>%s</td><td class="who-%s">%s</td><td>%s</td></tr>'
            % (esc(m["t"].strftime("%H:%M:%S")), esc(m["who"]), esc("用户" if m["who"] == "user" else "Agent"),
               esc(m["text"]))
            for m in s["msgs"])
        cards.append(
            '<div class="card chat-card"><h3>%s %s<small>%s–%s · %d 条用户发言 / %d 条 Agent 回复</small></h3>'
            '<p><b>诉求：</b>%s</p><p><b>结果/现状：</b>%s</p>'
            '<details><summary>查看完整对话（%d 条）</summary>'
            '<table><thead><tr><th scope="col">时间</th><th scope="col">角色</th><th scope="col">内容</th></tr></thead>'
            '<tbody>%s</tbody></table></details></div>'
            % (esc(s["title"]), tag, esc(s["start"].strftime("%H:%M")), esc(s["end"].strftime("%H:%M")),
               s["n_user"], s["n_agent"], esc(s["ask"]), esc(s["result"]), len(s["msgs"]), detail_rows))
    return '<div class="grid">%s</div>' % "\n".join(cards)


HIST_JS = """<script>
(function(){
  var q=document.getElementById('hist-q'),n=document.getElementById('hist-n');
  if(!q)return;
  var days=[].slice.call(document.querySelectorAll('#hist .hist-day'));
  q.addEventListener('input',function(){
    var k=q.value.trim().toLowerCase(),hit=0;
    days.forEach(function(d){
      var any=false;
      [].forEach.call(d.querySelectorAll('.chat-card'),function(c){
        var m=!k||c.textContent.toLowerCase().indexOf(k)>=0;
        c.style.display=m?'':'none';
        if(m)any=true;
      });
      hit+=any&&k?[].filter.call(d.querySelectorAll('.chat-card'),function(c){return c.style.display!=='none'}).length:0;
      d.style.display=any?'':'none';
      d.open=!!k&&any;
    });
    n.textContent=k?('匹配 '+hit+' 个会话'):'';
  });
})();
</script>"""


def chat_history(chat, today):
    """Chat of all earlier days, newest day first, one collapsible block per day."""
    days = sorted({r["t"].date() for r in chat if r["t"].date() < today}, reverse=True)
    if not days:
        return "<p>没有更早的对话记录。</p>"
    blocks = []
    for d in days:
        n = len(chat_sessions(chat, d))
        blocks.append('<details class="hist-day"><summary>%s · %d 个会话</summary>%s</details>'
                      % (esc(d.isoformat()), n, chat_table(chat, d)))
    box = ('<p><input id="hist-q" type="search" placeholder="搜索历史对话关键词（会话标题、诉求、对话原文）" '
           'aria-label="搜索历史对话" style="width:min(480px,100%%);padding:6px 8px">'
           ' <span id="hist-n" class="meta"></span></p>')
    return box + '<div id="hist">' + "\n".join(blocks) + '</div>' + HIST_JS


def read_needs_owner():
    f = STATE / "needs-owner.log"
    return f.read_text(encoding="utf-8", errors="replace").splitlines() if f.exists() else []


def read_activity(since):
    """Activity log records at or after `since`, oldest first. Bad lines are skipped."""
    out = []
    d = STATE / "activity"
    for f in sorted(d.glob("*.jsonl")) if d.exists() else []:
        try:
            day = dt.date.fromisoformat(f.stem)
        except ValueError:
            continue
        if day < since.date():
            continue
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(line)
                r["t"] = dt.datetime.fromisoformat(r["ts"])
            except (ValueError, KeyError, TypeError):
                continue
            if r["t"] >= since and r.get("kind") in KINDS:
                out.append(r)
    out.sort(key=lambda r: r["t"])
    return out


def running_tasks():
    """Cron tasks with a live run-task.sh process. Reads /proc only; never touches the task locks,
    because run-task.sh uses `flock -n` and even a brief probe could make a real run skip."""
    found = set()
    for p in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            argv = p.read_bytes().split(b"\0")
        except OSError:
            continue
        for i, a in enumerate(argv[:-1]):
            if a.endswith(b"run-task.sh"):
                found.add(argv[i + 1].decode("utf-8", "replace"))
    return found & set(ROLES)


def read_products():
    out = []
    for pdir in sorted(REPO.glob("companies/*/products/*")):
        if not (pdir / "Productfile.yaml").exists() or pdir.name in TEMPLATE_PRODUCTS:
            continue
        p = {"id": pdir.name, "milestones": [], "waiting": [], "updated": None,
             "todos": [], "todo_items": [], "status_text": "", "done_features": [], "has_goal": (pdir / "goal.md").exists(), "has_handoff": (pdir / "handoff.md").exists()}
        if p["has_goal"]:
            for line in (pdir / "goal.md").read_text(encoding="utf-8").splitlines():
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if line.startswith("|") and len(cells) >= 3 and not set(cells[0]) <= set("-: ") \
                        and cells[0] not in ("里程碑", "任务"):
                    p["milestones"].append((cells[0], cells[1], cells[-1]))
        if p["has_handoff"]:
            text = (pdir / "handoff.md").read_text(encoding="utf-8")
            m = re.search(r"最近更新[:：]\s*(\d{4}-\d{2}-\d{2})", text)
            p["updated"] = m.group(1) if m else None
            m = re.search(r"^## *等待项.*?\n(.*?)(?=^##|\Z)", text, re.M | re.S)
            if m:
                p["waiting"] = [re.sub(r"^\d+\.\s*", "", l.strip()) for l in m.group(1).splitlines()
                                if re.match(r"\s*(\d+\.|-)\s", l) and "~~" not in l[:12]]
            # 「已完成功能」：### 功能名，其下 - 条目（做完的待办移到这里，保留编号）
            m = re.search(r"^## *已完成功能.*?\n(.*?)(?=^## |\Z)", text, re.M | re.S)
            if m:
                for l in m.group(1).splitlines():
                    if l.startswith("### "):
                        p["done_features"].append((l[4:].strip(), []))
                    elif re.match(r"-\s", l) and p["done_features"]:
                        p["done_features"][-1][1].append(l[2:].strip())
            m = re.search(r"^## *现状.*?\n(.*?)(?=^## |\Z)", text, re.M | re.S)
            p["status_text"] = m.group(1) if m else ""
            m = re.search(r"^## *待办清单.*?\n(.*?)(?=^## |\Z)", text, re.M | re.S)
            if m:
                for l in m.group(1).splitlines():
                    mm = re.match(r"\s*-\s*(?:待办(\d+)\s*)?\[(高|中|低)\]\[([^\]]+)\]\s*(.*)$", l)
                    if mm:
                        num, pr, st, tx = mm.groups()
                        p["todo_items"].append((pr, st, tx, int(num) if num else None))
            # 没有「待办清单」时的兜底：「下一步」一节里没有划掉、没写「已完成」的条目（含缩进的子条目）；调研记录之后不再收
            m = re.search(r"^## *下一步.*?\n(.*?)(?=^## |\Z)", text, re.M | re.S)
            if m:
                for l in ([] if p["todo_items"] else m.group(1).splitlines()):
                    if l.startswith("- （以下为"):
                        break
                    if re.match(r"\s*-\s", l) and not re.match(r"\s*-\s+(\*\*)?~~", l) \
                            and "已完成" not in l and not re.match(r"\s*-\s+(结果|\*\*[^*]*\*\*[:：]$)", l) and "已合入" not in l[:60]:
                        p["todos"].append(re.sub(r"^\s*-\s*", "", l).strip())
        if p["has_goal"] and not p["todo_items"]:
            for l in (pdir / "goal.md").read_text(encoding="utf-8").splitlines():
                if "待用户定" in l or "待定" in l:
                    p["todos"].append("[goal.md] " + l.strip().lstrip("-").strip())
        out.append(p)
    return out


def step_key(head):
    """Step name of a digest line: text before the first ':' or '(' (e.g. 'KEY1/KEY2', 'audprc 烧录')."""
    return re.split(r"[:：(（]", head, 1)[0].strip().lower()


def read_manual():
    """Verdict lines of each manual role's evidence digest, in file order.

    The digest is append-only, so an early 'pending' line for a step stays in the file after
    the step is settled. Only the last line per step name is kept (heuristic: see step_key)."""
    out = []
    for role, product, path in MANUAL_ROLES:
        if path is None:
            continue
        items = []
        if path.exists():
            for l in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if l.startswith("- ") and "判定" in l:
                    head, _, verdict = l[2:].rpartition("判定")
                    items.append((head.strip(" .:：,，"), verdict.strip(" :：")))
        last = {}
        for n, (head, _) in enumerate(items):
            last[step_key(head)] = n
        items = [it for n, it in enumerate(items) if last[step_key(it[0])] == n]
        out.append({"role": role, "product": product, "path": path, "items": items,
                    "mtime": dt.datetime.fromtimestamp(path.stat().st_mtime) if path.exists() else None})
    return out


def timeline_svg(events, activity, since, days):
    """One row per role (cron roles, then manual roles, then IDE heartbeats), one cell per hour,
    coloured by the most notable outcome in that hour."""
    hours = days * 24
    left, cell_w, row_h, top = 110, 6, 26, 28
    width = left + hours * cell_w + 10
    rows = [(task, ROLES[task][0]) for task in ROLES] + [(r, r) for r, _, _ in MANUAL_ROLES] + [(HB_ROW, HB_ROW)]
    tasks = [k for k, _ in rows]
    label = dict(rows)
    height = top + len(tasks) * row_h + 24
    buckets = defaultdict(lambda: defaultdict(int))
    for t, task, kind, _ in events:
        if kind and task in ROLES:
            buckets[(task, int((t - since).total_seconds() // 3600))][kind] += 1
    for r in activity:
        key = HB_ROW if r["kind"] == "heartbeat" else r.get("role")
        if key in label:
            buckets[(key, int((r["t"] - since).total_seconds() // 3600))][ACT_COLOR[r["kind"]]] += 1
    rank = ["err", "woke", "run", "skip", "act", "hb", "ok"]
    parts = ['<svg role="img" aria-labelledby="tl-title" viewBox="0 0 %d %d" width="100%%">' % (width, height),
             '<title id="tl-title">最近 %d 天各角色每小时活动</title>' % days]
    for d in range(days + 1):
        x = left + d * 24 * cell_w
        parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#8892a0" stroke-width="1"/>'
                     % (x, top - 6, x, top + len(tasks) * row_h))
        if d < days:
            day = since + dt.timedelta(days=d)
            parts.append('<text x="%d" y="%d" font-size="12" fill="#333">%s</text>'
                         % (x + 4, top - 10, day.strftime("%m-%d %a")))
    for i, task in enumerate(tasks):
        y = top + i * row_h
        parts.append('<text x="0" y="%d" font-size="13" fill="#111">%s</text>' % (y + 16, esc(label[task])))
        parts.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#f3f5f7"/>'
                     % (left, y + 3, hours * cell_w, row_h - 6))
        for h in range(hours):
            b = buckets.get((task, h))
            if not b:
                continue
            kind = next(k for k in rank if b.get(k))
            start = since + dt.timedelta(hours=h)
            tip = "%s %s–%02d:00  " % (label[task], start.strftime("%m-%d %H:00"), (start.hour + 1) % 24)
            tip += "，".join("%s %d" % (LABELS[k], b[k]) for k in rank if b.get(k))
            parts.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"><title>%s</title></rect>'
                         % (left + h * cell_w, y + 3, cell_w - 1, row_h - 6, COLORS[kind], esc(tip)))
    parts.append("</svg>")
    return "\n".join(parts)


def fmt_age(now, t):
    m = int((now - t).total_seconds() // 60)
    return "%d 分钟前" % m if m < 60 else ("%d 小时前" % (m // 60) if m < 48 * 60 else t.strftime("%m-%d %H:%M"))


def cron_card(task, role, product, events, runs, running, now):
    ev = [e for e in events if e[1] == task]
    cnt = defaultdict(int)
    for e in ev:
        if e[2]:
            cnt[e[2]] += 1
    task_runs = [r for r in runs if r["task"] == task]
    last = ev[-1] if ev else None
    open_run = next((r for r in task_runs if not r["end"]), None)
    if task in running:
        since = open_run["start"] if open_run else None
        status = "运行中" + ("，已 %d 分钟（%s 开始）" % ((now - since).total_seconds() // 60, since.strftime("%H:%M"))
                             if since else "（还在预检，未启动 Agent）")
        cls = "run"
    elif not ev:
        status, cls = "无活动", "idle"
    elif last[2] == "err":
        status, cls = "最近一次出错", "bad"
    else:
        recent_err = sum(1 for e in ev if e[2] == "err" and e[0] > last[0] - dt.timedelta(hours=24))
        if recent_err:
            status, cls = "已恢复，24 小时内出错 %d 次" % recent_err, "warn"
        else:
            status, cls = "正常", "good"
    extra = ""
    if task in running and open_run:
        extra = "<li>本场 digest：<code>%s</code></li>" % esc(open_run["dir"] / "digest.md")
    return ('<div class="card %s"><h3>%s <small>%s · cron</small></h3><p class="status">%s</p><ul>'
            '<li>检查 %d 次（无事件 %d / 唤醒 %d / 出错 %d）</li><li>Agent 运行 %d 场</li>'
            '<li>最近活动：%s</li>%s</ul></div>'
            % (cls, esc(role), esc(product), esc(status), cnt["ok"] + cnt["woke"] + cnt["err"], cnt["ok"],
               cnt["woke"], cnt["err"], len(task_runs),
               esc(last[0].strftime("%m-%d %H:%M") + " " + last[3]) if last else "—", extra))


def current_milestone(prod):
    """First milestone whose status is not finished, from goal.md's table."""
    for item, what, status in (prod or {}).get("milestones", []):
        if not status.startswith("已完成"):
            return "%s %s（%s）" % (item, what, status)
    return None


def manual_card(role, product, activity, manual, products, now):
    acts = [r for r in activity if r.get("role") == role]
    today = [r for r in acts if r["t"].date() == now.date()]
    beats = [r for r in activity if r["kind"] == "heartbeat"]
    last = acts[-1] if acts else None
    m = next((x for x in manual if x["role"] == role), None)
    if not last:
        status, cls = "最近 7 天没有活动日志记录", "idle"
        if m and m["mtime"]:
            status += "（证据 digest %s更新，见下方「手动任务」）" % fmt_age(now, m["mtime"])
    else:
        status = "%s：%s（%s）" % (KINDS[last["kind"]], last["text"], fmt_age(now, last["t"]))
        cls = {"blocked": "bad", "waiting": "warn", "start": "run", "progress": "run"}.get(last["kind"], "good")
        if last["kind"] in ("start", "progress") and now - last["t"] > dt.timedelta(hours=6):
            cls = "idle"
            status += "，之后没有新记录"
    prod = next((p for p in products if p["id"].lower() == product.lower()), None)
    lis = []
    ms = current_milestone(prod)
    if ms:
        lis.append("<li>当前里程碑：%s</li>" % esc(ms))
    lis.append("<li>今天记录 %d 条</li>" % len(today))
    for r in acts[-5:][::-1]:
        lis.append("<li>%s %s — %s</li>" % (esc(r["t"].strftime("%m-%d %H:%M")), esc(KINDS[r["kind"]]), esc(r["text"])))
    # a session was active after the last logged entry: say so, so a missing log line is visible
    if beats and (not last or beats[-1]["t"] - last["t"] > dt.timedelta(minutes=30)):
        lis.append('<li class="hint">IDE 会话最近活动 %s，此后没有记录进展（心跳不区分角色）</li>'
                   % esc(fmt_age(now, beats[-1]["t"])))
    if m and m["mtime"]:
        lis.append("<li>证据 digest 更新：%s</li>" % esc(fmt_age(now, m["mtime"])))
    if prod and prod["waiting"]:
        lis.append("<li>等人处理 %d 项（见产品进度）</li>" % len(prod["waiting"]))
    return ('<div class="card %s"><h3>%s <small>%s · IDE 手动</small></h3><p class="status">%s</p><ul>%s</ul></div>'
            % (cls, esc(role), esc(product), esc(status), "".join(lis)))


def role_cards(events, runs, activity, manual, products, running, now):
    cards = [cron_card(task, role, product, events, runs, running, now) for task, (role, product) in ROLES.items()]
    cards += [manual_card(role, product, activity, manual, products, now) for role, product, _ in MANUAL_ROLES]
    return "\n".join(cards)


def activity_table(activity, now):
    rows = [r for r in activity if r["kind"] != "heartbeat" and r["t"].date() == now.date()][::-1][:60]
    if not rows:
        return ("<p>今天还没有活动记录。IDE 会话按 <code>.kiro/steering/activity-log.md</code> 用 "
                "<code>scripts/report/log_activity.py</code> 记录。</p>")
    body = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s%s</td></tr>"
                   % (esc(r["t"].strftime("%H:%M")), esc(r.get("role", "")), esc(KINDS[r["kind"]]), esc(r["text"]),
                      " <code>%s</code>" % esc(r["ref"]) if r.get("ref") else "") for r in rows)
    return ('<table><thead><tr><th scope="col">时间</th><th scope="col">角色</th><th scope="col">类型</th>'
            '<th scope="col">内容</th></tr></thead><tbody>%s</tbody></table>' % body)


def runs_table(runs, running):
    if not runs:
        return "<p>这段时间没有 Agent 运行。</p>"
    # the newest open run of a task whose run-task.sh is alive is the live one; older open runs were cut off
    live = {}
    for r in runs:  # newest first
        if not r["end"] and r["task"] in running and r["task"] not in live:
            live[r["task"]] = r
    rows = []
    for r in runs:
        if r["end"]:
            dur = "%d 分 %02d 秒" % divmod(int((r["end"] - r["start"]).total_seconds()), 60)
        elif live.get(r["task"]) is r:
            dur = "运行中"
        else:
            dur = "被中断（日志没有结束记录）"
        flag = '<span class="tag bad">需要处理</span>' if r["needs_owner"] else ""
        hl = "".join("<li>%s</li>" % esc(h) for h in r["highlights"]) or "<li>（无 digest）</li>"
        rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s<ul>%s</ul><code>%s</code></td></tr>"
                    % (esc(ROLES.get(r["task"], (r["task"],))[0]), esc(r["start"].strftime("%m-%d %H:%M")), esc(dur),
                       esc(r["exit"] if r["exit"] is not None else "—"), flag, hl,
                       esc(r["digest"] or r["dir"])))
    return ('<table><thead><tr><th scope="col">角色</th><th scope="col">开始</th><th scope="col">用时</th>'
            '<th scope="col">退出码</th><th scope="col">结论（摘自 digest）</th></tr></thead><tbody>%s</tbody></table>'
            % "".join(rows))


PRIO_CLASS = {"高": "bad", "中": "warn", "低": "idle"}


def stale_warning(p, activity):
    """Warn when handoff.md's 「最近更新」 is more than a day older than the product's newest activity-log record
    (heartbeats ignored). Returns an HTML snippet or ''."""
    if not p["updated"]:
        return ""
    roles = {r for r, prod in known_roles().items() if prod.lower() == p["id"].lower()}
    times = [r["t"].replace(tzinfo=None) for r in activity if r.get("role") in roles and r["kind"] != "heartbeat"]
    if not times:
        return ""
    try:
        upd = dt.datetime.fromisoformat(p["updated"])
    except ValueError:
        return ""
    last = max(times)
    if last - upd <= dt.timedelta(days=1):
        return ""
    return ('<p class="stale">⚠ handoff.md 的「最近更新」是 %s，比最近一条活动记录（%s）旧 %d 天，'
            '下面的待办可能已过期；更新 handoff 时要回看「待办清单」。</p>'
            % (esc(p["updated"]), esc(last.strftime("%Y-%m-%d %H:%M")), (last - upd).days))
# 「现状」里表示做完的词，和同一句里表示没做完的词（后者出现就不算做完）
DONE_RE = re.compile(r"通过|已[^，。；：]{0,8}合入|已推送|已完成")
NOT_DONE_RE = re.compile(r"未(合入|上板|推送|运行|能|测|烧录|实测|验证|做)|不通过|没通过|待")
# 标题里有这些词的待办本来就是「做完之后的剩余项」，不拿来比
LEFTOVER_RE = re.compile(r"剩余|遗留|未测|未实测|小项")
# 太泛的词（几乎每条都提到）和提交号不拿来比
GENERIC_TERMS = {"main", "origin/main"}
HASH_RE = re.compile(r"[0-9a-f]{7,40}")
def done_todo_hints(p):
    """To-do items whose key terms appear in 「现状」 as done (通过 / 已合入 / 已推送 / 已完成).
    Key terms: `backticked` tokens in the item title (before the first ：), minus GENERIC_TERMS and
    commit hashes. A 「现状」 bullet counts as done for a term when the bullet's lead-in (text before the
    first ：) says done (and names no other `subject`, or names this term), or one sentence (split on 。；;) holding the term says done; either way a
    not-done word (未合入 / 待 / ...) in that same text cancels it. ~~struck~~ text is ignored.
    Returns [(title, evidence)]."""
    units = [re.sub(r"~~.*?~~", "", l).strip(" -*") for l in p.get("status_text", "").splitlines()]
    def done(s):
        return DONE_RE.search(s) and not NOT_DONE_RE.search(s)
    hits = []
    for _prio, _st, text, num in p["todo_items"]:
        title = re.split(r"[:：]", text, 1)[0]
        if LEFTOVER_RE.search(title):
            continue
        terms = [x for x in re.findall(r"`([^`]{3,})`", title) if x not in GENERIC_TERMS and not HASH_RE.fullmatch(x)]
        ev = None
        for term in terms:
            for u in units:
                if term not in u:
                    continue
                head = re.split(r"[:：]", u, 1)[0]
                # 引言里点名了别的东西（`x`，路径除外）就只对它们算数；term 所在那句写了「未…」也不算
                subjects = [x for x in re.findall(r"`([^`]+)`", head) if "/" not in x]
                own = next((s for s in re.split(r"[。；;]", u) if term in s), "")
                if done(head) and (term in head or not subjects) and not NOT_DONE_RE.search(own):
                    ev = head
                else:
                    ev = next((s.strip() for s in re.split(r"[。；;]", u) if term in s and done(s)), None)
                if ev:
                    break
            if ev:
                break
        if ev:
            hits.append((("待办%d " % num if num else "") + title, ev.strip("* ")))
    return hits
def todo_block(p, activity=()):
    """The product's to-do list, made prominent: count badge, then items grouped 高/中/低.
    Source is handoff.md 「待办清单」 (curated); without it, falls back to heuristic lines."""
    items = p["todo_items"]
    warn = stale_warning(p, activity)
    hints = done_todo_hints(p)
    if hints:
        warn += ('<div class="stale">⚠ 以下待办在「现状」里已写成通过或已合入，可能该移到「已完成功能」：<ul>%s</ul></div>'
                 % "".join("<li><b>%s</b>（「现状」：%s）</li>"
                           % (esc(ti), esc(s if len(s) <= 160 else s[:160] + "…")) for ti, s in hints))
    if not items:
        lis = "".join("<li>%s</li>" % esc(t if len(t) <= 220 else t[:220] + "…") for t in p["todos"]) or "<li>无</li>"
        return ('<div class="todo"><h4 class="todo-h">待办 <span class="badge">%d</span>'
                '<small>handoff.md 没有「待办清单」一节，以下为按关键词猜的</small></h4>%s<ul>%s</ul></div>'
                % (len(p["todos"]), warn, lis))
    cnt = {k: sum(1 for i in items if i[0] == k) for k in "高中低"}
    head = "".join('<span class="tag %s">%s %d</span> ' % (PRIO_CLASS[k], k, cnt[k]) for k in "高中低" if cnt[k])
    rows = "".join('<li class="p-%s"><b class="num">%s</b> <span class="tag %s">%s</span> <span class="st">%s</span> %s</li>'
                   % (PRIO_CLASS[pr], "待办%d" % num if num else "", PRIO_CLASS[pr], esc(pr), esc(st), esc(tx))
                   for pr, st, tx, num in items)
    return ('<div class="todo"><h4 class="todo-h">待办 <span class="badge">%d</span> %s'
            '<small>来源 handoff.md「待办清单」，高优先在前</small></h4>%s<ul>%s</ul></div>' % (len(items), head, warn, rows))


def done_block(p, done_ms):
    """Completed features at the end of the product card: handoff.md 「已完成功能」 (### feature, the
    finished to-dos listed under it), then goal.md milestones whose status starts with 已完成."""
    feats = p.get("done_features", [])
    if not feats and not done_ms:
        return ""
    parts = []
    for name, items in feats:
        lis = "".join("<li>%s</li>" % esc(i) for i in items)
        parts.append("<li><b>%s</b>%s</li>" % (esc(name), "<ul>%s</ul>" % lis if lis else ""))
    for a, b, c in done_ms:
        parts.append("<li><b>%s %s</b> <small>%s</small></li>" % (esc(a), esc(b), esc(c)))
    return ('<div class="done"><h4>已完成功能 <span class="badge">%d</span>'
            '<small>来源 handoff.md「已完成功能」与 goal.md 已完成的里程碑；做完的待办移到对应功能下</small></h4>'
            '<ul>%s</ul></div>' % (len(feats) + len(done_ms), "".join(parts)))
def products_section(products, activity=()):
    out = []
    for p in products:
        if not p["has_goal"] and not p["has_handoff"]:
            out.append('<div class="card idle"><h3>%s</h3><p>没有 goal.md / handoff.md</p></div>' % esc(p["id"]))
            continue
        # 没做完的里程碑留在顶部；已完成的里程碑和 handoff「已完成功能」放到卡片最后
        open_ms = [m for m in p["milestones"] if not m[2].startswith("已完成")]
        done_ms = [m for m in p["milestones"] if m[2].startswith("已完成")]
        ms = ('<table><thead><tr><th scope="col">项</th><th scope="col">内容</th><th scope="col">状态</th></tr></thead>'
              '<tbody>%s</tbody></table>' % "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % tuple(esc(x) for x in m)
                                                 for m in open_ms)) if open_ms else ""
        wt = "".join("<li>%s</li>" % esc(w) for w in p["waiting"]) or "<li>无</li>"
        td = todo_block(p, activity)
        out.append('<div class="card"><h3>%s <small>handoff 更新：%s</small></h3>'
                   '%s<h4>等人处理</h4><ul>%s</ul>%s%s</div>'
                   % (esc(p["id"]), esc(p["updated"] or "未写"), ms, wt, td, done_block(p, done_ms)))
    return "\n".join(out)


def role_digests_section(day):
    d = STATE / "digests" / day.isoformat()
    files = sorted(d.glob("*.md")) if d.exists() else []
    if not files:
        return "<p>还没有当日角色 digest（由 <code>scripts/report/build_digests.py</code> 生成）。</p>"
    rows = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        title = text.splitlines()[0].lstrip("# ").split(" · ")[0] if text else f.stem
        m = re.search(r"^- 结论：(.*)$", text, re.M)
        rows.append("<tr><td>%s</td><td>%s</td><td><code>%s</code></td></tr>"
                    % (esc(title), esc(m.group(1) if m else "—"), esc(f)))
    return ('<table><thead><tr><th scope="col">角色</th><th scope="col">结论</th><th scope="col">digest</th></tr></thead>'
            '<tbody>%s</tbody></table>' % "".join(rows))


def manual_section(manual):
    out = []
    for m in manual:
        items = "".join("<li>%s — <b>%s</b></li>" % (esc(h), esc(v)) for h, v in m["items"][-15:])
        out.append('<div class="card"><h3>%s <small>%s · 手动触发</small></h3><p>来源：<code>%s</code>'
                   '（最近 15 个步骤的最新判定，按时间先后；同一步骤只留最后一条）</p><ul>%s</ul></div>'
                   % (esc(m["role"]), esc(m["product"]), esc(m["path"]), items or "<li>无记录</li>"))
    return "\n".join(out)


CSS = """
body{font-family:system-ui,-apple-system,"Noto Sans CJK SC",sans-serif;margin:24px;color:#111;background:#fff;max-width:1200px}
h1{font-size:22px;margin:0 0 4px} h2{font-size:18px;margin:28px 0 10px;border-bottom:1px solid #ddd;padding-bottom:4px}
h3{font-size:15px;margin:0 0 6px} h3 small,h4{font-weight:normal;color:#555;font-size:13px}
.meta{color:#555;font-size:13px} .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
.card{border:1px solid #d5dbe1;border-left:6px solid #8892a0;border-radius:6px;padding:10px 14px;background:#fafbfc}
.card.good{border-left-color:#1f9d55} .card.bad{border-left-color:#d64545} .card.warn{border-left-color:#e0a100} .card.idle{border-left-color:#b9c2cc}
.card.run{border-left-color:#2f6fdb} .hint{color:#8a5a00} .fresh{background:#f3f5f7;border:1px solid #d5dbe1;border-radius:6px;padding:6px 10px;font-size:13px}
.card ul{margin:4px 0 0 18px;padding:0;font-size:13px} .status{margin:0;font-weight:600}
table{border-collapse:collapse;width:100%;font-size:13px} th,td{border:1px solid #d5dbe1;padding:5px 7px;text-align:left;vertical-align:top}
th{background:#eef1f4} td ul{margin:2px 0 2px 16px;padding:0} code{font-size:12px;color:#444;word-break:break-all}
.tag{display:inline-block;padding:1px 6px;border-radius:3px;font-size:12px;color:#fff;background:#666}.tag.bad{background:#d64545}
.tag.warn{background:#e0a100}
.who-user{color:#1f9d55;font-weight:600} .who-assistant{color:#2f6fdb;font-weight:600}
.hist-day{margin:8px 0} .hist-day>summary{cursor:pointer;font-weight:600;padding:4px 0}
.chat-card p{margin:4px 0} .chat-card details{margin-top:6px} .chat-card summary{cursor:pointer;color:#2f6fdb;font-size:13px}
.legend span{display:inline-block;margin-right:14px;font-size:13px} .legend i{display:inline-block;width:12px;height:12px;margin-right:4px;vertical-align:-1px}
.todo{margin-top:12px;padding:8px 12px;border:2px solid #d64545;border-radius:6px;background:#fff6f6}
.todo-h{font-size:16px;color:#111;margin:0 0 6px} .todo-h small{margin-left:8px}
.badge{display:inline-block;min-width:22px;text-align:center;padding:1px 8px;border-radius:11px;background:#d64545;color:#fff;font-size:14px}
.todo ul{list-style:none;margin:0;padding:0} .todo li{font-size:14px;padding:4px 0;border-bottom:1px dotted #e3c9c9}
.done{margin-top:12px;border-top:1px solid #ddd;padding-top:6px} .done ul ul{margin:2px 0 6px 18px;font-size:13px;color:#444}
.todo .stale{background:#fff3cd;border:1px solid #e0b84c;color:#6b4e00;padding:4px 8px;margin:0 0 6px;font-size:13px}
.todo li.p-bad{font-weight:600} .todo .st{color:#555;font-size:12px;border:1px solid #bbb;border-radius:3px;padding:0 4px;font-weight:normal}
.tag.idle{background:#8892a0}
pre{background:#f3f5f7;padding:8px;font-size:12px;white-space:pre-wrap}
"""


def freshness(now, events, activity, chat, manual):
    """When each source last changed, and when the next scheduled rebuild is."""
    # cron runs at minute REFRESH_MINUTE, then every REFRESH_EVERY minutes (crontab.example)
    m = REFRESH_MINUTE + ((now.minute - REFRESH_MINUTE) // REFRESH_EVERY + 1) * REFRESH_EVERY
    nxt = now.replace(minute=0, second=0) + dt.timedelta(minutes=m)
    beats = [r["t"] for r in activity if r["kind"] == "heartbeat"]
    acts = [r["t"] for r in activity if r["kind"] != "heartbeat"]
    src = [("cron 日志", events[-1][0] if events else None), ("活动日志", acts[-1] if acts else None),
           ("IDE 心跳", beats[-1] if beats else None), ("对话记录", chat[-1]["t"] if chat else None)]
    src += [("%s 证据 digest" % m["product"], m["mtime"]) for m in manual]
    parts = "；".join("%s %s" % (n, t.strftime("%m-%d %H:%M") if t else "无") for n, t in src)
    return ('<p class="fresh">数据截至 <b>%s</b>（报告不是实时的，cron 每 %d 分钟重建，下次约 <b>%s</b>；'
            '想马上看最新的，按操作手册第 2 节手动重建）<br>各来源最近更新：%s</p>'
            % (esc(now.strftime("%m-%d %H:%M")), REFRESH_EVERY, esc(nxt.strftime("%H:%M")), esc(parts)))


def build(days, out):
    now = dt.datetime.now().replace(microsecond=0)
    since = (now - dt.timedelta(days=days - 1)).replace(hour=0, minute=0, second=0)
    events = read_events(since)
    runs = read_runs(events)
    activity = read_activity(since)
    chat = read_chat(since)
    chat_all = read_chat(dt.datetime(2000, 1, 1))  # history covers every recorded day
    manual = read_manual()
    products = read_products()
    running = running_tasks()
    legend = "".join('<span><i style="background:%s"></i>%s</span>' % (COLORS[k], LABELS[k])
                     for k in ("ok", "woke", "run", "act", "hb", "skip", "err"))
    legend += '<span><i style="background:#f3f5f7;border:1px solid #ccc"></i>无记录（关机或未排班）</span>'
    needs = read_needs_owner()
    # 报告各节顺序固定为 SECTION_ORDER（见文件顶部）；要增删或换位只改那个列表。
    body = {
        "roles": '<div class="grid">%s</div>' % role_cards(events, runs, activity, manual, products, running, now),
        "todo": '<div class="grid">%s</div><h4>needs-owner.log（最近 20 行）</h4><pre>%s</pre>'
                % (products_section(products, activity), esc("\n".join(needs[-20:]) or "无")),
        "activity": activity_table(activity, now),
        "chat": chat_table(chat, now.date()),
        "history": chat_history(chat_all, now.date()),
        "digests": role_digests_section(now.date()),
        "timeline": '<div class="legend">%s</div>%s' % (legend, timeline_svg(events, activity, since, days)),
        "runs": runs_table(runs, running),
        "manual": '<div class="grid">%s</div>' % manual_section(manual),
    }
    assert set(body) == {k for k, _ in SECTION_ORDER}, "SECTION_ORDER 与 body 不一致"
    sections = "\n".join("<h2>%s</h2>%s" % (title, body[key]) for key, title in SECTION_ORDER)
    doc = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Open Company 进度报告</title>
<style>%s</style></head><body>
<h1>Open Company 进度报告</h1>
<p class="meta">生成时间 %s · 统计范围 %s 起 %d 天 · 数据来自本机 cron 日志、活动日志与 digest，未联网</p>
%s
%s
</body></html>""" % (CSS, esc(now), esc(since.date()), days, freshness(now, events, activity, chat, manual), sections)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(doc, encoding="utf-8")
    tmp.replace(out)
    return out, len(events), len(runs)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--out", type=Path, default=STATE / "report/index.html")
    a = ap.parse_args()
    path, n_ev, n_runs = build(max(1, a.days), a.out)
    print("wrote %s (%d log events, %d agent runs)" % (path, n_ev, n_runs))
