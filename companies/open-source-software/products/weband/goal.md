# Weband 当前目标

- 产品：Weband（`incubating`），对标 refdevice 的 SF32LB52 硬件产品，本阶段只做固件。
- 代码仓库：`/home/whole/data/reawork/weband`（本地 git，尚无远端，`codebaseId` 待建公开仓库后补）。
- 开发板：SF32LB52-DevKit-Nano-R16N16，板级 `sf32lb52-weband`。

## 当前目标：P0（只靠 DevKit-Nano 即可验收）

| 里程碑 | 内容 | 结案条件 | 状态 |
|---|---|---|---|
| M0 | 构建烧录基线 | 编译 → 烧录 → 回读一致 → 串口出现 `Hello world!` 且 `msh />` 可交互 | 已完成（2026-11-09） |
| M1 | 板级工程与外设清点 | `sf32lb52-weband` 编译通过并上板启动；`docs/hardware-inventory.md` 写清实有与缺失外设；分区核对 | 已完成（2026-11-10） |
| M2 | BLE 控制协议 | 主机单测通过；上板后经 BLE 联调走通 `pair → auth → ok` | 已完成（2026-11-11，分支 `m2-ble-protocol`，未合入 main） |

## 之后（P1，需要外设到位）
硬件对标 refdevice **V1 圆屏**（2026-11-10 决定），外设以 V1 为准，详见 `AGENTS.md` 第一节。

- M3 音频链：模拟 MEMS 麦 → 片内 audcodec ADC。**硬件链路已实测通过（2026-11-10）**：3037 模拟麦接 `VCC`→J1-5（MIC_BIAS）、`OUT`→J1-4（MIC_ADC，板上已有 2.2 µF 隔直）、`GND`→J1-1。用 SDK `audprc` 例程录音，出声时比安静时高 10–28 dB（−51 → −23 dBFS）。导出 WAV 试听正常（音调、语速无异常，2026-11-11 用户确认）。MIC_BIAS 电压本身没实测（没有万用表），但麦能正常拾音。剩下的是固件：VAD + Opus 编码录音。
- M4 显示与电源：缺 JDI387A 圆形 LCD（1.2 寸 240×240，JDI 并行）+ 转接；Nano 上 14 根 JDI 信号都已引出。**充电在 Nano 上做不了**（SF32LB52JUD6 不带充电），要验充电需另购锂电版芯片的板子（如 SF32LB52-DevKit-LCD）+ 锂电池；不再买 LGS4056。
- IMU（LSM6DS3TR-C）：V1 原理图有，但 V1 固件反汇编确认不访问（2026-11-10），不对标、不排期。
- M5 OTA / DFU。

里程碑定义与红线以本目录 `AGENTS.md` 为准；本文件只记录当前要推进到哪。
