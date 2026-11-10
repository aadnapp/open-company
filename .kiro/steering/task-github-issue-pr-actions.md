---
inclusion: manual
---

# 值班任务:GitHub Issue 与构建报错盯盘

在对话中输入 `#task-github-issue-pr-actions` 触发。原定每 5 分钟运行,Kiro 无定时调度,改为手动触发。

执行约定:
- 工作目录:`companies/open-source-software/products/open-compare/projects/github`
- 预检:先运行 `node guards/github-sentinel.mjs`。退出码 0 = 有新事件,继续处理;1 = 无新事件,直接收工;2 = 脚本出错,报告给用户。
- 对外写操作一律走 `node guards/gh.mjs`,不要用个人 `gh` 登录。
- Munk 运行时概念的替代:`skill(...)` 忽略;`digest.md` 当普通文件写;`needsOwner: true` 改为在对话里直接向用户请示。

#[[file:companies/open-source-software/products/open-compare/projects/github/tasks/github-issue-pr-actions.md]]
