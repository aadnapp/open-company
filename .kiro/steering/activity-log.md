---
inclusion: always
---

# IDE 会话活动记录

进度报告（`~/.local/state/open-company/report/index.html`）的角色概览、今日活动和时间线只看写进活动日志的内容；对话原文由 Stop hook 自动摘取展示在「今日对话记录」小节，不用额外操作。所以在 IDE 会话里替某个角色干活时，按下面的规则记一句话进展。

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

- 密钥、token、口令、对话原文、用户个人信息。这条一句话摘要只写结果和判定；对话原文已经由 Stop hook 自动记录，不用也不要在这里重复。
- 没有发生的事。记录是事实，不是计划；计划写进 `handoff.md` 的「下一步」。

## 和其它记录的关系

- 活动日志是给报告看的一句话摘要，不代替产品自己的证据：Weband 的逐步实测仍写 `evidence/digest.md`，现状和等待项仍写 `handoff.md`。
- 每轮回复结束，Stop hook 会自动记一条「会话心跳」（只有时间和工作区，不含内容），并调用 `scripts/report/capture_chat.py` 把这轮新增的用户发言和 Agent 实际回复文字摘取进 `~/.local/state/open-company/chat/<日期>.jsonl`（经过粗略脱敏，不含工具调用和推理过程）。报告据此在「今日活动」小节提示「有会话活动但没有记录进展」，在「今日对话记录」小节展示对话原文，所以漏记一句话进展会被看出来，对话内容则始终能看到。

## workflow 运行时（2026-11-19 用户指出）

workflow 的每一步是单独的会话，**不触发 Stop hook**：不记心跳，不即时摘取对话，也不重建报告。2026-11-19 按小时录音那次 workflow，设计到编码约 40 分钟，活动日志里一条记录都没有，收尾后 `goal.md` 也停在「上板验证待用户确认」。所以：

- **每一步自己记活动日志**：步骤开始记 `start`，出结论记 `progress` 或 `done`，停下来请示用户前记 `waiting`。角色按上面的规则选（Weband 的工作记 `固件研发与实测`）。一句话里写 workflow 的步骤名，例如 `设计: design.md 已写完，3 个待定点已请示`。
- **步骤结束时重建报告**：
  ```bash
  cd /home/whole/data/src/open-company/scripts/report && python3 capture_chat.py && python3 build_digests.py >/dev/null && python3 build_report.py >/dev/null
  ```
  cron 每 10 分钟也会跑同样的命令兜底（`scripts/cron/crontab.example`）。
- **收尾那一步更新产品状态**：一项工作合入或状态变化时，同步改产品的 `goal.md`（对应遗留或里程碑条目）和 `handoff.md`（顶部「最近更新」与对应条目），写清提交号、证据路径和没测的部分。
- **收尾那一步归档 workflow 产物**（2026-11-23 用户定）：workflow 写在产品仓库 `.agents/tasks/<任务>/` 下的设计、计划、评审、报告，在任务完成后搬进产品的 `evidence/NNNN_task_<任务>/`（编号取当前最大加 1，搬之前先 `ls evidence` 确认没有被别的会话占用）。目录里加一份 README，写明内容和对应提交；参考设备名按 `refdevice-files/scrub.py` 的规则替换，令牌写成 `****`；文中旧的 `.agents/tasks/...` 路径改成新目录。和已有证据重复的文件（例如同一份构建日志）不搬。搬完删掉空的 `.agents/tasks/<任务>/`，`goal.md` / `handoff.md` 里的引用同步改成新路径。
- **发起 workflow 的会话（编排者）负责兜底**：写 workflow brief 时把以上四条写进去；收到 workflow 完成的通知后，核对 `goal.md` / `handoff.md` 是否已经更新到最新结论，没有就补上，再重建一次报告。之后在会话里继续做的实测和修复，同样要回写这两个文件。

## 更新 handoff 必须回看「待办清单」（2026-11-20 用户要求）

进度报告的「产品待办」只读 `handoff.md` 的「## 待办清单」一节，不读「现状」「下一步」。改 `handoff.md` 的任何一处（包括只往「现状」加一条）时，同一次编辑里必须：

1. 逐条回看「待办清单」：已做完的连同编号移到「## 已完成功能」对应的 `### 功能` 下（没有就新建，新完成的功能写在最上面），结论也写进「现状」，状态变了的改状态（进行中 / 等用户 / 待定 / 排期），新出现的待办补进去。
2. 同步「等待项」：用户已答复或已做完的条目删掉或改成已定，不留过期的"下一步做 X"。
3. 把顶部「最近更新」日期改成今天，并写一句现状。
4. 待办条目写成 `- 待办<编号> [高|中|低][状态] 标题：说明`。编号一经分配不改、不复用，新条目取当前最大编号加 1（注释里写着已用到几号），删掉的编号空着。用户说「待办N」时，指的就是这个编号的条目。

收尾自查：改完后用 `grep -n '^- 待办[0-9]' handoff.md` 看待办清单是否和刚写进「现状」的结论一致。workflow 的收尾步骤和编排者兜底同样适用。
