# Weband 当前目标

- 产品：Weband（`incubating`），对标 refdevice 的 SF32LB52 硬件产品，本阶段只做固件。
- 代码仓库：`/home/whole/data/reawork/weband`（本地 git，尚无远端，`codebaseId` 待建公开仓库后补）。
- 开发板：SF32LB52-DevKit-Nano-R16N16，板级 `sf32lb52-weband`。

## 当前目标：P0（只靠 DevKit-Nano 即可验收）

| 里程碑 | 内容 | 结案条件 | 状态 |
|---|---|---|---|
| M0 | 构建烧录基线 | 编译 → 烧录 → 回读一致 → 串口出现 `Hello world!` 且 `msh />` 可交互 | 已完成（2026-11-09） |
| M1 | 板级工程与外设清点 | `sf32lb52-weband` 编译通过并上板启动；`docs/hardware-inventory.md` 写清实有与缺失外设；分区核对 | 已完成（2026-11-10） |
| M2 | BLE 控制协议 | 主机单测通过；上板后经 BLE 联调走通 `pair → auth → ok` | 未开始 |

## 之后（P1，需要外设到位）
- M3 音频链：缺 PDM 麦克风。
- M4 显示与电源：缺 JD7601 墨水屏 + FPC 转接、LGS4056 充电板 + 电池。
- M5 OTA / DFU。

里程碑定义与红线以本目录 `AGENTS.md` 为准；本文件只记录当前要推进到哪。
