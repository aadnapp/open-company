#!/usr/bin/env python3
"""Write one daily digest per role, so every role leaves a record even when no Agent ran.

Cron roles (盯盘分诊 / 定时发版 / 晚间复盘) are summarised from run-task.sh logs and the
digests of their Agent runs. Manual (IDE) roles are summarised from the activity log
(log_activity.py) and point at the evidence digest the product keeps in its work dir.

Output: ~/.local/state/open-company/digests/<YYYY-MM-DD>/<task-id>.md
Usage:  build_digests.py [--date YYYY-MM-DD] [--days N]   (default: today and yesterday)
Python 3.8+, standard library only. Reads local files only.
"""
import argparse
import datetime as dt
import re
from collections import Counter
from pathlib import Path

from build_report import KINDS, MANUAL_ROLES, ROLES, STATE, read_activity, read_events, read_products, read_runs

# How each cron role is scheduled; keep in sync with scripts/cron/crontab.example
SCHEDULE = {
    "daily-patrol": "每天 21:00",
}
GAP = dt.timedelta(minutes=20)  # errors closer than this belong to one window


def error_windows(events):
    wins = []
    for t, _task, kind, msg in events:
        if kind != "err":
            continue
        reason = msg.split(":", 1)[-1].strip() if "guard error" in msg else msg
        if wins and t - wins[-1]["end"] <= GAP:
            wins[-1]["end"] = t
            wins[-1]["n"] += 1
            wins[-1]["why"][reason] += 1
        else:
            wins.append({"start": t, "end": t, "n": 1, "why": Counter([reason])})
    return wins


def cron_digest(task, day, events, runs):
    role, product = ROLES[task]
    ev = [e for e in events if e[1] == task and e[0].date() == day]
    cnt = Counter(e[2] for e in ev if e[2])
    day_runs = sorted((r for r in runs if r["task"] == task and r["start"].date() == day), key=lambda r: r["start"])
    wins = error_windows(ev)
    needs = [r for r in day_runs if r["needs_owner"]]

    if not ev:
        verdict = "无活动（未排班、关机，或当天还没到排班时间）"
    elif needs:
        verdict = "需要处理：%d 场 Agent 运行标记了 needsOwner" % len(needs)
    elif ev[-1][2] == "err":
        verdict = "异常：最近一次检查出错，尚未恢复"
    elif wins:
        verdict = "已恢复：当天出错 %d 次，最近一次检查正常" % cnt["err"]
    else:
        verdict = "正常"

    lines = ["# %s · %s digest" % (role, day), "",
             "- 角色：%s（`%s`），产品 %s" % (role, task, product),
             "- 当前排班：%s" % SCHEDULE.get(task, "见 crontab"),
             "- 结论：%s" % verdict]
    if task == "github-issue-pr-actions" or cnt["ok"] or cnt["err"]:
        lines.append("- 预检：共 %d 次，无事件 %d / 有事件唤醒 %d / 出错 %d / 跳过 %d"
                     % (cnt["ok"] + cnt["woke"] + cnt["err"], cnt["ok"], cnt["woke"], cnt["err"], cnt["skip"]))
    if ev:
        lines.append("- 活动时段：%s – %s" % (ev[0][0].strftime("%H:%M"), ev[-1][0].strftime("%H:%M")))
    lines += ["", "## 出错时段"]
    if wins:
        for w in wins:
            why = "；".join("%s ×%d" % (k, v) for k, v in w["why"].most_common(2))
            lines.append("- %s – %s，%d 次：%s" % (w["start"].strftime("%H:%M"), w["end"].strftime("%H:%M"), w["n"], why))
    else:
        lines.append("- 无")
    lines += ["", "## Agent 运行"]
    if day_runs:
        for r in day_runs:
            dur = ("未结束（运行中，或被中断而没有结束记录）" if not r["end"]
                   else "%d 分 %02d 秒" % divmod(int((r["end"] - r["start"]).total_seconds()), 60))
            lines.append("- %s，用时 %s，退出码 %s%s" % (r["start"].strftime("%H:%M"), dur,
                                                     r["exit"] if r["exit"] is not None else "—",
                                                     "，**needsOwner**" if r["needs_owner"] else ""))
            lines.append("  - digest：`%s`" % (r["digest"] or "无"))
            for h in r["highlights"]:
                lines.append("  - %s" % h)
    else:
        lines.append("- 无（预检没有发现新事件，或当天未排班）")
    lines += ["", "## 对外操作", "- 以各场 Agent digest 为准；本汇总不执行任何操作。"]
    return "\n".join(lines) + "\n"


