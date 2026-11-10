---
inclusion: manual
---

# 值班任务:固件构建与烧录基线(Weband)

在对话中输入 `#task-firmware-build-flash` 触发,并在消息里提供 brief(目标板名、串口设备、应用目录、SDK 路径)。

执行约定:
- 工作目录:`/home/whole/data/reawork/weband`(SDK 在其下的 `sifli-sdk/`,证据放 `evidence/`)。
- 这条任务需要真实开发板,不挂 cron。烧录会改写设备 Flash,执行前必须向用户确认端口与板型。
- 找不到串口设备就记为 blocked,不要伪造烧录或串口结果。
- Munk 运行时概念的替代:`skill(...)` 忽略;`digest.md` 当普通文件写;`needsOwner: true` 改为在对话里直接向用户请示。

#[[file:companies/open-source-software/products/weband/projects/firmware/tasks/firmware-build-flash.md]]
