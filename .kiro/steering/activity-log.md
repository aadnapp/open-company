---
inclusion: always
---

# IDE 会话活动记录

进度报告（`~/.local/state/open-company/report/index.html`）看不到 IDE 对话本身，只看得到写进活动日志的内容。所以在 IDE 会话里替某个角色干活时，按下面的规则记录。

## 怎么记

```bash
python3 /home/whole/data/src/open-company/scripts/report/log_activity.py \
  --role <角色> --kind <类型> [--ref <证据路径>] "<一句话>"
```

- 角色（只接受这几个，写错会报错）：
  - `固件研发与实测`：Weband 固件、板子、外设、实测（`/home/whole/data/reawork/weband` 下的工作）
  - `团队运营`：本仓库自身的规则、任务、cron、报告脚本、操作手册
  - `晚间复盘`：在 IDE 里手动跑 `#task-daily-patrol` 时
- 类型：`start` 开始一项工作 / `progress` 一个子步骤有了结果 / `done` 这项工作完成 / `blocked` 卡住（缺板、缺外设、缺资料、报错查不出）/ `waiting` 等用户确认或操作
- 一句话：写结果和判定，不写过程流水账。例：`A/B 录音通过，出声比安静高 10-28 dB`、`等用户确认烧录 audprc 例程`。
- `--ref`：有证据文件时写上路径（日志、digest 行所在文件）。

## 什么时候记

- 开始一项用户交代的工作时记一条 `start`。
- 每完成一个能独立说清结论的子步骤记一条 `progress`。大约每次往产品 `evidence/digest.md` 追加判定，或改了 `goal.md` / `handoff.md` 时。
- 停下来问用户、等用户操作之前记 `waiting`；遇到做不下去的情况记 `blocked`。
- 这项工作收尾时记 `done`。
- 纯问答、没有动手做事的回复不用记。

## 不要写进去的

- 密钥、token、口令、对话原文、用户个人信息。
- 没有发生的事。记录是事实，不是计划；计划写进 `handoff.md` 的「下一步」。

## 和其它记录的关系

- 活动日志是给报告看的一句话摘要，不代替产品自己的证据：Weband 的逐步实测仍写 `evidence/digest.md`，现状和等待项仍写 `handoff.md`。
- 每轮回复结束，Stop hook 会自动记一条「会话心跳」（只有时间和工作区，不含内容）。报告据此提示「有会话活动但没有记录进展」，所以漏记会被看出来。