def manual_digest(role, product, path, day, activity):
    acts = [r for r in activity if r.get("role") == role and r["t"].date() == day]
    beats = [r for r in activity if r["kind"] == "heartbeat" and r["t"].date() == day]
    lines = ["# %s · %s digest" % (role, day), "",
             "- 角色：%s，产品 %s" % (role, product),
             "- 排班：手动触发（IDE 会话，不挂 cron）"]
    if acts:
        last = acts[-1]
        verdict = "当天 %d 条活动记录，最后一条 %s %s：%s" % (len(acts), last["t"].strftime("%H:%M"),
                                                            KINDS[last["kind"]], last["text"])
    else:
        verdict = "当天没有活动记录"
    if path is not None and path.exists():
        mtime = dt.datetime.fromtimestamp(path.stat().st_mtime)
        verdict += "；证据 digest %s" % ("当天有更新（最后修改 %s）" % mtime.strftime("%H:%M") if mtime.date() == day
                                         else "当天无更新（最后修改 %s）" % mtime.strftime("%Y-%m-%d %H:%M"))
    lines.append("- 结论：%s" % verdict)
    if beats:
        lines.append("- IDE 会话心跳：%d 次，%s – %s（心跳不区分角色）"
                     % (len(beats), beats[0]["t"].strftime("%H:%M"), beats[-1]["t"].strftime("%H:%M")))
    lines += ["", "## 当天活动"]
    lines += ["- %s %s：%s%s" % (r["t"].strftime("%H:%M"), KINDS[r["kind"]], r["text"],
                                 "（`%s`）" % r["ref"] if r.get("ref") else "") for r in acts] or ["- 无"]
    if path is None:
        return "\n".join(lines) + "\n"
    if not path.exists():
        lines.append("- 证据 digest：无记录（`%s` 不存在）" % path)
        return "\n".join(lines) + "\n"
    lines += ["", "- 证据 digest：`%s`（逐步实测记录，只追加，旧的 pending 行可能已在后文结案）" % path]
    # Current open items come from the product's handoff.md, which is kept up to date,
    # rather than from the append-only task digest.
    prod = next((p for p in read_products() if p["id"].lower() == product.lower()), None)
    lines += ["", "## 当前等人处理（摘自 handoff.md，更新于 %s）" % ((prod or {}).get("updated") or "未知")]
    lines += ["- %s" % w for w in (prod or {}).get("waiting", [])] or ["- 无"]
    return "\n".join(lines) + "\n"


def slug(role):
    return {"固件研发与实测": "weband-firmware", "团队运营": "team-ops"}.get(role, re.sub(r"\W+", "-", role))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--date", type=lambda s: dt.datetime.strptime(s, "%Y-%m-%d").date())
    ap.add_argument("--days", type=int, default=2, help="how many days back from --date (default 2)")
    a = ap.parse_args()
    end = a.date or dt.date.today()
    days = [end - dt.timedelta(days=i) for i in range(max(1, a.days))]
    since = dt.datetime.combine(min(days), dt.time()) - dt.timedelta(days=1)
    events = read_events(since)
    runs = read_runs(events)
    activity = read_activity(since)
    for day in days:
        out = STATE / "digests" / day.isoformat()
        out.mkdir(parents=True, exist_ok=True)
        for task in ROLES:
            (out / ("%s.md" % task)).write_text(cron_digest(task, day, events, runs), encoding="utf-8")
        for role, product, path in MANUAL_ROLES:
            (out / ("%s.md" % slug(role))).write_text(manual_digest(role, product, path, day, activity),
                                                      encoding="utf-8")
        print("wrote %s (%d roles)" % (out, len(ROLES) + len(MANUAL_ROLES)))


if __name__ == "__main__":
    main()
