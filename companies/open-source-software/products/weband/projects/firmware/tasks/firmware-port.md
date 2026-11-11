---
title: 固件功能移植
period: day
---
按本场 brief 指定的**一个**里程碑（M1–M5，定义见产品 `AGENTS.md`）移植功能。brief 必须给出：里程碑编号、目标板名、要实现的具体行为。缺任何一项就停下来问。

资料入口（只读，`/home/whole/data/reawork/refdevice` 下）：
- BLE 协议、鉴权、配对、OTA 窗口：`refdevice_固件反汇编分析.md` 第 4 节
- 板级与外设、引脚假设清单：`.agents/tasks/refboard-v2/design.md`（**V2 设计**；Weband 对标 V1，PDM / JD7601 / LGS4056 部分不适用，外设以产品 `AGENTS.md` 第一节的 V1 表为准）
- V1 外设证据：`/home/whole/data/reawork/refdevice-v1/v1_strings.txt`（V1 固件字符串）、`fw/firmware-manifest.json`、原理图截图 `/home/whole/share/mic_imu.webp`。上面的逆向分析基于 V2 固件，用到 V1 时先用 V1 字符串复核。
- 构建与烧录、分区表：`analysis/固件构建与烧录参考.md`
- 符号恢复覆盖范围：`analysis/sigmatch/COVERAGE.md`

流程：
1. 开工先建 `digest.md` 骨架，列出本场范围、依据的资料章节、用到的假设。
2. 在独立 `git worktree` 里开发，不直接动主分支。
3. 协议解析、会话状态机、超时窗口这类纯逻辑，先写成能在 PC 上跑的单测并通过，再上板。
4. 上板验证走 `firmware-build-flash` 的流程，拿到串口日志；M2 起还要有 BLE 联调记录（`pair → auth → ok` 的往返）。
5. 凡是依据"推断"得到的常量、字段名、状态串，代码里标 `TODO(weband)`，并在 digest 登记成清单，写明来源章节。
6. digest 收口：完成项、未完成项、blocked 项（缺板 / 缺外设 / 缺资料）、证据路径。

硬约束：
- 净室：不复制 `ghidra_out` 里的反编译代码，不把原厂二进制、APK 放进产品仓库；按行为和 SiFli-SDK 公开 API 重写。
- 只做 brief 指定的那一个里程碑，不顺手扩范围。
- 外设缺失就记 blocked，不用模拟结果代替真机结果。
- 同一个失败最多重试 2 次，之后写出根因并停手。
