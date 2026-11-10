#!/usr/bin/env python3
"""Build a self-contained HTML progress report of what each Open Company role did.

Reads (all local, nothing is sent anywhere):
  ~/.local/state/open-company/logs/<task>-<date>.log   cron runner log (run-task.sh)
  ~/.local/state/open-company/runs/<task>/<ts>/digest.md
  ~/.local/state/open-company/needs-owner.log
  <repo>/companies/*/products/*/goal.md, handoff.md
  manual digests listed in MANUAL_DIGESTS

Writes ~/.local/state/open-company/report/index.html (no scripts, no external assets).

Usage: build_report.py [--days N] [--out PATH]
Python 3.8+, standard library only.
"""
import argparse
import datetime as dt
import html
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
# Work done by hand in the IDE, recorded in per-product digests
MANUAL_DIGESTS = [
    ("固件研发与实测", "Weband", Path("/home/whole/data/reawork/weband/evidence/digest.md")),
]

LINE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[([\w-]+)\] (.*)$")
COLORS = {"err": "#d64545", "woke": "#2f6fdb", "run": "#1f9d55", "ok": "#b9c2cc", "skip": "#e0a100"}
LABELS = {"ok": "检查无事件", "woke": "有事件唤醒", "run": "Agent 运行", "err": "出错", "skip": "跳过（上一场未结束）"}


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


def read_needs_owner():
    f = STATE / "needs-owner.log"
    return f.read_text(encoding="utf-8", errors="replace").splitlines() if f.exists() else []


def read_products():
    out = []
    for pdir in sorted(REPO.glob("companies/*/products/*")):
        if not (pdir / "Productfile.yaml").exists() or pdir.name in TEMPLATE_PRODUCTS:
            continue
        p = {"id": pdir.name, "milestones": [], "waiting": [], "updated": None,
             "has_goal": (pdir / "goal.md").exists(), "has_handoff": (pdir / "handoff.md").exists()}
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
                                if re.match(r"\s*(\d+\.|-)\s", l)]
        out.append(p)
    return out


def read_manual():
    out = []
    for role, product, path in MANUAL_DIGESTS:
        items = []
        if path.exists():
            for l in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if l.startswith("- ") and "判定" in l:
                    head, _, verdict = l[2:].rpartition("判定")
                    items.append((head.strip(" .:：,，"), verdict.strip(" :：")))
        out.append({"role": role, "product": product, "path": path, "items": items})
    return out


def timeline_svg(events, since, days):
    """One row per cron role, one cell per hour, coloured by the worst outcome in that hour."""
    hours = days * 24
    left, cell_w, row_h, top = 110, 6, 26, 28
    width = left + hours * cell_w + 10
    tasks = list(ROLES)
    height = top + len(tasks) * row_h + 24
    buckets = defaultdict(lambda: defaultdict(int))
    for t, task, kind, _ in events:
        if kind and task in ROLES:
            buckets[(task, int((t - since).total_seconds() // 3600))][kind] += 1
    rank = ["err", "woke", "run", "skip", "ok"]
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
        parts.append('<text x="0" y="%d" font-size="13" fill="#111">%s</text>' % (y + 16, esc(ROLES[task][0])))
        parts.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#f3f5f7"/>'
                     % (left, y + 3, hours * cell_w, row_h - 6))
        for h in range(hours):
            b = buckets.get((task, h))
            if not b:
                continue
            kind = next(k for k in rank if b.get(k))
            start = since + dt.timedelta(hours=h)
            tip = "%s %s–%02d:00  " % (ROLES[task][0], start.strftime("%m-%d %H:00"), (start.hour + 1) % 24)
            tip += "，".join("%s %d" % (LABELS[k], b[k]) for k in rank if b.get(k))
            parts.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"><title>%s</title></rect>'
                         % (left + h * cell_w, y + 3, cell_w - 1, row_h - 6, COLORS[kind], esc(tip)))
    parts.append("</svg>")
    return "\n".join(parts)


def role_cards(events, runs):
    cards = []
    for task, (role, product) in ROLES.items():
        ev = [e for e in events if e[1] == task]
        cnt = defaultdict(int)
        for e in ev:
            if e[2]:
                cnt[e[2]] += 1
        task_runs = [r for r in runs if r["task"] == task]
        last = ev[-1] if ev else None
        if not ev:
            status, cls = "无活动", "idle"
        elif last[2] == "err":
            status, cls = "最近一次出错", "bad"
        else:
            recent_err = sum(1 for e in ev if e[2] == "err" and e[0] > last[0] - dt.timedelta(hours=24))
            if recent_err:
                status, cls = "已恢复，24 小时内出错 %d 次" % recent_err, "warn"
            else:
                status, cls = "正常", "good"
        cards.append(
            '<div class="card %s"><h3>%s <small>%s</small></h3><p class="status">%s</p><ul>'
            '<li>检查 %d 次（无事件 %d / 唤醒 %d / 出错 %d）</li><li>Agent 运行 %d 场</li>'
            '<li>最近活动：%s</li></ul></div>'
            % (cls, esc(role), esc(product), esc(status), cnt["ok"] + cnt["woke"] + cnt["err"], cnt["ok"],
               cnt["woke"], cnt["err"], len(task_runs), esc(last[0].strftime("%m-%d %H:%M") + " " + last[3]) if last else "—"))
    return "\n".join(cards)


def runs_table(runs):
    if not runs:
        return "<p>这段时间没有 Agent 运行。</p>"
    rows = []
    for r in runs:
        dur = "运行中或被中断" if not r["end"] else "%d 分 %02d 秒" % divmod(int((r["end"] - r["start"]).total_seconds()), 60)
        flag = '<span class="tag bad">需要处理</span>' if r["needs_owner"] else ""
        hl = "".join("<li>%s</li>" % esc(h) for h in r["highlights"]) or "<li>（无 digest）</li>"
        rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s<ul>%s</ul><code>%s</code></td></tr>"
                    % (esc(ROLES.get(r["task"], (r["task"],))[0]), esc(r["start"].strftime("%m-%d %H:%M")), esc(dur),
                       esc(r["exit"] if r["exit"] is not None else "—"), flag, hl,
                       esc(r["digest"] or r["dir"])))
    return ('<table><thead><tr><th scope="col">角色</th><th scope="col">开始</th><th scope="col">用时</th>'
            '<th scope="col">退出码</th><th scope="col">结论（摘自 digest）</th></tr></thead><tbody>%s</tbody></table>'
            % "".join(rows))


