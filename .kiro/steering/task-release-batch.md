---
inclusion: manual
---

# 值班任务:每日 07:00 定时发版

在对话中输入 `#task-release-batch` 触发。原定每天 07:00 运行,Kiro 无定时调度,改为手动触发。

执行约定:
- 工作目录:`companies/open-source-software/products/open-compare/projects/github`;代码仓为 OpenCompare 的 main 分支。
- 推 tag、创建 Release 属高风险操作,执行前必须向用户确认。
- Munk 运行时概念的替代:`skill(...)` 忽略;`munk_task_publish` 无对应工具,改为向用户给出需要执行的 git 命令并请其确认;`digest.md` 当普通文件写;`needsOwner: true` 改为在对话里直接向用户请示。

#[[file:companies/open-source-software/products/open-compare/projects/github/tasks/release-batch.md]]
