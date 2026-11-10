---
inclusion: manual
---

# 值班任务:固件功能移植(Weband)

在对话中输入 `#task-firmware-port` 触发,并在消息里提供 brief(里程碑编号、目标板名、要实现的具体行为)。

执行约定:
- 工作目录:`/home/whole/data/reawork/weband`(SDK 在其下的 `sifli-sdk/`,证据放 `evidence/`)。
- 参考资料目录 `/home/whole/data/reawork/refdevice` 只读,不要在里面改文件。
- 这条任务上板验证需要真实开发板,不挂 cron。
- Munk 运行时概念的替代:`skill(...)` 忽略;`digest.md` 当普通文件写;`needsOwner: true` 改为在对话里直接向用户请示。

#[[file:companies/open-source-software/products/weband/projects/firmware/tasks/firmware-port.md]]
