---
inclusion: always
---

# Open Company(open-company/v0)在 Kiro 中的映射

本仓库按 Open Company 标准组织多 Agent 团队。源文件仍是唯一事实来源,`.kiro/steering/` 只做引用和运行适配,修改规则请改源文件。

| Open Company 概念 | Kiro 对应 |
|---|---|
| `Companyfile.yaml` + 公司 `AGENTS.md` | `company-standards.md`(always) |
| `Productfile.yaml` + 产品 `AGENTS.md` | `open-compare-product.md`(fileMatch 产品目录) |
| `tasks/*.md` 值班任务 | `task-*.md`(manual,用 `#task-<id>` 调用) |
| `trigger.schedule` 定时 | 系统 cron 调用 `scripts/cron/run-task.sh <task-id>`(见 `scripts/cron/crontab.example`,目前只排 `daily-patrol`),也可在 IDE 里手动触发 |
| `trigger.guard` 预检脚本 | cron 模式由 `run-task.sh` 先跑 guard,exit=0 才启动 Agent;手动模式在任务开头自己跑 |
| `brief` | 用户在触发任务的那条消息里提供 |
| `digest.md` | 任务工作目录下的普通文件 |
| `needsOwner: true` | 停下来在对话里向用户请示 |
| `skill(...)`、`munk_task_publish`、`computer` 场 | 无对应;按各任务文件里的替代说明处理 |

可用任务:
- 团队级:`#task-daily-patrol`、`#task-computer`
- OpenCompare(**仅作参考模板,不做实际运营**,不挂 cron,晚间盘点也不对账;任务文件保留作写法示例):`#task-github-issue-pr-actions`、`#task-release-batch`、`#task-l1-package-smoke`、`#task-l2-large-dir-load`、`#task-l3-cdp-ui`、`#task-l3-computer-native`、`#task-issue-closeout`
- Weband(固件,需真实开发板,手动触发):`#task-firmware-build-flash`、`#task-firmware-port`

角色 digest:每个角色每天一份,`~/.local/state/open-company/digests/<日期>/<角色>.md`,由 cron 每小时用 `scripts/report/build_digests.py` 从日志、活动日志和各场 digest 汇总生成;即使当天没有唤醒 Agent 也会生成。图形化报告 `~/.local/state/open-company/report/index.html` 同时更新。

活动日志:IDE 会话里替角色干活时,按 `activity-log.md`(always)用 `scripts/report/log_activity.py` 记一句话进展,写入 `~/.local/state/open-company/activity/<日期>.jsonl`;Stop hook 另记会话心跳。报告的角色概览、今日活动和时间线都读它。

进度文件(每个产品目录下各一份,晚间盘点读取):
- `goal.md`:当前目标、里程碑、结案条件。目标变化时更新。
- `handoff.md`:现状、等待项、下一步、证据索引,顶部写「最近更新」日期。每次任务收工或里程碑状态变化时更新。

人工操作说明书:`docs/operator-manual.md`(凭据、cron、报告、Weband 构建烧录串口、还原出厂、常见故障)。改了排班、凭据、构建或烧录流程时,同步更新这份说明书。

通用规则:
- 推 tag、发 Release、GitHub 回帖/关单等对外操作,执行前先向用户确认。
- 无法在当前环境完成的步骤记为 blocked 并写明原因,不伪造结果。