def products_section(products):
    out = []
    for p in products:
        if not p["has_goal"] and not p["has_handoff"]:
            out.append('<div class="card idle"><h3>%s</h3><p>没有 goal.md / handoff.md</p></div>' % esc(p["id"]))
            continue
        ms = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(a), esc(b), esc(c)) for a, b, c in p["milestones"])
        wt = "".join("<li>%s</li>" % esc(w) for w in p["waiting"]) or "<li>无</li>"
        out.append('<div class="card"><h3>%s <small>handoff 更新：%s</small></h3>'
                   '<table><thead><tr><th scope="col">项</th><th scope="col">内容</th><th scope="col">状态</th></tr></thead>'
                   '<tbody>%s</tbody></table><h4>等人处理</h4><ul>%s</ul></div>'
                   % (esc(p["id"]), esc(p["updated"] or "未写"), ms, wt))
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
        items = "".join("<li><b>%s</b> — %s</li>" % (esc(v), esc(h)) for h, v in m["items"][-15:])
        out.append('<div class="card"><h3>%s <small>%s · 手动触发</small></h3><p>来源：<code>%s</code>（最近 15 条判定）</p><ul>%s</ul></div>'
                   % (esc(m["role"]), esc(m["product"]), esc(m["path"]), items or "<li>无记录</li>"))
    return "\n".join(out)


CSS = """
body{font-family:system-ui,-apple-system,"Noto Sans CJK SC",sans-serif;margin:24px;color:#111;background:#fff;max-width:1200px}
h1{font-size:22px;margin:0 0 4px} h2{font-size:18px;margin:28px 0 10px;border-bottom:1px solid #ddd;padding-bottom:4px}
h3{font-size:15px;margin:0 0 6px} h3 small,h4{font-weight:normal;color:#555;font-size:13px}
.meta{color:#555;font-size:13px} .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
.card{border:1px solid #d5dbe1;border-left:6px solid #8892a0;border-radius:6px;padding:10px 14px;background:#fafbfc}
.card.good{border-left-color:#1f9d55} .card.bad{border-left-color:#d64545} .card.warn{border-left-color:#e0a100} .card.idle{border-left-color:#b9c2cc}
.card ul{margin:4px 0 0 18px;padding:0;font-size:13px} .status{margin:0;font-weight:600}
table{border-collapse:collapse;width:100%;font-size:13px} th,td{border:1px solid #d5dbe1;padding:5px 7px;text-align:left;vertical-align:top}
th{background:#eef1f4} td ul{margin:2px 0 2px 16px;padding:0} code{font-size:12px;color:#444;word-break:break-all}
.tag{display:inline-block;padding:1px 6px;border-radius:3px;font-size:12px;color:#fff;background:#666}.tag.bad{background:#d64545}
.legend span{display:inline-block;margin-right:14px;font-size:13px} .legend i{display:inline-block;width:12px;height:12px;margin-right:4px;vertical-align:-1px}
pre{background:#f3f5f7;padding:8px;font-size:12px;white-space:pre-wrap}
"""


def build(days, out):
    now = dt.datetime.now().replace(microsecond=0)
    since = (now - dt.timedelta(days=days - 1)).replace(hour=0, minute=0, second=0)
    events = read_events(since)
    runs = read_runs(events)
    legend = "".join('<span><i style="background:%s"></i>%s</span>' % (COLORS[k], LABELS[k])
                     for k in ("ok", "woke", "run", "skip", "err"))
    legend += '<span><i style="background:#f3f5f7;border:1px solid #ccc"></i>无记录（关机或未排班）</span>'
    needs = read_needs_owner()
    doc = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Open Company 进度报告</title>
<style>%s</style></head><body>
<h1>Open Company 进度报告</h1>
<p class="meta">生成时间 %s · 统计范围 %s 起 %d 天 · 数据来自本机 cron 日志与 digest，未联网</p>
<h2>各角色概览</h2><div class="grid">%s</div>
<h2>今日各角色 digest</h2>%s
<h2>时间线（每格 1 小时，悬停看明细）</h2><div class="legend">%s</div>%s
<h2>Agent 运行记录</h2>%s
<h2>手动任务</h2><div class="grid">%s</div>
<h2>产品进度（goal.md / handoff.md）</h2><div class="grid">%s</div>
<h2>待人处理（needs-owner.log）</h2><pre>%s</pre>
</body></html>""" % (CSS, esc(now), esc(since.date()), days, role_cards(events, runs), role_digests_section(now.date()), legend,
                     timeline_svg(events, since, days), runs_table(runs), manual_section(read_manual()),
                     products_section(read_products()), esc("\n".join(needs[-20:]) or "无"))
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
