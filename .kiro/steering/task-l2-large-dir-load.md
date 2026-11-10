---
inclusion: manual
---

# 值班任务:大文件夹加载性能测试(L2)

在对话中输入 `#task-l2-large-dir-load` 触发,并在消息里提供 brief。仅在改动触及扫描、哈希、缓存、IPC、树渲染或取消路径时才运行。

执行约定:
- 工作目录:`companies/open-source-software/products/open-compare/projects/github`
- 计时期间独占机器,不叠加其它高负载任务。
- Munk 运行时概念的替代:`skill(...)` 忽略;`digest.md` 当普通文件写;`needsOwner: true` 改为在对话里直接向用户请示。

#[[file:companies/open-source-software/products/open-compare/projects/github/tasks/l2-large-dir-load.md]]
