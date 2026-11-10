---
inclusion: manual
---

# 值班任务:安装包下载与启动自检(L1)

在对话中输入 `#task-l1-package-smoke` 触发,并在消息里提供 brief(版本号、下载 URL、sha256、字节数、真实双目录路径等)。

执行约定:
- 工作目录:`companies/open-source-software/products/open-compare/projects/github`
- 原任务面向 macOS(hdiutil、.app)。在其它系统上无法执行的步骤,记为 blocked 并说明原因,不要伪造结果。
- Munk 运行时概念的替代:`skill(...)` 忽略;`digest.md` 当普通文件写;`needsOwner: true` 改为在对话里直接向用户请示。

#[[file:companies/open-source-software/products/open-compare/projects/github/tasks/l1-package-smoke.md]]
