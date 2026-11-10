---
inclusion: manual
---

# 值班任务:新版本发布后回帖关单

在对话中输入 `#task-issue-closeout` 触发,并在消息里提供 brief(版本号、Issue 编号、回帖正文)。

执行约定:
- 工作目录:`companies/open-source-software/products/open-compare/projects/github`
- 回帖、关单一律走 `node guards/gh.mjs`(身份 `munk-agent`),回帖后复核作者。
- 回帖和关单是对外可见操作,执行前向用户确认 brief 点名的 Issue 列表。
- Munk 运行时概念的替代:`skill(...)` 忽略;`digest.md` 当普通文件写;`needsOwner: true` 改为在对话里直接向用户请示。

#[[file:companies/open-source-software/products/open-compare/projects/github/tasks/issue-closeout.md]]
